"""
Re-score Experiment 0 JSONL outputs with the revised disagreement metric.

This script is intentionally lightweight: it does not rerun any model. It reads
saved agent answers/confidences, recomputes D(q), applies either a fixed or
percentile hard-case threshold, and writes a compact summary JSON.

Example:
  python experiments/experiment_0/rescore_with_new_disagreement.py \
    --input experiments/experiment_0/results/exp0_heterogeneous_mistral_d_n300.jsonl \
    --output experiments/experiment_0/results/rescore_mistral_d_n300_revised.json \
    --adaptive_percentile 80
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[2]
SCORER_DIR = ROOT / "disagreement_scorer"
sys.path.insert(0, str(SCORER_DIR))

from task2_disagreement_scorer import AgentOutput, DisagreementScorer  # noqa: E402


def normalize_answer(answer: Any) -> str:
    text = str(answer or "").strip().upper()
    return text[:1] if text and text[:1].isalpha() else text


def spearman(x: List[float], y: List[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return float("nan")

    def ranks(values: List[float]) -> List[float]:
        order = sorted(range(len(values)), key=lambda idx: values[idx])
        out = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            rank = (i + j + 2) / 2.0
            for k in range(i, j + 1):
                out[order[k]] = rank
            i = j + 1
        return out

    rx = ranks(x)
    ry = ranks(y)
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den_x = math.sqrt(sum((a - mx) ** 2 for a in rx))
    den_y = math.sqrt(sum((b - my) ** 2 for b in ry))
    if den_x == 0 or den_y == 0:
        return float("nan")
    return num / (den_x * den_y)


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no} is not valid JSONL") from exc


def first_present(row: Dict[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def extract_outputs(row: Dict[str, Any]) -> Optional[List[AgentOutput]]:
    raw_outputs = row.get("agent_outputs") or row.get("agents") or row.get("outputs")
    if isinstance(raw_outputs, list):
        outputs = []
        for idx, item in enumerate(raw_outputs):
            if not isinstance(item, dict):
                continue
            outputs.append(
                AgentOutput(
                    agent_name=str(item.get("agent_name") or item.get("name") or f"A{idx}"),
                    answer=str(item.get("answer") or item.get("prediction") or ""),
                    confidence=float(item.get("confidence") or item.get("conf") or 0.0),
                    probs=item.get("probs") or item.get("probabilities"),
                )
            )
        return outputs if len(outputs) == 3 else None

    specs = [
        ("R", ["agent_r_answer", "r_answer", "R_answer", "answer_r"], ["agent_r_confidence", "r_confidence", "R_confidence", "confidence_r"]),
        ("D", ["agent_d_answer", "d_answer", "D_answer", "answer_d"], ["agent_d_confidence", "d_confidence", "D_confidence", "confidence_d"]),
        ("C", ["agent_c_answer", "c_answer", "C_answer", "answer_c"], ["agent_c_confidence", "c_confidence", "C_confidence", "confidence_c"]),
    ]
    outputs = []
    for name, answer_keys, conf_keys in specs:
        answer = first_present(row, answer_keys)
        conf = first_present(row, conf_keys)
        if answer is None:
            return None
        outputs.append(AgentOutput(name, str(answer), float(conf or 0.0)))
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--adaptive_percentile", type=float, default=80.0)
    args = parser.parse_args()

    rows = list(iter_jsonl(args.input))
    scorer = DisagreementScorer(
        threshold=args.threshold,
        adaptive_percentile=args.adaptive_percentile,
    )

    questions = []
    outputs_per_question = []
    kept_rows = []
    dropped = 0
    for idx, row in enumerate(rows):
        outputs = extract_outputs(row)
        if outputs is None:
            dropped += 1
            continue
        question = str(first_present(row, ["question", "prompt", "text"]) or "")
        correct = first_present(row, ["answer", "correct_answer", "gold", "label"])
        questions.append(
            {
                "question_id": str(first_present(row, ["question_id", "id"]) or idx),
                "question": question,
                "answer": correct,
            }
        )
        outputs_per_question.append(outputs)
        kept_rows.append(row)

    results = scorer.score_batch(questions, outputs_per_question)
    difficulties = [
        first_present(row, ["difficulty", "difficulty_score", "task1_difficulty", "score"])
        for row in kept_rows
    ]
    paired = [
        (result.d_score, float(difficulty))
        for result, difficulty in zip(results, difficulties)
        if difficulty not in (None, "")
    ]

    summary = {
        "input": str(args.input),
        "n_rows": len(rows),
        "n_scored": len(results),
        "n_dropped": dropped,
        "metric": "entropy + pairwise JS + confidence variance + optional correctness diversity",
        "adaptive_percentile": args.adaptive_percentile,
        "fixed_threshold": args.threshold,
        "mean_D_q": sum(r.d_score for r in results) / len(results) if results else None,
        "hard_case_rate": sum(1 for r in results if r.is_hard_case) / len(results) if results else None,
        "spearman_rho_Dq_vs_difficulty": spearman(
            [score for score, _ in paired],
            [difficulty for _, difficulty in paired],
        ) if paired else None,
        "component_means": {
            "answer_entropy": sum(r.d_answer for r in results) / len(results) if results else None,
            "pairwise_js": sum(r.d_distribution for r in results) / len(results) if results else None,
            "confidence_variance": sum(r.d_confidence for r in results) / len(results) if results else None,
            "correctness_diversity": sum(r.d_correctness for r in results) / len(results) if results else None,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
