# NeurIPS Review-to-Evidence Matrix

Submission 10833: *Disagreement, Diversity, and Difficulty in Multi-Agent Language Models*

Audit date: 2026-07-27

This matrix separates points that can be answered by clarification from points
that require new evidence. A rebuttal should not cite a submitted table as
independently verified unless its raw outputs are available.

## Shared concerns and response policy

| Concern | Reviewers | Classification | Current evidence | Response policy |
|---|---|---|---|---|
| Surface-feature difficulty proxy is not validated | ph2X, txM8, mEV6 | Valid limitation; required experiment | Appendix B.1 defines the heuristic. The repository has no human, pass-rate, or IRT target. GPQA and BBH prepared targets are constant. | Concede. Prioritize independent model pass rate; add IRT only if the response matrix is large enough. Narrow claims if unavailable. |
| Gold labels are used | ph2X | Valid limitation | `D_correctness`, Agent-C routing, target answers, and specialization/co-evolution inputs use correctness. | State that only entropy/JS/confidence scoring is label-free at inference. Describe the full current pipeline as supervised. |
| Split/adaptivity bias is unclear | ph2X | Valid concern confirmed in current checkout | 240/300 static evaluation rows fall in Agent-C's checked-in training/validation partition. No submitted split manifest is present. | Do not claim the stored result is held out. Use the new immutable 2,416/300/300 manifest and rerun Agent C before presenting a repaired result. |
| Theory is stronger than the evidence supports | ph2X | Valid limitation | Theorems rely on assumptions not empirically established by the stored artifacts. | Narrow to design intuition and empirical motivation; avoid claiming a general disagreement-difficulty guarantee. |
| Correlation is modest; utility is unclear | ph2X | Valid limitation; required analysis | Saved static results are weak. Independent hard-case labels are unavailable. | Report top-k enrichment only after constructing pass-rate/IRT difficulty; frame the method as triage, not a reliable difficulty oracle. |
| Training/evaluation details are hard to reproduce | ph2X, txM8, mEV6 | Valid concern | Appendix D states hardware, decoding, and seeds, but the current checkout lacks submitted configs, seed logs, adapters, and trajectories. | Give a concise authoritative configuration table, explicitly distinguishing manuscript claims from recovered artifacts. |

## Reviewer ph2X

| Review point | Manuscript location | Evidence/status | Planned answer |
|---|---|---|---|
| Clarify train/validation/test separation | Sections 4-5; Appendix B.5, B.6, D | Current checkout contradicts a held-out Agent-C claim; strict split manifest is now generated but not yet wired into training. | Acknowledge the issue, describe the repaired protocol, and give new numbers only after retraining/evaluating on the untouched test set. |
| Explain difficulty on benchmarks beyond MMLU-Pro | Table 1; Section 4; Table 18 | No raw 12-by-7 matrix. Current GPQA and BBH preparation uses constant `difficulty_score=1.0`; other benchmark pipelines are absent. | Recover the original target definitions and artifacts. Otherwise withdraw cross-benchmark quantitative claims from the rebuttal rather than extrapolating. |
| Acknowledge label dependence | Eq. 7; Appendix B.6; Table 11 | Confirmed. The saved-output pipeline can recompute a label-free score, but cannot reproduce co-evolved Table 11. | Distinguish inference-time label-free scoring from supervised specialization and routing. Present static ablation only as supplementary unless endpoint artifacts are recovered. |
| Address limited theory | Section 3 | No repository artifact validates the stated bound or fixed-point assumptions. | Recast the theory as intuition and explicitly delimit its assumptions. |
| Address modest effect | Tables 2-3; Table 10 | Table 2 stored samples are reproducible; Table 3 is not. | Report uncertainty and operational top-k metrics against an independent target; avoid "reliable signal" language. |

## Reviewer txM8

