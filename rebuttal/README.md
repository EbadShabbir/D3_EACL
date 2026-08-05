# NeurIPS 2026 Rebuttal Task Board

Repository: `EbadShabbir/Multi_agent_neurips`

Current branch: `agent/organize-research-repository`

This workspace tracks the rebuttal for submission **10833**, *Disagreement, Diversity, and Difficulty in Multi-Agent Language Models*.

Use the stable task numbers below when assigning work, for example:

> Start Task 03.

> What is the status of Tasks 07 and 08?

> Draft the response using Tasks 16-18.

Operational guides:

- `A100_RUNBOOK.md` - numbered plan for the MBZUAI/CIAI A100 reruns.
- `SPLIT_PROTOCOL.md` - immutable split rules and current executable commands.

## Deadline

- Author, reviewer, and AC discussion ends: **August 3, 2026 (AoE)**
- NeurIPS notification: **September 24, 2026 (AoE)**
- Fallback ARR cycle submission: **October 12, 2026**

## Status legend

- `[ ]` Not started
- `[~]` In progress
- `[x]` Completed and verified
- `[!]` Blocked

## Current status

| ID | Status | Note |
|---|---|---|
| 01 | `[x]` | Current checkout inventoried; missing submitted-run artifacts are enumerated. |
| 02 | `[x]` | Reviewer concerns are mapped in `REVIEW_EVIDENCE_MATRIX.md`. |
| 03 | `[x]` | Audit confirms Agent-C/evaluation overlap and supervised label use. |
| 04 | `[!]` | Iteration 0-30 artifacts and update scripts are not present in the current checkout. |
| 05 | `[~]` | Submitted-PDF settings are mapped; actual submitted run config is still missing. |
| 06 | `[~]` | Manifest guards are wired into Agent-C, co-evolution, and core Experiment 0 runners; GPU reruns remain. |
| 07 | `[!]` | Requires the claimed multi-backbone response matrix or new model inference. |
| 09 | `[x]` | Gold-label use is classified by pipeline stage. |
| 10 | `[~]` | Static full/no-correctness rescoring is verified; co-evolved ablation is blocked. |
| 11 | `[!]` | Exploratory surface-proxy triage ran, but a defensible target is still unavailable. |

## Critical path

`Task 01 -> Task 03 -> Task 06 -> Tasks 07-11 -> Tasks 16-18 -> Tasks 19-20`

If Task 03 identifies train/test leakage, Task 06 and a clean rerun take precedence over every optional experiment.

## Task index

| ID | Task | Priority | Depends on | Expected output |
|---|---|---:|---|---|
| 01 | Repository and artifact inventory | Critical | Repository attachment | Reproducibility map |
| 02 | Review-to-claim evidence matrix | High | None | Reviewer concern matrix |
| 03 | Data-flow, label-use, and leakage audit | Critical | 01 | Audited data-flow diagram |
| 04 | Reproduce Table 3 | Critical | 01 | Verified Iter 0/30 results |
| 05 | Resolve configuration ambiguities | High | 01, 04 | Configuration reference sheet |
| 06 | Implement strict train/validation/test protocol | Critical | 03 | Held-out evaluation pipeline |
| 07 | Construct empirical model pass-rate difficulty | Critical | 01, 03 | Independent difficulty target |
| 08 | Estimate IRT/Rasch difficulty | High | 07 | IRT-based robustness result |
| 09 | Audit all gold-label dependence | Critical | 03 | Label-dependence inventory |
| 10 | Run label-free score and sampling ablations | Critical | 06, 09 | Label-free comparison table |
| 11 | Evaluate practical hard-case triage utility | High | 06, 07 | Top-k enrichment metrics |
| 12 | Run non-specialized co-evolution baseline | Medium | 04, 06 | Initialization ablation |
| 13 | Add and compare with EIP | High | 01, 07 | Citation and comparison |
| 14 | Narrow and clarify theoretical claims | High | 02, 03 | Defensible theory response |
| 15 | Define difficulty for every benchmark | Critical | 01, 07 | Benchmark proxy table |
| 16 | Draft response to Reviewer ph2X | Critical | 03-15 | Reviewer-specific rebuttal |
| 17 | Draft response to Reviewer txM8 | Critical | 03-15 | Reviewer-specific rebuttal |
| 18 | Draft response to Reviewer mEV6 | Critical | 03-15 | Reviewer-specific rebuttal |
| 19 | Numerical and consistency audit | Critical | 16-18 | Verified final responses |
| 20 | Submit responses and manage discussion | Critical | 19 | Submitted rebuttals |
| 21 | Prepare improved ARR version if needed | Later | NeurIPS decision | Revised manuscript |

## Detailed tasks

### Task 01 - Repository and artifact inventory

**Objective:** Identify the exact code, data, models, and outputs used for the submitted paper.

