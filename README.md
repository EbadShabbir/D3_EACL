# Multi-Agent Co-Evolution for Hard-Case Discovery

Research code for studying whether heterogeneous language-model agents can
identify difficult multiple-choice questions through disagreement, calibration,
and iterative hard-case training.

This repository is an active research prototype. Reported outputs are
experimental artifacts, not production guarantees.

## Repository map

| Path | Purpose |
| --- | --- |
| `data_preparation/` | Prepare MMLU-Pro and optional secondary datasets. |
| `disagreement_scorer/` | Compute answer, distribution, confidence, and correctness disagreement. |
| `hard_case_buffer/` | Maintain and sample the rolling hard-case buffer. |
| `agents/agent_r/` | Reasoning-agent training scripts and notebooks. |
| `agents/agent_d/` | Domain-agent training code. |
| `agents/agent_c/` | Calibration-agent training code. |
| `experiments/experiment_0/` | Homogeneous and heterogeneous baseline experiments and result analysis. |
| `co_evolution/` | Build per-agent hard batches across co-evolution iterations. |
| `diversity_regularizer/` | Penalize agent-distribution collapse. |
| `paper/experiment.tex` | Current paper source. |
| `scripts/` | Small repository utilities such as model download helpers. |

Large checkpoints, adapter archives, generated Kaggle bundles, private
documents, raw caches, and credentials are intentionally excluded from Git.

## Setup

Python 3.10 or newer is recommended. GPU training scripts may require a CUDA
environment compatible with the installed PyTorch and `bitsandbytes` versions.

```powershell
git clone https://github.com/EbadShabbir/Multi_agent_neurips.git
cd Multi_agent_neurips
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Put provider credentials in `.env` or in the shell environment. The experiment
scripts recognize variables such as `NVIDIA_API_KEY`, `GROQ_API_KEY`, and
`OPENAI_API_KEY`.

## Core workflow

1. Prepare a hard-question subset with
   `data_preparation/task1_prep_data.py`.
2. Score inter-agent disagreement with
   `disagreement_scorer/task2_disagreement_scorer.py`.
3. Route high-disagreement examples through
   `hard_case_buffer/Task3_hard_case_buffer.py`.
4. Train or update Agent-R, Agent-D, and Agent-C with the scripts in their
   respective directories.
5. Run the baselines in `experiments/experiment_0/`.
6. Build iteration-specific hard batches with
   `co_evolution/task10_coevolution_loop.py`.

See the component READMEs and `NEXT_STEPS_EXPERIMENT0.md` for detailed commands
and current research follow-ups.

## Validation

The lightweight unit tests do not require model downloads:

```powershell
python disagreement_scorer/test_disagreement_scorer.py
python -m unittest discover -s diversity_regularizer -p "test_*.py"
python -m unittest discover -s co_evolution -p "test_*.py"
```

Training and full experiment runs require the model adapters and datasets named
in the component documentation.

## Security and artifact policy

- Never place API tokens directly in scripts, notebooks, dependency files, or
  experiment outputs.
- Keep checkpoints and adapter archives in external artifact storage.
- Commit small, reviewable result tables when they support a paper result; keep
  bulk run outputs outside Git.
- Before publishing a notebook, clear credentials and unnecessary cell output.

## Contributing

Read `CONTRIBUTING.md` before opening a pull request. Keep changes scoped,
document validation commands, and avoid committing generated or private files.
