# Same-family Qwen R/D/C heterogeneous row

This run fills the Experiment 0 row:

`Heterogeneous, same family = Agent-R + Agent-D + Agent-C, all Qwen2.5-3B-Instruct adapters`

## Kaggle inputs to attach

Attach these as Kaggle datasets/model inputs:

- Qwen base model: `qwen2-5-3b-instruct`
- Same-family code/data bundle: `kaggle_same_family_code_data.zip`
- Agent-R adapter: `agent_r_v0_grpo_adapter.zip`
- Agent-D adapter: `results.zip`
- Agent-C adapter: `results.zip`

Local source files:

- `D:\Multi_Agent_Code\experiments\experiment_0\kaggle_same_family_code_data.zip`
- `D:\Multi_Agent_Code\agents\agent_r\agent_r_v0_grpo_adapter.zip`
- `D:\Multi_Agent_Code\agents\agent_d\results.zip`
- `D:\Multi_Agent_Code\agents\agent_c\results.zip`

## Kaggle setup cell

Run this first if the code/data zip is attached as a Kaggle input:

```bash
cd /kaggle/working
unzip -o /kaggle/input/same-family-code-data/kaggle_same_family_code_data.zip -d /kaggle/working
```

Change `same-family-code-data` to the actual Kaggle input folder name if Kaggle gives it a different slug.

## Smoke test row

Run this first. It should produce 50 rows and the table JSON quickly enough to confirm all paths are right.

```bash
python /kaggle/working/experiments/experiment_0/Experiment_zero_hetero.py \
  --base_model /kaggle/input/qwen2-5-3b-instruct \
  --agent_r /kaggle/input/agent-r/agent_r_v0_grpo_adapter.zip \
  --agent_d /kaggle/input/agent-d/results.zip \
  --agent_c /kaggle/input/agent-c/results.zip \
  --mmlu_path /kaggle/working/data_preparation/mmlu_pro_hard_subset.csv \
  --output_dir /kaggle/working \
  --limit 50
```

## Full same-family row

After the smoke test succeeds, remove `--limit 50`:

```bash
python /kaggle/working/experiments/experiment_0/Experiment_zero_hetero.py \
  --base_model /kaggle/input/qwen2-5-3b-instruct \
  --agent_r /kaggle/input/agent-r/agent_r_v0_grpo_adapter.zip \
  --agent_d /kaggle/input/agent-d/results.zip \
  --agent_c /kaggle/input/agent-c/results.zip \
  --mmlu_path /kaggle/working/data_preparation/mmlu_pro_hard_subset.csv \
  --output_dir /kaggle/working
```

## Outputs to download

Download these from `/kaggle/working`:

- `exp0_heterogeneous.jsonl`
- `table1_heterogeneous.csv`
- `table1_heterogeneous.json`

Copy them locally into:

`D:\Multi_Agent_Code\experiments\experiment_0\results\`
