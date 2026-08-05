# A100 Rebuttal Runbook

This is the operational plan for rerunning the highest-value NeurIPS rebuttal
experiments on the MBZUAI/CIAI A100 cluster. Use the stable IDs `A100-01`
through `A100-12` when assigning or discussing a step.

The goal is not to rerun every claim in the submitted paper. The goal is to
produce a small set of trustworthy results that directly answer the reviewers:

1. a leakage-free held-out result;
2. a genuine closed-loop co-evolution result;
3. a regularizer control;
4. a label-free score ablation; and
5. evaluation against an independent model pass-rate difficulty target.

## Non-negotiable rules

- Do not launch a full run until the three-iteration pilot passes every gate.
- Co-evolution and buffer construction may read `train` questions only.
- Temperature scaling and hyperparameter selection may read `validation` only.
- Do not inspect `test` metrics until the configuration and checkpoints are frozen.
- Run the final test evaluation once.
- Never place cluster credentials, API keys, access tokens, or private keys in Git.
- Every reported number must be traceable to a commit, manifest hash, seed,
  configuration, checkpoint hash, and raw output.
- The current `co_evolution/task10_coevolution_loop.py` is a split-safe batch
  builder, not yet a valid closed feedback loop. It must not be used to claim
  Table 3 reproduction until `A100-04` is complete.

## Current fixed protocol

| Item | Value |
|---|---|
| Train questions | 2,416 |
| Validation questions | 300 |
| Test questions | 300 |
| Seeds | 42, 1337, 2024 |
| Co-evolution budget | 30 iterations, subject to pilot validation |
| Manifest | `rebuttal/splits/mmlu_pro_hard_split_manifest.csv` |
| Manifest SHA-256 | `d06f8afb50f7fff4fb0f5dc0a7ca19c040d25dbe0fad3c8544d1fd6353129ed8` |
| Primary static setting | Qwen Agent-R/C plus Mistral Agent-D |
| Development evaluation | Validation only |
| Final evaluation | Test once, after freeze |

## Status board

| ID | Status | Step | Exit condition |
|---|---|---|---|
| A100-01 | `[ ]` | Record cluster configuration | Scheduler, partition, A100 memory, quota, and storage are known |
| A100-02 | `[~]` | Freeze code and data inputs | Rebuttal branch is committed and manifest hash is verified |
| A100-03 | `[!]` | Stage original adapters and artifacts | Agent-R/D/C adapters and base models are available on cluster storage |
| A100-04 | `[!]` | Implement the real closed loop | Updated adapters are reloaded and fresh predictions are produced every iteration |
| A100-05 | `[ ]` | Build and verify A100 environment | CUDA, PyTorch, PEFT, Transformers, TRL, and bitsandbytes smoke tests pass |
| A100-06 | `[ ]` | Retrain Agent-C strictly | Training uses train IDs and temperature scaling uses validation IDs |
| A100-07 | `[ ]` | Run three-iteration pilot | All correctness, split, gradient, checkpoint, and metric gates pass |
| A100-08 | `[ ]` | Run regularized validation experiment | Seeds 42/1337/2024 finish with complete trajectories |
| A100-09 | `[ ]` | Run no-regularizer validation control | Same seeds and budget finish with only the regularizer disabled |
| A100-10 | `[ ]` | Build pass-rate difficulty | Independent reference-model response matrix and target are complete |
| A100-11 | `[ ]` | Freeze and evaluate test once | Frozen configurations produce the final untouched-test outputs |
| A100-12 | `[ ]` | Archive, analyze, and draft rebuttal | Artifacts are hashed, copied off scratch storage, and summarized |

## A100-01 - Record cluster configuration

