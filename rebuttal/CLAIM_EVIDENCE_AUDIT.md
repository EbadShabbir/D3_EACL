# NeurIPS Rebuttal Claim-Evidence Audit

Audit date: 2026-07-27

Repository branch: `agent/organize-research-repository`

Submitted paper: `10833_Disagreement_Diversity_a.pdf`

## Technical summary

The repository is sufficient for static Experiment 0 rescoring and descriptive
analysis, but it is not currently sufficient to reproduce the submitted
co-evolution, multi-seed, or seven-benchmark results. The most important
verified issue is evaluation overlap: under the checked-in Agent-C data-loading
logic, 202 of the 300 static evaluation questions are in Agent-C's training
partition and another 38 are in its validation partition.

No iteration-level co-evolution result files, co-evolved adapters, or checkpoint
archives are present in the current checkout. The checked-in co-evolution
driver rebuilds its buffer from the same static input rows at every iteration
and delegates model updates to external commands that are not included.

These findings do not prove that the submitted experiments were never run.
They establish that the current repository cannot verify them. External Kaggle
notebooks, outputs, adapters, or logs must be recovered before those results
are used in the rebuttal.

## Evidence status

| Claim or result | Repository evidence | Status | Severity | Required action |
|---|---|---|---|---|
| Static same-family correlation near 0.154 | The 50-row rescored file reproduces `rho=0.1539` | Verified for one stored sample | Medium | Clarify `n=50`; do not present as a three-seed result without seed files |
| Static different-family `n=300` correlation near 0.003 | The rescored file reproduces `rho=0.00286` | Verified for one stored output | Medium | Treat duplicate filenames as aliases, not independent runs |
| Table 3 Iter 0 to Iter 30 improvement | No iteration trajectories or endpoint outputs are present | Not reproducible | Critical | Recover original artifacts or rerun a correct co-evolution pipeline |
| Three-seed means and standard deviations | No per-seed outputs or seed manifests are present | Not reproducible | Critical | Recover or rerun all seeds |
| Seven benchmarks and 12 backbones | No full prediction matrix or matching runner is present | Not reproducible | Critical | Recover model-response matrix and scripts |
| GPQA disagreement-difficulty correlation | Prepared GPQA records all have `difficulty_score=1.0` | Invalid with current target | Critical | Construct a non-constant target before correlation |
| BBH disagreement-difficulty correlation | BBH preparation assigns `difficulty_score=1.0` | Invalid with current target | Critical | Construct a non-constant target before correlation |
| Held-out evaluation with no evaluation training | Agent-C's documented split overlaps 240 of 300 evaluation questions | Contradicted by current code | Critical | Introduce explicit train/validation/test manifests and retrain Agent-C |
| Label-free method | Correctness is used in the score, Agent-C routing, target answers, and supervised updates | Contradicted for full pipeline | High | Describe inference-only and supervised variants separately |
| Diversity regularizer used during co-evolution | Driver records a `regularizer_hint`; no included update script consumes it | Not established | Critical | Integrate the loss into actual update scripts and verify gradients/logs |
| Regularizer values `tau_JS=0.30`, `lambda=1.0` | Driver defaults are `0.03` and `0.05` | Configuration conflict | High | Recover the actual run config or rerun with declared values |
| Component ablation in Table 11 | No component-sweep script or raw result file is present | Not reproducible | High | Recover or rerun the sweep |
| Bootstrap and permutation significance | No matching saved script/output for the submitted claims is present | Not reproducible | High | Implement locally on verified outputs |
| Cross-benchmark transfer | No transfer predictions or frozen-adapter evaluation output is present | Not reproducible | Critical | Recover artifacts or remove from rebuttal evidence |

## Data-quality findings

### Critical — Agent-C specialization overlaps the static evaluation

The checked-in Agent-C loader:

1. loads `mmlu_pro_hard_subset.json`;
2. shuffles it with seed 42;
3. retains 2,500 rows under the `deadline` profile;
4. assigns 375 rows to validation and 2,125 to training.

