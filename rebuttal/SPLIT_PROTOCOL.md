# Strict Split Protocol

This protocol repairs the Agent-C/evaluation overlap found in the current
checkout. It must be used for every new rebuttal run.

## Immutable assignment

| Split | Questions | Permitted use |
|---|---:|---|
| Train | 2,416 | Agent specialization, hard-case buffer, and co-evolution updates |
| Validation | 300 | Temperature scaling, hyperparameter selection, debugging, and model selection |
| Test | 300 | One final evaluation after all choices are frozen |

Manifest:
`rebuttal/splits/mmlu_pro_hard_split_manifest.csv`

Current SHA-256:
`d06f8afb50f7fff4fb0f5dc0a7ca19c040d25dbe0fad3c8544d1fd6353129ed8`

The committed manifest contains only `question_id` and `split`. Per-question
difficulty values are not duplicated into it. Aggregate balance diagnostics
are stored in `mmlu_pro_hard_split_summary.json`.

## Safety properties

- Unknown question IDs abort the run.
- Duplicate IDs in either the manifest or an input batch abort the run.
- A manifest hash mismatch aborts the run.
- Agent-C uses only `train` for fitting and `validation` for temperature scaling.
- Co-evolution accepts `train` rows only.
- Experiment 0 runners default to `validation`.
- Validation and test results use different filenames, preventing accidental resume-file mixing.
- The `test` split must be requested explicitly after all choices are frozen.

## 1. Retrain Agent-C on Kaggle

Upload the repository or, at minimum, the Agent-C script, `split_guard.py`,
the split manifest, and the MMLU-Pro hard data.

```bash
CUDA_VISIBLE_DEVICES=0 python agents/agent_c/agent_c_calibration_fast.py \
  --mmlu_json data_preparation/mmlu_pro_hard_subset.json \
  --split_manifest rebuttal/splits/mmlu_pro_hard_split_manifest.csv \
  --split_manifest_sha256 d06f8afb50f7fff4fb0f5dc0a7ca19c040d25dbe0fad3c8544d1fd6353129ed8 \
  --output_dir /kaggle/working/agent_c_strict
```

Do not use `--allow_legacy_random_split` for rebuttal evidence.

## 2. Run validation inference

Same-family:

```bash
python experiments/experiment_0/Experiment_zero_hetero.py \
  --mmlu_path data_preparation/mmlu_pro_hard_subset.json \
  --agent_r /path/to/agent_r \
  --agent_d /path/to/agent_d \
  --agent_c /kaggle/working/agent_c_strict \
  --split_manifest rebuttal/splits/mmlu_pro_hard_split_manifest.csv \
  --split_manifest_sha256 d06f8afb50f7fff4fb0f5dc0a7ca19c040d25dbe0fad3c8544d1fd6353129ed8 \
  --eval_split validation
```

Different-family:

```bash
python experiments/experiment_0/Experiment_zero_hetero_multibackbone.py \
  --mmlu_path data_preparation/mmlu_pro_hard_subset.json \
  --agent_r /path/to/agent_r \
  --agent_c /kaggle/working/agent_c_strict \
  --agent_d /path/to/mistral_agent_d \
  --split_manifest rebuttal/splits/mmlu_pro_hard_split_manifest.csv \
  --split_manifest_sha256 d06f8afb50f7fff4fb0f5dc0a7ca19c040d25dbe0fad3c8544d1fd6353129ed8 \
  --eval_split validation
```

The corresponding homogeneous runner uses `--split-manifest` and
`--eval-split validation` (hyphenated argument names).

## 3. Build co-evolution batches from training outputs only

The input JSONL must contain predictions for training questions. Passing
validation/test rows is safe: the guard excludes them and records the counts.

```bash
python co_evolution/task10_coevolution_loop.py \
  --exp0_jsonl /path/to/training_predictions.jsonl \
  --split_manifest rebuttal/splits/mmlu_pro_hard_split_manifest.csv \
  --split_manifest_sha256 d06f8afb50f7fff4fb0f5dc0a7ca19c040d25dbe0fad3c8544d1fd6353129ed8 \
  --output_dir /kaggle/working/coevolution_strict \
  --max_iterations 30
```

The current co-evolution driver still does not form a closed loop: it does not
reload updated adapters and rescore fresh training/validation data after each
iteration. This command is therefore a split-safe batch builder, not yet a
valid reproduction of Table 3.

## 4. Freeze choices, then evaluate test once

After selecting weights, thresholds, iteration count, and checkpoints using
training/validation only, change only:

```text
--eval_split validation
```

to:

```text
--eval_split test
```

Archive the exact command, manifest hash, code commit, adapter hashes, seed,
stdout log, and split-specific result files. Do not tune anything after
looking at test metrics.