Run these commands on the login node and save the output in the run log:

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
command -v sbatch
sinfo -o "%P %G %l %a" 2>/dev/null | head -20
python --version
```

Also record:

- A100 memory: 40 GB or 80 GB;
- maximum concurrent GPUs;
- Slurm partition and account;
- maximum wall time;
- project/scratch storage paths;
- whether compute nodes have internet access; and
- which CUDA/PyTorch modules are supported.

Do not paste authentication material into issues, logs, or this repository.

## A100-02 - Freeze code and data inputs

Before copying anything to the cluster:

```bash
git status --short
git rev-parse HEAD
sha256sum rebuttal/splits/mmlu_pro_hard_split_manifest.csv
```

The manifest digest must equal:

```text
d06f8afb50f7fff4fb0f5dc0a7ca19c040d25dbe0fad3c8544d1fd6353129ed8
```

Commit the run-preparation changes intentionally. On the cluster, clone that
exact branch or checkout the exact commit. Do not run from a moving branch
without recording its commit.

## A100-03 - Stage models and original artifacts

Use persistent project storage for:

- Qwen2.5-3B-Instruct;
- Mistral-7B-Instruct-v0.3;
- the original Agent-R adapter;
- the original Mistral Agent-D adapter;
- any recoverable Agent-C adapter and temperature file;
- MMLU-Pro hard data;
- the strict split manifest; and
- any original Kaggle iteration outputs, logs, and configurations.

Use node-local scratch only for caches and temporary checkpoints. Keep model
weights and generated adapters outside Git.

Suggested external layout:

```text
<project-storage>/neurips_rebuttal/
  models/
    qwen2.5-3b-instruct/
    mistral-7b-instruct-v0.3/
  input_adapters/
    agent_r/
    agent_d/
    recovered_agent_c/
  data/
    mmlu_pro_hard_subset.json
    mmlu_pro_hard_split_manifest.csv
  runs/
    <run_id>/
```

Record SHA-256 hashes for every adapter file before running.

## A100-04 - Implement the genuine closed feedback loop

This is the blocking engineering step. One iteration must perform:

1. load the current Agent-R/D/C adapters;
2. score a new training batch with those adapters;
3. compute disagreement without using the surface difficulty target;
4. update the rolling train-only hard-case buffer;
5. create agent-specific training batches;
6. update each LoRA adapter;
7. apply the diversity regularizer in the actual differentiable training loss;
8. save the new adapters, optimizer/training logs, and hashes;
9. reload the new adapters;
10. rescore validation data with the updated adapters; and
11. write iteration metrics from the fresh validation predictions.

The loop must not rebuild every iteration from the same static Experiment 0
file. A `regularizer_hint` in JSON is not evidence that the regularizer
affected gradients.

Required command interface for the new runner:

```text
--seed
--max_iterations
--train_manifest
--validation_manifest
--agent_r
--agent_d
--agent_c
--regularizer_weight
--min_js_divergence
--output_dir
--resume
```

The full Slurm command will be filled in only after this runner exists and
passes local tests.

## A100-05 - Build the A100 environment

Use the cluster-supported CUDA module or container. Do not blindly install a
CUDA build that conflicts with the driver.

Illustrative setup:

```bash
module purge
module load <cluster-cuda-module>

python -m venv <project-storage>/venvs/neurips-rebuttal
source <project-storage>/venvs/neurips-rebuttal/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verify inside an allocated GPU job:

```bash
python - <<'PY'
import torch
import transformers
import peft
import bitsandbytes

print("torch", torch.__version__)
print("cuda available", torch.cuda.is_available())
print("cuda runtime", torch.version.cuda)
print("gpu", torch.cuda.get_device_name(0))
print("bf16", torch.cuda.is_bf16_supported())
print("transformers", transformers.__version__)
print("peft", peft.__version__)
print("bitsandbytes", bitsandbytes.__version__)
assert torch.cuda.is_available()
PY
```

Save the final environment:

```bash
python -m pip freeze > <run-dir>/environment.freeze.txt
```

## A100-06 - Retrain Agent-C with the strict split

Agent-C must be fitted on `train` and temperature-scaled on `validation`.

```bash
CUDA_VISIBLE_DEVICES=0 python agents/agent_c/agent_c_calibration_fast.py \
  --model_path <models>/qwen2.5-3b-instruct \
  --mmlu_json data_preparation/mmlu_pro_hard_subset.json \
  --split_manifest rebuttal/splits/mmlu_pro_hard_split_manifest.csv \
  --split_manifest_sha256 d06f8afb50f7fff4fb0f5dc0a7ca19c040d25dbe0fad3c8544d1fd6353129ed8 \
  --seed 42 \
  --output_dir <run-dir>/agent_c_strict
```

Reject the output if `agent_c_meta.json` does not report
`mode: strict_manifest`, 2,416 training rows, 300 validation rows, and the
expected manifest digest.

## A100-07 - Three-iteration pilot

Run only seed 42 for three iterations. The pilot passes only if:

- all buffer question IDs are in `train`;
- no validation or test ID appears in any training batch;
- the three adapters are stored separately;
- adapter hashes change after each update;
- the updater logs show finite, nonzero gradients;
- the regularizer appears in the differentiable loss and its gradient path is active;
- validation predictions are regenerated after every update;
- validation output timestamps and adapter hashes match the iteration;
- no NaN/Inf values occur;
- memory stays below the allocated limit; and
- a stopped job can resume without repeating or mixing iterations.

