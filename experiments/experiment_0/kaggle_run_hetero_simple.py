"""
Kaggle runner for Experiment 0: heterogeneous Agent-R/D/C.

Only edit the PATHS block below.
Then run:
  !python /kaggle/input/YOUR_SCRIPT_DATASET/kaggle_run_hetero_simple.py

For a quick test:
  !python /kaggle/input/YOUR_SCRIPT_DATASET/kaggle_run_hetero_simple.py --limit 20
"""

import argparse
import ast
import json
import math
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import torch
from peft import PeftModel
from scipy.stats import spearmanr
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


# ============================================================
# PATHS: EDIT ONLY THIS BLOCK
# ============================================================

BASE_MODEL = "/kaggle/input/datasets/ebadshabbir/qwen2-5-3b-instruct"
MMLU_CSV = "/kaggle/input/datasets/ebadshabbir/mmlu-pro-hard/mmlu_pro_hard_subset.csv"

AGENT_R_ZIP = "/kaggle/input/PUT-YOUR-AGENT-R-DATASET-NAME-HERE/agent_r_v0_grpo_adapter.zip"
AGENT_D_ZIP = "/kaggle/input/PUT-YOUR-AGENT-D-DATASET-NAME-HERE/results.zip"
AGENT_C_ZIP = "/kaggle/input/PUT-YOUR-AGENT-C-DATASET-NAME-HERE/results.zip"

OUTPUT_DIR = "/kaggle/working"


# ============================================================
# CONSTANTS
# ============================================================

LETTERS = "ABCDEFGHIJ"

SYSTEM_PROMPTS = {
    "R": (
        "You are Agent-R, a careful mathematical and symbolic reasoner. "
        "Solve deliberately and choose the best option."
    ),
    "D": (
        "You are Agent-D, a domain specialist. Use subject-matter knowledge "
        "and choose the best option."
    ),
    "C": (
        "You are Agent-C, a calibrated analyst. Choose the best option while "
        "keeping uncertainty honest."
    ),
}


# ============================================================
# FILE HELPERS
# ============================================================

def check_path(path: str, name: str) -> Path:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"{name} does not exist:\n{path}\n\n"
            "Fix the path in the PATHS block at the top of this script."
        )
    return p


def unzip_to(path: str, dest: Path) -> Path:
    src = check_path(path, "Zip/folder")
    if src.is_dir():
        return src

    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / ".unzipped"
    if not marker.exists():
        print(f"Unzipping {src} -> {dest}")
        with zipfile.ZipFile(src, "r") as zf:
            zf.extractall(dest)
        marker.write_text("ok", encoding="utf-8")
    return dest


def find_adapter_dir(root: Path, preferred_folder: str) -> Path:
    direct = root / preferred_folder
    if (direct / "adapter_config.json").exists():
        return direct

    if (root / "adapter_config.json").exists():
        return root

    matches = list(root.rglob("adapter_config.json"))
    if not matches:
        raise FileNotFoundError(f"No adapter_config.json found under:\n{root}")

    return matches[0].parent


def prepare_adapters() -> Dict[str, Path]:
    r_root = unzip_to(AGENT_R_ZIP, Path("/kaggle/working/unzipped_agent_r"))
    d_root = unzip_to(AGENT_D_ZIP, Path("/kaggle/working/unzipped_agent_d"))
    c_root = unzip_to(AGENT_C_ZIP, Path("/kaggle/working/unzipped_agent_c"))

    return {
        "R": find_adapter_dir(r_root, "agent_r_v0_grpo_adapter"),
        "D": find_adapter_dir(d_root, "agent_d_v0"),
        "C": find_adapter_dir(c_root, "agent_c_v0"),
    }


# ============================================================
# DATA
# ============================================================