**Actions:**

- [x] Record the audited commit, branch, environment, entry points, and whether the submitted commit is identifiable.
- [x] Locate datasets and prepared benchmark subsets.
- [x] Locate or record the absence of model checkpoints, LoRA adapters, saved logits, predictions, and confidence scores.
- [x] Locate or record the absence of configuration files for every table and figure.
- [x] Locate or record the absence of logs for seeds 42, 1337, and 2024.
- [x] Map repository evidence to Tables 1, 2, 3, 11, and 18.
- [x] Record missing and non-reproducible artifacts.

**Done when:** A new researcher could identify the command, configuration, input, and output associated with every headline result.

---

### Task 02 - Review-to-claim evidence matrix

**Objective:** Convert the three reviews into an actionable evidence map.

**Actions:**

- [x] List every criticism and question from ph2X, txM8, and mEV6.
- [x] Link each concern to the relevant manuscript section, table, equation, or missing experiment.
- [x] Classify each item as a misunderstanding, missing clarification, valid limitation, or required experiment.
- [x] Identify concerns shared by multiple reviewers.
- [x] Mark which claims should be defended, narrowed, or withdrawn.

**Done when:** Every reviewer point has a planned answer supported by text, code, or a new result.

---

### Task 03 - Data-flow, label-use, and leakage audit

**Objective:** Determine whether training, buffer construction, hyperparameter selection, and final evaluation are properly separated.

**Actions:**

- [x] Trace the implemented path from source data through filtering, scoring, buffering, and evaluation.
- [x] Identify whether the same questions are used for specialization and final correlation reporting.
- [x] Identify where the heuristic target `s(q)` is read or used.
- [x] Identify every implemented use of gold answers and correctness.
- [x] Check whether repository evidence establishes independent hyperparameter selection.
- [x] Check for duplicate or overlapping questions across available splits and outputs.
- [x] Record which parts of the claimed Table 3 protocol are and are not present.

**Done when:** We can state precisely whether there is leakage or adaptivity bias and show evidence from the implementation.

---

### Task 04 - Reproduce Table 3

**Objective:** Reproduce the main co-evolution result before adding new experiments.

**Actions:**

- [ ] Reproduce the different-family, `n=300`, Iter 0 result.
- [ ] Reproduce the Iter 30 result with diversity regularization.
- [ ] Reproduce the no-regularizer endpoint.
- [ ] Reproduce per-agent accuracy, ECE, and mean pairwise JS.
- [ ] Verify results across all three stated seeds.
- [ ] Compare raw outputs with the submitted table.

**Done when:** Each Table 3 number is regenerated or any discrepancy is documented.

---

### Task 05 - Resolve configuration ambiguities

**Objective:** Produce one authoritative description of the experimental setup.

**Actions:**

- [~] Specify Agent C's submitted-run training dataset, validation data, objective, and temperature-scaling split.
- [x] Define “static disagreement” as disagreement before co-evolution.
- [x] State that Table 3 uses the different-family, `n=300` configuration.
- [x] Explain that Table 3 Iter 0 matches the corresponding Table 2 row.
- [x] Explain why Table 1 is not the appropriate comparison because it aggregates a broader design space.
- [x] Extract the submitted prompts, decoding, seeds, compute, batch size, sequence length, and LoRA claims.
- [~] Reconcile in-domain training, per-benchmark training, and zero-shot transfer with raw artifacts.

**Done when:** All experimental settings can be described without contradictions.

---

### Task 06 - Implement strict train/validation/test protocol

**Objective:** Eliminate adaptivity bias and provide a genuinely held-out final evaluation.

**Actions:**

- [x] Create a deterministic, stratified train/validation/test split.
- [x] Make the checked-in co-evolution entry point accept only training questions.
- [~] Use only validation questions for weights and hyperparameter selection.
- [~] Default all core evaluation runners to validation and require an explicit test request.
- [x] Check category balance and difficulty distributions across splits.
- [ ] Run Iter 0 and Iter 30 evaluation on the untouched test set.
- [x] Save split manifests and hashes for reproducibility.

Implementation and cloud commands: `SPLIT_PROTOCOL.md`.

**Done when:** The final correlation and triage results are computed once on an untouched test set.

---

### Task 07 - Construct empirical model pass-rate difficulty

**Objective:** Replace or validate the surface-feature heuristic with an independently grounded difficulty target.

**Proposed definition:**

```text
d_pass(q) = 1 - mean correctness across the reference model panel
```

**Actions:**

- [ ] Build a question-by-model correctness matrix from the available backbone predictions.
- [ ] Exclude the evaluated three-agent outputs from the reference panel where necessary.
- [ ] Require sufficient model coverage per question.
- [ ] Calculate empirical failure rate and uncertainty.
- [ ] Correlate the original heuristic `s(q)` with pass-rate difficulty.
- [ ] Evaluate static and co-evolved disagreement against pass-rate difficulty.
- [ ] Report per-category results.

