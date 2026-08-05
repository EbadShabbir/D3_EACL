"""Build the executable repository evidence-audit notebook with nbformat."""

from __future__ import annotations

import json
from pathlib import Path

import nbformat as nbf

from audit_core import run_audit


HERE = Path(__file__).resolve().parent
NOTEBOOK_PATH = HERE / "repository_evidence_audit.ipynb"


def format_number(value, digits: int = 3) -> str:
    if value is None:
        return "not available"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def build_notebook() -> None:
    audit = run_audit(write_artifacts=True)
    overlap = audit["agent_c_overlap"]
    inventory = audit["artifact_inventory"]
    duplicate_groups = [
        row for row in audit["hash_groups"] if row["exact_duplicate_group"]
    ]

    summary_markdown = f"""# Repository Evidence Audit

## tl;dr

- The checkout contains **{inventory['static_result_jsonl_count']} static result JSONL files** and **{inventory['rescored_result_jsonl_count']} rescored JSONL files**, but **{inventory['coevolution_result_artifact_count']} stored co-evolution result artifacts** and **{inventory['checkpoint_or_adapter_archive_count']} checkpoint or adapter archives**.
- Under the documented Agent-C `deadline` split recreation, **{overlap['evaluation_in_agent_c_training']} of {overlap['evaluation_rows']}** evaluated questions fall in Agent-C training and **{overlap['evaluation_in_agent_c_validation']}** fall in Agent-C validation. This means the repository does not establish a held-out test set for the static `n=300` evaluation.
- The saved result directory contains **{len(duplicate_groups)} exact duplicate file group(s)**. Duplicated filenames must not be treated as independent experimental runs.
- The stored static outputs are suitable for rescoring and descriptive ablations. They are not sufficient on their own to substantiate the submitted 30-iteration, three-seed, seven-benchmark claims.
"""

    notebook = nbf.v4.new_notebook()
    notebook["metadata"]["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook["metadata"]["language_info"] = {"name": "python", "version": "3.12"}
    notebook["cells"] = [
        nbf.v4.new_markdown_cell(summary_markdown),
        nbf.v4.new_markdown_cell(
            """## Context & Methods

This notebook audits the repository-local evidence intended to support the NeurIPS rebuttal. The unit of analysis is one saved model-response row per question. Checks cover completeness, uniqueness, target variation, exact file duplication, score reproducibility, agent-output coverage, and overlap between Agent-C specialization data and the static evaluation set.

### Key Assumptions

- Agent-C used the documented `deadline` profile: seed 42, at most 2,500 rows, and a 15% validation fraction.
- The `n=300` experiment selected the first 300 rows from `mmlu_pro_hard_subset.json`, matching the repository evaluation loader.
- Repository-local files are the complete evidence available for this audit. External Kaggle artifacts are treated as missing until attached.
"""
        ),
        nbf.v4.new_code_cell(
            """from pathlib import Path
import json
import pandas as pd

from audit_core import ARTIFACT_DIR, REPO_ROOT, run_audit

pd.set_option("display.max_columns", 50)
audit = run_audit(write_artifacts=True)
print("Repository:", REPO_ROOT)
print("Artifacts:", ARTIFACT_DIR)
"""
        ),
        nbf.v4.new_markdown_cell(
            """## Data

The audit uses the checked-in Experiment 0 JSONL files, rescored JSONLs, MMLU-Pro hard-subset data, and GPQA preparation output. It does not download models or infer missing results.
"""
        ),
        nbf.v4.new_code_cell(
            """result_profiles = pd.DataFrame(audit["result_profiles"])
result_profiles[[
    "file", "rows", "unique_question_ids", "duplicate_question_rows",
    "difficulty_complete_rate", "difficulty_unique_values",
    "three_agent_complete_rows", "option_probability_complete_rows",
    "raw_spearman_rho", "revised_spearman_rho"
]]
"""
        ),
        nbf.v4.new_markdown_cell(
            """## Results

### Saved outputs have useful static coverage but do not contain co-evolution trajectories

The table below distinguishes stored static predictions from the iteration-level artifacts and checkpoints required to reproduce Table 3.
"""
        ),
        nbf.v4.new_code_cell(
            """inventory = audit["artifact_inventory"]
pd.DataFrame([
    {"artifact": "Static result JSONLs", "count": inventory["static_result_jsonl_count"]},
    {"artifact": "Rescored result JSONLs", "count": inventory["rescored_result_jsonl_count"]},
    {"artifact": "Co-evolution result artifacts", "count": inventory["coevolution_result_artifact_count"]},
    {"artifact": "Checkpoint or adapter archives", "count": inventory["checkpoint_or_adapter_archive_count"]},
])
"""
        ),
        nbf.v4.new_markdown_cell(
            """### Some result filenames are exact copies, not independent runs

Exact SHA-256 matches identify copied artifacts. These files can be aliases for convenience, but they must not be counted as separate seeds or replications.
"""
        ),
        nbf.v4.new_code_cell(
            """hash_groups = pd.DataFrame(audit["hash_groups"])
hash_groups.loc[hash_groups["exact_duplicate_group"], ["file_count", "files", "sha256"]]
"""
        ),
        nbf.v4.new_markdown_cell(
            """### The available Agent-C split overlaps the static evaluation

This reconstruction follows the checked-in Agent-C loader exactly: shuffle the full hard subset with seed 42, retain at most 2,500 questions, allocate the first 15% to validation, and use the rest for training. The experiment loader then evaluates the first 300 hard-subset rows.
"""
        ),
        nbf.v4.new_code_cell(
            """overlap = audit["agent_c_overlap"]
pd.DataFrame([
    {"partition": "Agent-C training", "evaluation_questions": overlap["evaluation_in_agent_c_training"]},
    {"partition": "Agent-C validation", "evaluation_questions": overlap["evaluation_in_agent_c_validation"]},
    {"partition": "Excluded from Agent-C", "evaluation_questions": overlap["evaluation_excluded_from_agent_c"]},
])
"""
        ),
        nbf.v4.new_markdown_cell(
            """### GPQA currently has no usable difficulty variation

A rank correlation requires variation in the target. A constant difficulty value makes Spearman correlation undefined.
"""
        ),
        nbf.v4.new_code_cell(
            """dataset_profiles = pd.DataFrame(audit["dataset_profiles"])
dataset_profiles[[
    "file", "rows", "unique_question_ids", "difficulty_column",
    "difficulty_complete_rows", "difficulty_unique_values",
    "difficulty_min", "difficulty_max", "difficulty_std"
]]
"""
        ),
        nbf.v4.new_markdown_cell(
            """### A deterministic split repair is ready, but it is not yet wired into training

The manifest is stratified by category and difficulty quintile. It assigns every one of the 3,016 MMLU-Pro hard questions exactly once to train, validation, or test. Generating a manifest does not repair the submitted result by itself: Agent-C must be retrained and all co-evolution selection must be restricted to the training partition.
"""
        ),
        nbf.v4.new_code_cell(
            """from create_split_manifest import build_manifest, write_manifest

split_manifest = build_manifest()
split_summary = write_manifest()
assert split_manifest["question_id"].nunique() == len(split_manifest)
assert split_manifest["split"].value_counts().to_dict() == {
    "train": 2416, "validation": 300, "test": 300
}
pd.DataFrame([
    {
        "split": split,
        "rows": split_summary["counts"][split],
        "difficulty_mean": details["mean"],
        "difficulty_std": details["std"],
    }
    for split, details in split_summary["difficulty_range_by_split"].items()
])
"""
        ),
        nbf.v4.new_markdown_cell(
            """### Canonical rescoring supports both saved schemas

The canonical scorer handles heterogeneous `per_agent` rows and homogeneous `per_role` rows. It reproduces the stored revised heterogeneous score to within rounding tolerance and evaluates both the submitted score and two no-correctness variants. The target in this section remains the criticized surface heuristic, so these results test implementation and sensitivity rather than validate intrinsic difficulty.
"""
        ),
        nbf.v4.new_code_cell(
            """from local_saved_output_analysis import main as run_local_analysis

run_local_analysis()
component_ablation = pd.read_csv(
    ARTIFACT_DIR / "local_rescoring" / "component_ablation.csv"
)
key_scores = [
    "D_full",
    "D_no_correctness_paper",
    "D_no_correctness_renormalized",
]
key_files = [
    "experiments/experiment_0/results/exp0_heterogeneous.jsonl",
    "experiments/experiment_0/results/exp0_heterogeneous_mistral_d_n300.jsonl",
]
component_ablation.loc[
    component_ablation["file"].isin(key_files)
    & component_ablation["score"].isin(key_scores),
    [
        "file", "score", "n", "spearman_rho",
        "bootstrap_ci_lower", "bootstrap_ci_upper", "permutation_p",
    ],
]
"""
        ),
        nbf.v4.new_markdown_cell(
            """### Surface-proxy triage is exploratory only

Top-20% precision and enrichment are computed to validate the evaluation code. These values must not be presented as rebuttal evidence until the positive class is defined by independent pass-rate, IRT, or human difficulty.
"""
        ),
        nbf.v4.new_code_cell(
            """surface_triage = pd.read_csv(
    ARTIFACT_DIR / "local_rescoring" / "surface_proxy_triage.csv"
)
surface_triage.loc[
    (surface_triage["file"] == "experiments/experiment_0/results/exp0_heterogeneous_mistral_d_n300.jsonl")
    & surface_triage["score"].isin(key_scores),
    ["score", "n", "precision", "recall", "enrichment_over_random"],
]
"""
        ),
        nbf.v4.new_markdown_cell(
            """## Takeaways

1. **Safe now:** static-output rescoring, label-free score ablations, descriptive agent-error analysis, and code-level split/label auditing.
2. **Not safe yet:** citing Table 3 as reproduced, treating duplicated files as independent runs, claiming held-out Agent-C evaluation, or reporting cross-benchmark difficulty correlations from constant targets.
3. **Split repair ready:** a tested 2,416/300/300 manifest exists, but it must still be enforced in Agent-C training and the co-evolution pipeline.
4. **Required next:** recover the original iteration-level artifacts and adapters, rerun on the strict split, and construct a non-constant independently grounded difficulty target.
5. The generated CSV and JSON files in `rebuttal/artifacts/` are the compact machine-readable audit record.
"""
        ),
    ]
    nbf.validate(notebook)
    nbf.write(notebook, NOTEBOOK_PATH)
    print(f"Wrote {NOTEBOOK_PATH}")


if __name__ == "__main__":
    build_notebook()