Do not extrapolate pilot metrics or cite them in the rebuttal.

## A100-08 and A100-09 - Full validation runs

After the pilot passes, run seeds `42`, `1337`, and `2024`.

Conditions:

| Run | Regularizer | Everything else |
|---|---|---|
| A100-08 | Submitted/corrected setting | Frozen |
| A100-09 | Disabled (`lambda=0`) | Identical to A100-08 |

Use a Slurm job array if three A100s are available:

```bash
#!/bin/bash
#SBATCH --job-name=neurips-coev
#SBATCH --partition=<partition>
#SBATCH --account=<account>
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=<cluster-limit>
#SBATCH --array=0-2
#SBATCH --output=<logs>/coev_%A_%a.out
#SBATCH --error=<logs>/coev_%A_%a.err

set -euo pipefail
SEEDS=(42 1337 2024)
SEED="${SEEDS[$SLURM_ARRAY_TASK_ID]}"

source <project-storage>/venvs/neurips-rebuttal/bin/activate
cd <project-storage>/Multi_agent_neurips

# Replace this line with the A100-04 runner only after its pilot passes.
srun python <closed-loop-runner> \
  --seed "$SEED" \
  --max_iterations 30 \
  --output_dir "<run-root>/regularized/seed_${SEED}" \
  <frozen-arguments>
```

Submit the no-regularizer control as a separate array with the same arguments
except `--regularizer_weight 0`.

Expected timing after the implementation is stable:

- Agent-C: approximately 0.5-1.5 hours;
- one 30-iteration seed: approximately 4-8 hours;
- three seeds on three A100s: approximately 4-8 hours wall time;
- regularized plus no-regularizer arrays: approximately 8-16 hours, excluding queues.

These are planning estimates. Record actual wall time and peak memory.

## A100-10 - Independent pass-rate difficulty

Build a question-by-reference-model correctness matrix using reference models
that are not the evaluated Agent-R/D/C outputs:

```text
d_pass(q) = 1 - mean(reference-model correctness for q)
```

Requirements:

- use the same question IDs and split manifest;
- record model name, exact revision, prompt, decoding, and output hash;
- require adequate model coverage for every evaluated question;
- keep evaluated agent outputs out of the reference panel;
- report uncertainty and per-category coverage; and
- fit Rasch/IRT only if the response matrix is large enough and converges.

Run reference-model inference in parallel with A100-08/A100-09 when GPU quota
allows. If the original 12-backbone matrix is recovered, validate and reuse it
instead of spending GPU time unnecessarily.

## A100-11 - Freeze and evaluate test once

Before test evaluation, write a freeze record containing:

- selected iteration/checkpoint;
- component weights;
- hard-case threshold;
- regularizer weight and diversity floor;
- seed list;
- exact code commit;
- manifest digest;
- environment freeze;
- base-model and adapter hashes; and
- validation results used for selection.

Then change the evaluation split from `validation` to `test` without changing
any other setting. Store test outputs in a new split-specific directory. Do
not tune, select checkpoints, or rerun variants after examining test results.

## A100-12 - Archive and analyze

Each run directory must contain:

```text
<run_id>/
  RUN_METADATA.json
  command.txt
  environment.freeze.txt
  git_commit.txt
  split_manifest.sha256
  slurm/
  seed_42/
  seed_1337/
  seed_2024/
  aggregate/
```

Archive before scratch cleanup:

- raw predictions for every iteration;
- training and validation IDs;
- agent-specific batches;
- adapter checkpoints and hashes;
- loss, gradient, accuracy, ECE, JS, and correlation trajectories;
- stderr/stdout and Slurm accounting;
- regularized/no-regularizer configuration diff; and
- final aggregate CSV/JSON.

The MacBook remains responsible for the repository tests, canonical rescoring,
bootstrap/permutation analysis, figures, consistency checks, and rebuttal
drafting. The A100 cluster is responsible for model inference and LoRA updates.

## Stop conditions

Stop the full run and diagnose if any of the following occurs:

- a train/validation/test overlap is detected;
- the manifest digest differs;
- adapter hashes do not change after an update;
- an iteration reuses stale predictions;
- the diversity term never enters the gradient-bearing loss;
- loss or metrics become NaN/Inf;
- resume changes prior iteration outputs;
- validation data enters the buffer; or
- test data is accessed before the freeze record exists.

## Immediate next action

Complete `A100-01` by recording the cluster configuration. In parallel,
complete `A100-04` locally and add the real closed-loop runner. Only then
create the final Slurm scripts and launch `A100-07`.