**Done when:** The main conclusion is tested against model behavior rather than question formatting alone.

---

### Task 08 - Estimate IRT/Rasch difficulty

**Objective:** Add an established item-difficulty estimate using the model response matrix.

**Actions:**

- [ ] Check whether the response matrix has enough models and observations for stable estimation.
- [ ] Fit a one-parameter Rasch/IRT model.
- [ ] Inspect convergence and uncertainty.
- [ ] Compare IRT difficulty with pass rate and the original heuristic.
- [ ] Evaluate disagreement against IRT difficulty.
- [ ] Treat this result as exploratory if the model panel is too small.

**Done when:** We have either a valid IRT robustness result or a documented reason it is statistically unreliable.

---

### Task 09 - Audit all gold-label dependence

**Objective:** Separate label-free inference from supervised adaptation.

**Actions:**

- [x] List every use of the gold answer in `D_corr`.
- [x] List every use of correctness in Agent C sampling.
- [x] List every supervised task loss visible in specialization and co-evolution inputs.
- [x] Determine whether the difficulty target is used directly by the checked-in buffer sampler.
- [x] Classify each stage as label-free, weakly supervised, or fully supervised.
- [x] Record defensible rebuttal wording that does not describe the full method as label-free.

**Done when:** The rebuttal can accurately state which components require labels and under what deployment conditions.

---

### Task 10 - Run label-free score and sampling ablations

**Objective:** Quantify performance when gold-label-dependent components are removed.

**Actions:**

- [ ] Reproduce the existing “no correctness term” result from Table 11.
- [x] Evaluate saved static outputs with the paper's no-correctness weights.
- [x] Evaluate a renormalized score using entropy, JS divergence, and confidence variance only.
- [ ] Remove correctness-based Agent C sampling.
- [ ] Replace correctness-based selection with calibration disagreement or confidence inconsistency if defensible.
- [ ] Evaluate static and co-evolved variants under the strict held-out protocol.
- [~] Compare full supervised, label-free-score-only, and fully label-free-ranking variants.

**Done when:** We can support a precise deployment claim with an explicit performance tradeoff.

---

### Task 11 - Evaluate practical hard-case triage utility

**Objective:** Show whether a modest Spearman correlation is operationally useful.

**Actions:**

- [ ] Define truly hard cases using held-out pass-rate or IRT difficulty.
- [~] Validate precision and recall code at the top 20% using the surface proxy only.
- [~] Validate hard-case enrichment code using the surface proxy only.
- [ ] Report AUROC or average precision if the binary hard-case definition is stable.
- [ ] Compare against random, entropy-only, confidence-only, self-consistency, and single-agent uncertainty.
- [ ] Include uncertainty intervals.

**Done when:** The rebuttal can quantify what `rho approximately 0.20` means for an actual triage workload.

---

### Task 12 - Run non-specialized co-evolution baseline

**Objective:** Answer whether co-evolution works without initial agent specialization.

**Actions:**

- [ ] Initialize agents from the non-specialized baseline.
- [ ] Apply the same co-evolution budget and split protocol.
- [ ] Measure Iter 0 and Iter 30 disagreement correlation, accuracy, ECE, and JS.
- [ ] Compare against specialized initialization.
- [ ] State whether specialization is necessary, helpful, or replaceable by co-evolution.

**Done when:** Reviewer txM8's initialization question has a direct experimental answer.

---

### Task 13 - Add and compare with EIP

**Objective:** Correct the related-work omission and position the contribution against EIP.

**Reference:**

Hu et al. (2026), *EIP: Weighted Ranking of LLMs by Quantifying Question Difficulty*, ICLR 2026.

**Actions:**

- [ ] Read and cite EIP accurately.
- [ ] Compare objectives, required supervision, difficulty definitions, and validation strategies.
- [ ] Identify whether EIP code or outputs allow a direct baseline.
- [ ] Run a comparison if it is feasible and methodologically fair.
- [ ] Otherwise provide a concise conceptual comparison without overstating novelty.

**Done when:** The rebuttal acknowledges EIP and clearly distinguishes the present contribution.

---

### Task 14 - Narrow and clarify theoretical claims

**Objective:** Make the theoretical contribution defensible.

**Actions:**

- [ ] Recheck all assumptions and proof steps for Theorems 1-3.
- [ ] Determine whether the stated lower bound follows from the current assumptions.
- [ ] Determine whether the stated upper bound is meaningful for Spearman correlation.
- [ ] Remove or weaken claims not justified by the analysis.
- [ ] Present the theory primarily as motivation for diversity preservation unless stronger claims are proven.
- [ ] Explicitly state that diversity alone does not imply alignment with true difficulty.

