# Experiment 0 Next Steps

## 1. Cheap check: re-score existing outputs

This does not rerun models. It recomputes the new disagreement metric from
saved answers and confidences.

```bash
python experiments/experiment_0/rescore_with_new_disagreement.py \
  --input experiments/experiment_0/results/exp0_heterogeneous_mistral_d_n300.jsonl \
  --output experiments/experiment_0/results/rescore_mistral_d_n300_revised.json \
  --adaptive_percentile 80
```

Also run the same command for:

```bash
experiments/experiment_0/results/exp0_heterogeneous.jsonl
experiments/experiment_0/results/exp0_heterogeneous_mistral_d.jsonl
experiments/experiment_0/results/exp0_homogeneous.jsonl
```

If a file has a different name, point `--input` at that JSONL.

What to inspect:

- `hard_case_rate`: should be near `0.20` when `--adaptive_percentile 80`.
- `spearman_rho_Dq_vs_difficulty`: should improve if the old binary metric was
  washing out signal.
- `component_means`: tells whether entropy, JS divergence, confidence variance,
  or correctness diversity is carrying the score.

## 2. Full rerun after the metric fix

Run the different-family row first, because it is the strongest pilot.

```bash
python /kaggle/working/Experiment_zero_hetero_multibackbone.py \
  --qwen_base_model /kaggle/input/qwen2-5-3b-instruct \
  --mistral_base_model /kaggle/input/mistral-7b-instruct-v0-3 \
  --agent_r /kaggle/input/agent-r/agent_r_v0_grpo_adapter.zip \
  --agent_c /kaggle/input/agent-c/results.zip \
  --agent_d /kaggle/input/agent-d-mistral/agent_d_mistral7b_v0.zip \
  --mmlu_path /kaggle/input/mmlu/mmlu_pro_hard_subset.csv \
  --limit 300 \
  --output_dir /kaggle/working
```

Then run the same-family row:

```bash
python /kaggle/working/Experiment_zero_hetero.py \
  --base_model /kaggle/input/qwen2-5-3b-instruct \
  --agent_r /kaggle/input/agent-r/agent_r_v0_grpo_adapter.zip \
  --agent_d /kaggle/input/agent-d/results.zip \
  --agent_c /kaggle/input/agent-c/results.zip \
  --mmlu_path /kaggle/input/mmlu/mmlu_pro_hard_subset.csv \
  --limit 300 \
  --output_dir /kaggle/working
```

## 3. Add role orthogonality analysis

Agent-C cannot be presented as merely “the better agent.” Add these metrics:

- Pairwise error-overlap / Jaccard similarity for R-D, R-C, and D-C.
- Cases where exactly one agent is correct.
- Cases where Agent-C is wrong but low-confidence.
- Agent-C ECE or Brier score.
- Pairwise JS/KL divergence over answer distributions.

The paper should claim heterogeneity only if these show different failure modes,
not just different accuracies.

## 4. Paper cleanup before submission

The current LaTeX still has placeholders and contradictions. Before calling the
paper complete, fill or remove:

- Ablation tables.
- Main evaluation table.
- Co-evolution dynamics plots.
- Diversity regulariser validation table and plot.
- Qualitative example table.
- The conflicting sentence saying the 300-question Mistral-D run has near-zero
  correlation while earlier text says the completed Mistral-D run is 50 samples
  with positive correlation.
- Any claim that the full system “consistently achieves” results before exact
  values exist.
