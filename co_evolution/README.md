# Task 10 - Co-evolution loop

This folder adds the loop that turns heterogeneous Experiment 0 outputs into
per-agent hard-case batches.

Typical dry run:

```bash
python co_evolution/task10_coevolution_loop.py --dry_run --max_iterations 1
```

With updater commands:

```bash
set AGENT_R_UPDATE_CMD=python train_r.py --hard_batch {batch} --iteration {iteration}
set AGENT_D_UPDATE_CMD=python train_d.py --hard_batch {batch} --iteration {iteration}
set AGENT_C_UPDATE_CMD=python train_c.py --hard_batch {batch} --iteration {iteration}
python co_evolution/task10_coevolution_loop.py --max_iterations 5
```

The script writes:

- `iter_XX/agent_r_hard_batch.jsonl`
- `iter_XX/agent_d_hard_batch.jsonl`
- `iter_XX/agent_c_hard_batch.jsonl`
- `iter_XX/manifest.json`
- `coevolution_summary.json`

Task 11 is plugged in through the `regularizer_hint` object on each training
row, so training scripts can add the diversity penalty without changing the
buffer API.