**Done when:** No rebuttal statement relies on a theorem stronger than its assumptions support.

---

### Task 15 - Define difficulty for every benchmark

**Objective:** Answer how the target is constructed outside MMLU-Pro.

**Actions:**

- [ ] Record the exact proxy used for GPQA, MATH, MedQA, ARC-Challenge, BBH, and TruthfulQA.
- [ ] Check whether formulas or feature ranges differ by benchmark.
- [ ] Check whether category boosts are meaningful outside MMLU-Pro.
- [ ] Recalculate results using pass-rate difficulty where possible.
- [ ] Run sensitivity analyses across alternative target constructions.
- [ ] Create a concise benchmark-by-benchmark proxy table.

**Done when:** Every Table 1 benchmark has a transparent, reproducible target definition.

---

### Task 16 - Draft response to Reviewer ph2X

**Required topics:**

- [ ] Strict train/validation/test separation.
- [ ] Difficulty target beyond MMLU-Pro.
- [ ] Sensitivity to proxy construction.
- [ ] Gold-label dependence and deployment scope.
- [ ] Theory limitations.
- [ ] Practical interpretation of the effect size.
- [ ] Explicitly acknowledge remaining limitations.

**Done when:** Every question and weakness is answered with verified evidence or a candid limitation.

---

### Task 17 - Draft response to Reviewer txM8

**Required topics:**

- [ ] Alternative difficulty validation.
- [ ] EIP citation and positioning.
- [ ] Agent C dataset and training details.
- [ ] Formal definition of static disagreement.
- [ ] Table 3 setting and Iter 0 explanation.
- [ ] Component contribution ablation in Appendix E.6, Table 11.
- [ ] Non-specialized initialization experiment or limitation.

**Done when:** Every question is answered directly, including manuscript locations and new results.

---

### Task 18 - Draft response to Reviewer mEV6

**Required topics:**

- [ ] Pass-rate, IRT, human, or semantic difficulty validation.
- [ ] Circularity and target-hacking concern.
- [ ] Whether `s(q)` enters buffer sampling or training.
- [ ] Held-out evaluation protocol.
- [ ] Location and content of Appendix D.
- [ ] Commitment to improve figure readability and manuscript presentation.

**Done when:** The response resolves factual uncertainty and does not dismiss the central validity concern.

---

### Task 19 - Numerical and consistency audit

**Objective:** Ensure the rebuttal contains no unsupported or contradictory claims.

**Actions:**

- [ ] Trace every number to a saved output.
- [ ] Verify means, standard deviations, confidence intervals, and p-values.
- [ ] Check table-setting names and sample sizes.
- [ ] Check that all three responses use consistent terminology.
- [ ] Remove claims that cannot be verified before the deadline.
- [ ] Check anonymity and remove prohibited identifying information or links.
- [ ] Keep each per-review response within the NeurIPS character limit.

**Done when:** Two independent passes find no numerical, methodological, or policy errors.

---

### Task 20 - Submit responses and manage discussion

**Objective:** Submit the rebuttals and respond constructively during the discussion period.

**Actions:**

- [ ] Submit one focused response under each review.
- [ ] Lead with new evidence and major clarifications.
- [ ] Avoid asking reviewers directly for a higher score.
- [ ] Monitor reviewer and AC questions.
- [ ] Respond promptly with concise, verified answers.
- [ ] Preserve a final copy of every submitted message.

**Done when:** All three responses are submitted and all follow-up questions before the deadline are resolved.

---

### Task 21 - Prepare improved ARR version if needed

**Objective:** Convert the rebuttal work into a substantially stronger paper if NeurIPS rejects it.

**Actions:**

- [ ] Incorporate the strict held-out protocol into the paper.
- [ ] Replace the primary heuristic target with a validated target.
- [ ] Make the label-free variant central and clearly scope supervised co-evolution.
- [ ] Revise the theoretical section.
- [ ] Add EIP and other missing related work.
- [ ] Improve figure legibility and remove duplicated labels.
- [ ] Convert to the ACL long-paper format and page limit.
- [ ] Prepare for the October 12, 2026 ARR cycle.

**Done when:** The revised manuscript directly addresses every NeurIPS reviewer concern rather than merely appending rebuttal text.

## Evidence rules

1. Do not place a new number in a rebuttal unless it can be traced to a saved output.
2. Do not describe the full method as label-free unless both scoring and adaptation avoid gold labels.
3. Do not claim held-out generalization unless the evaluation questions were untouched by training, buffering, and tuning.
4. Distinguish model pass-rate difficulty, IRT difficulty, human difficulty, and the original surface-feature heuristic.
5. Present disagreement as a triage signal unless stronger validation supports a broader claim.
6. If an experiment cannot finish reliably before the deadline, state the limitation instead of reporting a preliminary or selectively chosen result.