def parse_options(value) -> List[str]:
    if isinstance(value, list):
        return [str(x) for x in value]

    text = str(value)
    for parser in (ast.literal_eval, json.loads):
        try:
            parsed = parser(text)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
            if isinstance(parsed, dict):
                return [str(parsed[k]) for k in sorted(parsed)]
        except Exception:
            pass

    return [text]


def load_questions(path: str, limit: Optional[int]) -> List[Dict]:
    check_path(path, "MMLU CSV")
    df = pd.read_csv(path)

    rows = []
    for i, row in df.iterrows():
        options = parse_options(row["options"])
        if len(options) < 2:
            continue

        rows.append({
            "question_id": str(row.get("question_id", i)),
            "question": str(row["question"]),
            "options": options[:len(LETTERS)],
            "answer": str(row["answer"]).strip().upper()[:1],
            "category": str(row.get("category", "")),
            "difficulty_score": float(row["difficulty_score"]),
        })

    return rows[:limit] if limit else rows


def load_temperature(agent_c_dir: Path) -> float:
    temp_path = agent_c_dir / "temperature.json"
    if not temp_path.exists():
        return 1.0

    data = json.loads(temp_path.read_text(encoding="utf-8"))
    for key in ("temperature", "T", "best_temperature"):
        if key in data:
            value = float(data[key])
            return value if value > 0 else 1.0

    return 1.0


# ============================================================
# MODEL INFERENCE
# ============================================================

def format_options(options: List[str]) -> str:
    return "\n".join(f"{LETTERS[i]}. {option}" for i, option in enumerate(options))


def make_prompt(tokenizer, agent: str, question: Dict) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[agent]},
        {
            "role": "user",
            "content": (
                "Answer this multiple-choice question.\n\n"
                f"Question:\n{question['question']}\n\n"
                f"Options:\n{format_options(question['options'])}\n\n"
                "Return only the single best answer letter."
            ),
        },
    ]
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )


def answer_token_ids(tokenizer, n_options: int) -> List[int]:
    ids = []
    for letter in LETTERS[:n_options]:
        tokenized = tokenizer.encode(letter, add_special_tokens=False)
        if not tokenized:
            raise ValueError(f"Could not tokenize answer letter: {letter}")
        ids.append(tokenized[-1])
    return ids


@torch.inference_mode()
def run_agent(model, tokenizer, agent: str, question: Dict, temperature: float) -> Dict:
    prompt = make_prompt(tokenizer, agent, question)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    output = model(**inputs)

    logits = output.logits[0, -1, :]
    ids = answer_token_ids(tokenizer, len(question["options"]))
    choice_logits = torch.stack([logits[token_id] for token_id in ids])
    probs = torch.softmax(choice_logits / max(temperature, 1e-6), dim=0)

    idx = int(torch.argmax(probs).item())
    return {
        "answer": LETTERS[idx],
        "confidence": float(probs[idx].item()),
        "option_text": question["options"][idx],
        "all_probs": {
            LETTERS[i]: float(probs[i].item())
            for i in range(len(question["options"]))
        },
    }


# ============================================================
# METRICS
# ============================================================

def answer_disagreement(answers: List[str]) -> float:
    normalized = [str(answer).strip().upper()[:1] for answer in answers]
    return 0.0 if len(set(normalized)) == 1 else 1.0


def confidence_disagreement(confidences: List[float]) -> float:
    values = [min(1.0, max(0.0, float(conf))) for conf in confidences]
    mean = sum(values) / len(values)
    var = sum((value - mean) ** 2 for value in values) / len(values)
    return min(var / (1.0 / 3.0), 1.0)


def majority_vote(per_agent: Dict[str, Dict]) -> str:
    scores: Dict[str, float] = {}
    for row in per_agent.values():
        scores[row["answer"]] = scores.get(row["answer"], 0.0) + row["confidence"]
    return max(scores, key=scores.get)


