"""Reusable data-quality checks for the NeurIPS rebuttal audit.

The functions in this module intentionally use only repository-local files.
They support the executable notebook and write bounded CSV/JSON artifacts that
can be traced back to the saved experiment outputs.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "experiments" / "experiment_0" / "results"
RESCORED_DIR = (
    REPO_ROOT
    / "experiments"
    / "experiment_0"
    / "local_kaggle1_outputs"
    / "rescored_jsonl"
)
DATA_DIR = REPO_ROOT / "data_preparation"
ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"

AGENT_NAMES = ("R", "D", "C")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                rows.append(json.loads(text))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
    return rows


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def safe_spearman(left: Iterable[Any], right: Iterable[Any]) -> tuple[float | None, float | None, int]:
    pairs = []
    for left_value, right_value in zip(left, right):
        x = finite_float(left_value)
        y = finite_float(right_value)
        if x is not None and y is not None:
            pairs.append((x, y))
    if len(pairs) < 3:
        return None, None, len(pairs)
    x_values, y_values = zip(*pairs)
    if len(set(x_values)) < 2 or len(set(y_values)) < 2:
        return None, None, len(pairs)
    result = spearmanr(x_values, y_values)
    rho = None if math.isnan(float(result.statistic)) else float(result.statistic)
    p_value = None if math.isnan(float(result.pvalue)) else float(result.pvalue)
    return rho, p_value, len(pairs)


def row_has_agents(row: dict[str, Any]) -> bool:
    per_agent = row.get("per_agent")
    return isinstance(per_agent, dict) and all(name in per_agent for name in AGENT_NAMES)


def row_has_probabilities(row: dict[str, Any]) -> bool:
    per_agent = row.get("per_agent")
    if not isinstance(per_agent, dict):
        return False
    for name in AGENT_NAMES:
        agent_row = per_agent.get(name)
        if not isinstance(agent_row, dict):
            return False
        probabilities = agent_row.get("all_probs")
        if not isinstance(probabilities, dict) or len(probabilities) < 2:
            return False
        values = [finite_float(value) for value in probabilities.values()]
        if any(value is None or value < 0 for value in values):
            return False
        if not math.isclose(sum(values), 1.0, rel_tol=0.02, abs_tol=0.02):
            return False
    return True


def profile_result_file(path: Path) -> dict[str, Any]:
    rows = read_jsonl(path)
    question_ids = [str(row.get("question_id", "")) for row in rows]
    difficulty = [
        row.get("difficulty_for_corr", row.get("difficulty_score", row.get("final_difficulty")))
        for row in rows
    ]
    valid_difficulty = [value for value in (finite_float(item) for item in difficulty) if value is not None]
    raw_scores = [row.get("D_q", row.get("d_score")) for row in rows]
    revised_scores = [row.get("D_revised") for row in rows]
    raw_rho, raw_p, raw_n = safe_spearman(raw_scores, difficulty)
    revised_rho, revised_p, revised_n = safe_spearman(revised_scores, difficulty)
    categories = {
        str(row.get("category", "")).strip()
        for row in rows
        if str(row.get("category", "")).strip()
    }
    return {
        "file": str(path.relative_to(REPO_ROOT)),
        "rows": len(rows),
        "unique_question_ids": len(set(question_ids)),
        "duplicate_question_rows": len(rows) - len(set(question_ids)),
        "difficulty_complete_rows": len(valid_difficulty),
        "difficulty_complete_rate": len(valid_difficulty) / len(rows) if rows else 0.0,
        "difficulty_unique_values": len(set(valid_difficulty)),
        "difficulty_min": min(valid_difficulty) if valid_difficulty else None,
        "difficulty_max": max(valid_difficulty) if valid_difficulty else None,
        "difficulty_std": float(np.std(valid_difficulty)) if valid_difficulty else None,
        "category_count": len(categories),
        "gold_answer_complete_rows": sum(
            bool(str(row.get("correct_answer", "")).strip()) for row in rows
        ),
        "three_agent_complete_rows": sum(row_has_agents(row) for row in rows),
        "option_probability_complete_rows": sum(row_has_probabilities(row) for row in rows),
        "raw_score_complete_rows": sum(finite_float(value) is not None for value in raw_scores),
        "revised_score_complete_rows": sum(
            finite_float(value) is not None for value in revised_scores
        ),
        "raw_spearman_rho": raw_rho,
        "raw_spearman_p": raw_p,
        "raw_spearman_n": raw_n,
        "revised_spearman_rho": revised_rho,
        "revised_spearman_p": revised_p,
        "revised_spearman_n": revised_n,
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_groups(paths: Iterable[Path]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        grouped[sha256(path)].append(str(path.relative_to(REPO_ROOT)))
    records = []
    for digest, files in sorted(grouped.items(), key=lambda item: item[1]):
        records.append(
            {
                "sha256": digest,
                "file_count": len(files),
                "files": " | ".join(files),
                "exact_duplicate_group": len(files) > 1,
            }
        )
    return records


def load_json_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list of records in {path}")
    return [dict(row) for row in payload]


def profile_dataset(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        records = load_json_records(path)
        frame = pd.DataFrame(records)
    else:
        frame = pd.read_csv(path)
    difficulty_column = next(
        (name for name in ("difficulty_score", "final_difficulty") if name in frame.columns),
        None,
    )
    if difficulty_column is None:
        difficulty = pd.Series(dtype=float)
    else:
        difficulty = pd.to_numeric(frame[difficulty_column], errors="coerce")
    question_ids = frame.get("question_id", pd.Series(range(len(frame)))).astype(str)
    return {
        "file": str(path.relative_to(REPO_ROOT)),
        "rows": int(len(frame)),
        "unique_question_ids": int(question_ids.nunique()),
        "duplicate_question_rows": int(len(frame) - question_ids.nunique()),
        "difficulty_column": difficulty_column,
        "difficulty_complete_rows": int(difficulty.notna().sum()),
        "difficulty_unique_values": int(difficulty.nunique(dropna=True)),
        "difficulty_min": float(difficulty.min()) if difficulty.notna().any() else None,
        "difficulty_max": float(difficulty.max()) if difficulty.notna().any() else None,
        "difficulty_std": float(difficulty.std(ddof=0)) if difficulty.notna().any() else None,
    }


def agent_c_overlap(
    max_rows: int = 2500,
    validation_fraction: float = 0.15,
    seed: int = 42,
    evaluation_rows: int = 300,
) -> dict[str, Any]:
    source_path = DATA_DIR / "mmlu_pro_hard_subset.json"
    records = load_json_records(source_path)
    original_ids = [str(row.get("question_id", row.get("id", ""))) for row in records]
    shuffled = list(original_ids)
    random.Random(seed).shuffle(shuffled)
    selected = shuffled[:max_rows]
    n_validation = max(32, int(round(len(selected) * validation_fraction)))
    n_validation = min(n_validation, max(1, len(selected) // 3))
    validation_ids = set(selected[:n_validation])
    training_ids = set(selected[n_validation:])
    excluded_ids = set(original_ids) - set(selected)
    evaluation_ids = set(original_ids[:evaluation_rows])
    return {
        "source_rows": len(original_ids),
        "agent_c_selected_rows": len(selected),
        "agent_c_training_rows": len(training_ids),
        "agent_c_validation_rows": len(validation_ids),
        "agent_c_excluded_rows": len(excluded_ids),
        "evaluation_rows": len(evaluation_ids),
        "evaluation_in_agent_c_training": len(evaluation_ids & training_ids),
        "evaluation_in_agent_c_validation": len(evaluation_ids & validation_ids),
        "evaluation_excluded_from_agent_c": len(evaluation_ids & excluded_ids),
        "evaluation_overlap_rate_any_agent_c_split": (
            len(evaluation_ids & (training_ids | validation_ids)) / len(evaluation_ids)
            if evaluation_ids
            else None
        ),
        "assumptions": {
            "agent_c_profile": "deadline",
            "max_rows": max_rows,
            "validation_fraction": validation_fraction,
            "seed": seed,
            "evaluation_selection": f"first {evaluation_rows} rows in hard-subset order",
        },
    }


def artifact_inventory() -> dict[str, Any]:
    tracked_files = [path for path in REPO_ROOT.rglob("*") if path.is_file() and ".git" not in path.parts]
    suffix_counts: dict[str, int] = defaultdict(int)
    for path in tracked_files:
        suffix_counts[path.suffix.lower() or "<none>"] += 1
    coevolution_outputs = [
        path
        for path in tracked_files
        if "co_evolution" in path.parts
        and path.suffix.lower() in {".json", ".jsonl", ".csv"}
        and "test_" not in path.name
    ]
    checkpoint_files = [
        path
        for path in tracked_files
        if path.suffix.lower() in {".safetensors", ".bin", ".pt", ".pth", ".zip"}
    ]
    return {
        "repository_file_count": len(tracked_files),
        "suffix_counts": dict(sorted(suffix_counts.items())),
        "static_result_jsonl_count": len(list(RESULTS_DIR.glob("*.jsonl"))),
        "rescored_result_jsonl_count": len(list(RESCORED_DIR.glob("*.jsonl"))),
        "coevolution_result_artifact_count": len(coevolution_outputs),
        "coevolution_result_artifacts": [
            str(path.relative_to(REPO_ROOT)) for path in coevolution_outputs
        ],
        "checkpoint_or_adapter_archive_count": len(checkpoint_files),
        "checkpoint_or_adapter_archives": [
            str(path.relative_to(REPO_ROOT)) for path in checkpoint_files
        ],
    }


def run_audit(write_artifacts: bool = True) -> dict[str, Any]:
    result_paths = sorted(RESULTS_DIR.glob("*.jsonl")) + sorted(RESCORED_DIR.glob("*.jsonl"))
    result_profiles = [profile_result_file(path) for path in result_paths]
    dataset_paths = [
        DATA_DIR / "mmlu_pro_hard_subset.json",
        DATA_DIR / "gpqa_diamond.json",
    ]
    dataset_profiles = [profile_dataset(path) for path in dataset_paths if path.exists()]
    hashes = hash_groups(result_paths)
    overlap = agent_c_overlap()
    inventory = artifact_inventory()
    summary = {
        "result_profiles": result_profiles,
        "dataset_profiles": dataset_profiles,
        "hash_groups": hashes,
        "agent_c_overlap": overlap,
        "artifact_inventory": inventory,
    }

    if write_artifacts:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(result_profiles).to_csv(
            ARTIFACT_DIR / "static_output_profile.csv", index=False
        )
        pd.DataFrame(dataset_profiles).to_csv(
            ARTIFACT_DIR / "dataset_profile.csv", index=False
        )
        pd.DataFrame(hashes).to_csv(
            ARTIFACT_DIR / "result_file_hash_groups.csv", index=False
        )
        (ARTIFACT_DIR / "agent_c_overlap.json").write_text(
            json.dumps(overlap, indent=2), encoding="utf-8"
        )
        (ARTIFACT_DIR / "artifact_inventory.json").write_text(
            json.dumps(inventory, indent=2), encoding="utf-8"
        )
        (ARTIFACT_DIR / "audit_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
    return summary


if __name__ == "__main__":
    audit = run_audit(write_artifacts=True)
    overlap = audit["agent_c_overlap"]
    inventory = audit["artifact_inventory"]
    print(
        json.dumps(
            {
                "profiled_result_files": len(audit["result_profiles"]),
                "exact_duplicate_groups": sum(
                    row["exact_duplicate_group"] for row in audit["hash_groups"]
                ),
                "evaluation_in_agent_c_training": overlap[
                    "evaluation_in_agent_c_training"
                ],
                "evaluation_in_agent_c_validation": overlap[
                    "evaluation_in_agent_c_validation"
                ],
                "coevolution_result_artifact_count": inventory[
                    "coevolution_result_artifact_count"
                ],
                "checkpoint_or_adapter_archive_count": inventory[
                    "checkpoint_or_adapter_archive_count"
                ],
            },
            indent=2,
        )
    )