The static experiment loader selects the first 300 rows of the same hard-subset
file. Reconstructing both procedures produces:

| Evaluation relationship | Questions | Share |
|---|---:|---:|
| In Agent-C training | 202 | 67.3% |
| In Agent-C validation | 38 | 12.7% |
| Excluded from Agent-C | 60 | 20.0% |

This prevents the current static result from being described as held-out with
respect to Agent-C. The smallest defensible repair is to create immutable split
manifests before any specialization or co-evolution and retrain Agent-C using
only the training partition.

The implemented repair now generates a deterministic, category- and
difficulty-stratified manifest with 2,416 training, 300 validation, and 300
test questions. Tests verify exact coverage, unique IDs, deterministic output,
and a maximum category-share gap below 0.6 percentage points. This completes
the split design. Fail-closed guards are now wired into Agent-C, the
co-evolution batch builder, and the same-family, different-family, and
homogeneous Experiment 0 runners. This does not complete the required Agent-C
retraining or held-out co-evolution evaluation.

### Critical — The stored co-evolution driver is not a closed feedback loop

For every requested iteration, the driver rebuilds the buffer from the same
original Experiment 0 rows. It may invoke external updater commands, but it
does not load the resulting adapters and rescore a fresh batch before the next
iteration. Therefore, this checkout cannot generate a genuine Iter 0-to-30
trajectory.

Required repair:

1. score only the current training batch with the current adapters;
2. update the rolling buffer without reconstructing it from scratch;
3. build agent-specific batches;
4. update each adapter;
5. save adapter hashes and training logs;
6. rescore validation data with the updated adapters;
7. reserve test scoring for the final selected configuration.

### Critical — Cross-benchmark targets are not implemented

The prepared GPQA and BBH records use a constant difficulty value of 1.0.
Spearman correlation is undefined when the target has no variation. The
current repository also lacks prepared MATH, MedQA, ARC-Challenge,
TruthfulQA, and complete BBH evaluation pipelines corresponding to Table 1.

Recommended target order:

1. empirical pass rate across an independent reference-model panel;
2. Rasch/IRT difficulty if the response matrix supports stable estimation;
3. human or expert annotations when available;
4. the surface heuristic only as a secondary sensitivity target.

### High — Exact duplicate files can be mistaken for replications

Three exact duplicate SHA-256 groups exist among the stored and rescored
result files. In particular:

- `exp0_heterogeneous_mistral_d.jsonl` and
  `exp0_heterogeneous_mistral_d_n300.jsonl` are byte-identical;
- their two rescored counterparts are also byte-identical;
- the two homogeneous rescored JSONLs are both empty files.

These aliases must not be counted as separate runs or seeds.

### High — The homogeneous control is not yet comparable

The homogeneous outputs use a `per_role` schema, while the heterogeneous
outputs use `per_agent`. The new local pipeline normalizes both schemas and
uses the submitted maximum-entropy reconstruction when full option
probabilities are unavailable.

Canonical rescoring of the stored homogeneous files yields positive
correlations (`rho=0.286`, `n=109`; `rho=0.344`, `n=300`) against the surface
heuristic. These files do not match the submitted homogeneous protocol
(Llama-3.3-70B, `n=30`, three seeds), so they neither reproduce nor directly
contradict Table 2. They do show that the repository's larger homogeneous
outputs must not be presented as the submitted baseline. The exact `n=30`
artifact still needs to be recovered.

## Verified local saved-output analysis

The canonical scorer reproduces the saved revised disagreement values for all
stored heterogeneous rows to within `5e-5`. Bootstrap intervals use 1,000
question resamples and permutation tests use 10,000 target permutations.