def accuracy(df: pd.DataFrame, agent: str) -> float:
    return float(
        df.apply(
            lambda r: r["per_agent"][agent]["answer"] == r["correct_answer"],
            axis=1,
        ).mean()
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    check_path(BASE_MODEL, "BASE_MODEL")
    check_path(MMLU_CSV, "MMLU_CSV")

    adapters = prepare_adapters()
    temp_c = load_temperature(adapters["C"])

    print("Base model:", BASE_MODEL)
    print("MMLU CSV  :", MMLU_CSV)
    print("Agent R   :", adapters["R"])
    print("Agent D   :", adapters["D"])
    print("Agent C   :", adapters["C"])
    print("Agent C T :", temp_c)

    questions = load_questions(MMLU_CSV, args.limit)
    print("Questions :", len(questions))

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    max_memory = {
        i: "14GiB"
        for i in range(torch.cuda.device_count())
    }

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb,
        device_map="auto",
        max_memory=max_memory or None,
        trust_remote_code=True,
        attn_implementation="sdpa",
    )

    model = PeftModel.from_pretrained(model, str(adapters["R"]), adapter_name="R")
    model.load_adapter(str(adapters["D"]), adapter_name="D")
    model.load_adapter(str(adapters["C"]), adapter_name="C")
    model.eval()

    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "exp0_heterogeneous.jsonl"

    with jsonl_path.open("w", encoding="utf-8") as f:
        for q in tqdm(questions, desc="Agent-R/D/C"):
            per_agent = {}

            for agent, temp in (("R", 1.0), ("D", 1.0), ("C", temp_c)):
                model.set_adapter(agent)
                per_agent[agent] = run_agent(model, tokenizer, agent, q, temp)

            answers = [row["answer"] for row in per_agent.values()]
            confidences = [
                row["confidence"]
                for row in per_agent.values()
            ]

            d_answer = answer_disagreement(answers)
            d_conf = confidence_disagreement(confidences)
            d_q = round(0.5 * d_answer + 0.5 * d_conf, 4)
            ensemble_answer = majority_vote(per_agent)

            record = {
                "question_id": q["question_id"],
                "category": q["category"],
                "difficulty_score": q["difficulty_score"],
                "correct_answer": q["answer"],
                "per_agent": per_agent,
                "ensemble_answer": ensemble_answer,
                "D_answer": round(d_answer, 4),
                "D_semantic": round(d_answer, 4),
                "D_confidence": round(d_conf, 4),
                "D_q": d_q,
                "is_hard_case": d_q > 0.5,
            }

            f.write(json.dumps(record) + "\n")
            f.flush()

    df = pd.read_json(jsonl_path, lines=True)
    rho, p_value = spearmanr(df["D_q"], df["difficulty_score"])

    table = {
        "run": "heterogeneous_agent_r_d_c",
        "n_questions": int(len(df)),
        "spearman_rho_Dq_vs_difficulty": None if math.isnan(rho) else float(rho),
        "spearman_p_value": None if math.isnan(p_value) else float(p_value),
        "mean_D_q": float(df["D_q"].mean()),
        "hard_case_rate": float(df["is_hard_case"].mean()),
        "agent_r_accuracy": accuracy(df, "R"),
        "agent_d_accuracy": accuracy(df, "D"),
        "agent_c_accuracy": accuracy(df, "C"),
        "ensemble_accuracy": float(
            df.apply(
                lambda r: r["ensemble_answer"] == r["correct_answer"],
                axis=1,
            ).mean()
        ),
    }

    json_path = out_dir / "table1_heterogeneous.json"
    csv_path = out_dir / "table1_heterogeneous.csv"

    json_path.write_text(json.dumps(table, indent=2), encoding="utf-8")
    pd.DataFrame([table]).to_csv(csv_path, index=False)

    print("\nDONE. TABLE 1 HETEROGENEOUS ROW:")
    print(json.dumps(table, indent=2))
    print("\nDownload these from Kaggle output:")
    print(jsonl_path)
    print(csv_path)
    print(json_path)


if __name__ == "__main__":
    main()