| Review point | Manuscript location | Evidence/status | Planned answer |
|---|---|---|---|
| Add EIP [Hu et al., 2026] | Related Work | Missing from the submitted references. | Add the citation, explain the methodological difference, and compare against EIP's validated difficulty signal if code/data access permits. |
| Specify Agent-C dataset | Section 2.2; Appendix B.2/B.10 | Checked-in code trains and temperature-scales on partitions of MMLU-Pro; 240/300 evaluation rows overlap. The submitted run metadata is absent. | State exactly what the current code does and rerun on the strict manifest. Do not assert a different submitted dataset without its run metadata. |
| Define "static disagreement" | Section 5.1/Table 2 | Clarification available. | Define it as disagreement computed from specialized agents before any co-evolution update (Iter 0). |
| Specify Table 3 setting and explain Iter 0 vs Table 1 | Tables 1-3 | Table 3 is the different-family MMLU-Pro `n=300` run. Its Iter 0 `rho=0.003` matches Table 2. Table 1 summarizes a broader 12-backbone/7-benchmark design space. | Answer directly; use Table 2, not Table 1, as the matching baseline. Also clarify how Table 1 cells were aggregated once artifacts are recovered. |
| Show component-wise ablation | Table 11 | The submitted appendix already reports entropy-only, JS-only, confidence-only, correctness-only, mixtures, and no-correctness. Raw endpoint artifacts are missing. | Point explicitly to Table 11 and summarize the relevant rows, while avoiding a new reproducibility claim. |
| Start co-evolution without specialization | Not reported | Required GPU experiment; no implementation/result present. | Run only after the held-out pipeline works. If compute is limited, mark as future work and do not imply it was tested. |

## Reviewer mEV6

| Review point | Manuscript location | Evidence/status | Planned answer |
|---|---|---|---|
| Surface proxy may fail across categories | Appendix B.1; Table 17 | Valid and shared by all reviewers. No independent target exists in the checkout. | Replace/validate with pass-rate difficulty and report per-category uncertainty. |
| The model may hack the heuristic target through the buffer | Appendix B.6/B.8 | Important manuscript ambiguity: B.8 says high `D(q)` and high `s(q)` are amplified, while B.6 equations and the checked-in driver rank by disagreement and agent-specific behavior, not `s(q)`. | Correct B.8. State that the implemented sampler does not optimize or select on `s(q)`; then verify this property in the repaired pipeline. |
| Put the target definition in the main paper | Eq. 12 in Appendix B.1 | Clarification/edit required. | Move a compact definition and its limitations into the main method/evaluation section. |
| Missing prompts, decoding, seeds, and compute | Appendix D | Some details are present: greedy option-token scoring, seeds 42/1337/2024, single T4 16 GB, about 14 h/seed. Prompts and the actual unified run config are not recoverable from the checkout. | Quote the available settings succinctly and supply exact commands/config only after recovering the original run bundle. |
| Figures are too small | Main and appendix figures | Presentation issue. | Enlarge text and simplify multi-panel figures in the revision; rebuttal space should focus on technical concerns. |

## Claim decisions

### Defend with clarification

- "Static disagreement" means pre-co-evolution disagreement (Iter 0).
- Table 3 uses the different-family, MMLU-Pro, `n=300` configuration.
- Table 3 Iter 0 matches the corresponding Table 2 row; Table 1 is not the
  corresponding single-run baseline.
- Appendix Table 11 already contains component-wise and no-correctness rows.

### Narrow

- Replace "reliable difficulty signal" with "weak triage signal" unless
  independent-target utility results are obtained.
- Treat the theoretical results as conditional motivation, not a general
  guarantee.
- Describe entropy/JS/confidence scoring as label-free at inference, while
  describing specialization and current routing as supervised.

### Withdraw unless artifacts are recovered or experiments are rerun

- The Table 3 Iter 30 and no-regularizer endpoints.
- Three-seed means/standard deviations not backed by per-seed outputs.
- The 12-backbone by seven-benchmark grid and cross-benchmark transfer.
- Claims of a held-out Agent-C evaluation under the current split.
- Any GPQA or BBH correlation computed against the current constant target.