| Stored sample | Score | n | Spearman rho | Bootstrap 95% CI | Permutation p |
|---|---|---:|---:|---:|---:|
| Same-family heterogeneous | Full submitted weights | 50 | 0.154 | [-0.134, 0.401] | 0.284 |
| Same-family heterogeneous | No correctness, paper weights | 50 | 0.207 | [-0.073, 0.457] | 0.143 |
| Same-family heterogeneous | Renormalized no correctness | 50 | 0.210 | [-0.078, 0.455] | 0.137 |
| Different-family heterogeneous | Full submitted weights | 300 | 0.003 | [-0.103, 0.120] | 0.960 |
| Different-family heterogeneous | No correctness, paper weights | 300 | -0.018 | [-0.127, 0.103] | 0.741 |

These are static, single stored samples evaluated against the submitted
surface heuristic. They do not reproduce Table 11's co-evolution endpoint and
do not resolve the reviewers' independent-difficulty concern.

The exploratory top-20% triage result on the different-family `n=300` sample
has enrichment 1.33 for the full score and 1.25 without correctness. Because
the positive class is defined by the same surface proxy under criticism, these
numbers validate the analysis code only and must not be used as rebuttal
evidence.

## Manuscript-to-code ambiguity: heuristic target in the buffer

Appendix B.8 says that examples with both high disagreement `D(q)` and high
difficulty `s(q)` are amplified by buffer sampling. However, Appendix B.6
defines sampling using disagreement, answer/confidence gaps, category, and
Agent-C calibration error. The checked-in driver likewise does not rank or
sample by `difficulty_score`.

The rebuttal should correct the B.8 sentence and state that the implemented
buffer does not optimize or select on `s(q)`. This removes direct target
circularity only if the repaired pipeline preserves that separation and is
evaluated on an untouched test set.

## Label-use inventory

| Stage | Gold-label use | Classification |
|---|---|---|
| Entropy, JS, confidence score components | No | Label-free |
| Correctness-diversity score component | Yes | Supervised |
| Agent-C hard-case routing | Yes | Supervised |
| Training-row `target_answer` | Yes | Supervised |
| Agent-C `target_confidence` | Yes | Supervised |
| Agent-R and Agent-D specialization | Yes | Supervised |
| Agent-C specialization and calibration | Yes | Supervised |
| Final correlation against pass rate or IRT | Usually requires reference correctness | Evaluation supervision |

The defensible framing is: the entropy/JS/confidence ranking can operate
without labels at inference, while specialization and the current co-evolution
procedure are supervised.

## What is safe to do locally

- Recompute revised disagreement from saved static outputs.
- Repair homogeneous-schema rescoring.
- Run the no-correctness score ablation.
- Run bootstrap and permutation tests on verified stored samples.
- Audit overlap, duplicate files, label use, and target variation.
- Compute triage metrics once a defensible target is available.

## What requires recovered artifacts or new GPU runs

- Table 3 reproduction.
- A strict held-out Agent-C result.
- Closed-loop co-evolution.
- Three-seed endpoint estimates.
- The 12-backbone by seven-benchmark study.
- Cross-benchmark transfer.
- Non-specialized co-evolution.

## Immediate execution order

1. Recover any external Kaggle notebooks, results, adapters, and logs.
2. Wire the verified split manifest into Agent-C training and every
   co-evolution/evaluation entry point.
3. Recover or rerun the submitted homogeneous `n=30` baseline.
4. Build pass-rate and IRT targets after recovering the reference-model matrix.
5. Decide which GPU experiments fit the rebuttal deadline.
6. Draft rebuttal language only from verified results.

## Supporting artifacts

- `repository_evidence_audit.ipynb`
- `REVIEW_EVIDENCE_MATRIX.md`
- `SPLIT_PROTOCOL.md`
- `split_guard.py`
- `artifacts/local_rescoring/component_ablation.csv`
- `artifacts/local_rescoring/surface_proxy_triage.csv`
- `splits/mmlu_pro_hard_split_manifest.csv`
- `splits/mmlu_pro_hard_split_summary.json`
- `artifacts/audit_summary.json`
- `artifacts/static_output_profile.csv`
- `artifacts/dataset_profile.csv`
- `artifacts/result_file_hash_groups.csv`
- `artifacts/agent_c_overlap.json`
- `artifacts/artifact_inventory.json`
