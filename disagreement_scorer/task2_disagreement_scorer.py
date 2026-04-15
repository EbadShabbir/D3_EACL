"""
TASK 2 — Disagreement Scorer Module + 4 Unit Tests
Run in: VS Code / local
Install first: pip install sentence-transformers numpy scipy torch
"""

import json
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import deque
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine

# ── Load sentence encoder once (reused across all calls) ─────────────────────
print("Loading sentence encoder...")
ENCODER = SentenceTransformer("all-MiniLM-L6-v2")
print("Encoder loaded.\n")


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class AgentOutput:
    """Output from a single agent for one question."""
    agent_name: str        # "R", "D", or "C"
    answer:     str        # The answer text
    confidence: float      # Float in [0, 1]


@dataclass
class DisagreementResult:
    """Full result for one question."""
    question_id:    str
    question:       str
    agent_outputs:  List[AgentOutput]
    d_semantic:     float   # Semantic distance component
    d_confidence:   float   # Confidence variance component
    d_score:        float   # Final D(q) = 0.6 * semantic + 0.4 * confidence
    is_hard_case:   bool    # True if D(q) > threshold


# ── Core Disagreement Scorer ──────────────────────────────────────────────────

class DisagreementScorer:
    """
    Computes D(q) for a question given outputs from 3 agents.

    D(q) = 0.6 * D_semantic(q) + 0.4 * D_confidence(q)

    D_semantic:   mean pairwise cosine distance between answer embeddings
    D_confidence: variance of the three confidence scores
    """

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.encoder   = ENCODER

    def _embed(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts, returns (N, dim) array."""
        return self.encoder.encode(texts, convert_to_numpy=True)

    def _semantic_distance(self, answers: List[str]) -> float:
        """
        Mean pairwise cosine distance across the 3 agent answers.
        cosine distance = 1 - cosine similarity, range [0, 1].
        """
        embeddings = self._embed(answers)
        n = len(embeddings)
        distances = []
        for i in range(n):
            for j in range(i + 1, n):
                dist = cosine(embeddings[i], embeddings[j])
                distances.append(dist)
        return float(np.mean(distances))

    def _confidence_variance(self, confidences: List[float]) -> float:
        """
        Variance of confidence scores, normalized to [0, 1].
        Max variance for 3 values in [0,1] is 1/3 (e.g. 0, 0.5, 1).
        We normalize by dividing by max possible variance.
        """
        var = float(np.var(confidences))
        max_var = 1 / 3  # theoretical max for 3 values in [0,1]
        return min(var / max_var, 1.0)

    def score(
        self,
        question_id: str,
        question:    str,
        outputs:     List[AgentOutput],
    ) -> DisagreementResult:
        """
        Compute D(q) for one question given 3 agent outputs.
        """
        assert len(outputs) == 3, "Exactly 3 agent outputs required."

        answers     = [o.answer     for o in outputs]
        confidences = [o.confidence for o in outputs]

        d_semantic    = self._semantic_distance(answers)
        d_confidence  = self._confidence_variance(confidences)
        d_score       = round(0.6 * d_semantic + 0.4 * d_confidence, 4)
        is_hard_case  = d_score > self.threshold

        return DisagreementResult(
            question_id   = question_id,
            question      = question,
            agent_outputs = outputs,
            d_semantic    = round(d_semantic, 4),
            d_confidence  = round(d_confidence, 4),
            d_score       = d_score,
            is_hard_case  = is_hard_case,
        )

    def score_batch(
        self,
        questions: List[Dict],
        outputs_per_question: List[List[AgentOutput]],
    ) -> List[DisagreementResult]:
        """Score a batch of questions."""
        results = []
        for q, outputs in zip(questions, outputs_per_question):
            result = self.score(
                question_id = q["question_id"],
                question    = q["question"],
                outputs     = outputs,
            )
            results.append(result)
        return results


# ── Hard Case Buffer ──────────────────────────────────────────────────────────
# (Full implementation is Task 3 — this is a minimal version needed for tests)

class HardCaseBuffer:
    """
    Rolling FIFO buffer of hard cases. Max 500 entries.
    Used by the co-evolution loop in Task 10.
    """

    def __init__(self, max_size: int = 500):
        self.max_size = max_size
        self.buffer: deque = deque(maxlen=max_size)

    def add(self, result: DisagreementResult):
        if result.is_hard_case:
            self.buffer.append(result)

    def top_k(self, k: int = 200) -> List[DisagreementResult]:
        """Return top-k by D(q) score."""
        sorted_buf = sorted(self.buffer, key=lambda x: x.d_score, reverse=True)
        return sorted_buf[:k]

    def __len__(self):
        return len(self.buffer)


# ── 4 Unit Tests ─────────────────────────────────────────────────────────────

def run_unit_tests():
    scorer = DisagreementScorer(threshold=0.5)
    results = []

    print("=" * 60)
    print("RUNNING 4 UNIT TESTS")
    print("=" * 60)

    # ── TEST 1: Identical answers → D(q) < 0.1 ───────────────────────────────
    print("\nTest 1: Identical answers — expect D(q) < 0.1")
    identical_outputs = [
        AgentOutput("R", "The answer is Paris, the capital of France.", 0.9),
        AgentOutput("D", "The answer is Paris, the capital of France.", 0.9),
        AgentOutput("C", "The answer is Paris, the capital of France.", 0.9),
    ]
    r1 = scorer.score("t1", "What is the capital of France?", identical_outputs)
    status = "✅ PASS" if r1.d_score < 0.1 else "❌ FAIL"
    print(f"  D_semantic={r1.d_semantic}, D_confidence={r1.d_confidence}, D(q)={r1.d_score}")
    print(f"  Expected: < 0.1   →  {status}")
    results.append(("Test 1 — Identical answers", r1.d_score < 0.1))

    # ── TEST 2: Maximal disagreement → D(q) > 0.8 ────────────────────────────
    print("\nTest 2: Maximal disagreement — expect D(q) > 0.8")
    maximal_outputs = [
        AgentOutput("R", "The mitochondria produce ATP through oxidative phosphorylation using the electron transport chain.", 0.95),
        AgentOutput("D", "The French Revolution began in 1789 due to economic hardship and social inequality among the estates.", 0.90),
        AgentOutput("C", "Quantum entanglement allows particles to instantaneously affect each other regardless of the distance separating them.", 0.85),
    ]
    r2 = scorer.score("t2", "Completely unrelated topics question.", maximal_outputs)
    status = "✅ PASS" if r2.d_score > 0.8 else "❌ FAIL"
    print(f"  D_semantic={r2.d_semantic}, D_confidence={r2.d_confidence}, D(q)={r2.d_score}")
    print(f"  Expected: > 0.8   →  {status}")
    results.append(("Test 2 — Maximal disagreement", r2.d_score > 0.8))

    # ── TEST 3: Same answer, different confidences → 0.1 < D(q) < 0.4 ────────
    print("\nTest 3: Same answer, confidences 0.9 / 0.5 / 0.1 — expect 0.1 < D(q) < 0.4")
    conf_only_outputs = [
        AgentOutput("R", "The boiling point of water is 100 degrees Celsius at standard pressure.", 0.9),
        AgentOutput("D", "The boiling point of water is 100 degrees Celsius at standard pressure.", 0.5),
        AgentOutput("C", "The boiling point of water is 100 degrees Celsius at standard pressure.", 0.1),
    ]
    r3 = scorer.score("t3", "What is the boiling point of water?", conf_only_outputs)
    status = "✅ PASS" if 0.1 < r3.d_score < 0.4 else "❌ FAIL"
    print(f"  D_semantic={r3.d_semantic}, D_confidence={r3.d_confidence}, D(q)={r3.d_score}")
    print(f"  Expected: 0.1 < D(q) < 0.4   →  {status}")
    results.append(("Test 3 — Confidence-only disagreement", 0.1 < r3.d_score < 0.4))

    # ── TEST 4: Hard case flagging on MMLU-Pro sample ────────────────────────
    print("\nTest 4: Hard case flagging — top quartile of D(q) should overlap with hard questions")
    try:
        with open("D:\\Multi_Agent_Code\\Data_prepare_task1\\mmlu_pro_hard_sample_50.json") as f:
            hard_sample = json.load(f)

        # Simulate diverse agent outputs for known hard questions
        # (In reality agents would differ; here we simulate with varied answers)
        simulated_results = []
        for q in hard_sample[:20]:
            opts = q["options"]
            sim_outputs = [
                AgentOutput("R", opts[0], 0.4),
                AgentOutput("D", opts[2], 0.7),
                AgentOutput("C", opts[1], 0.3),
            ]
            res = scorer.score(q["question_id"], q["question"], sim_outputs)
            simulated_results.append((q["difficulty_score"], res.d_score))

        # Check: correlation between difficulty and D(q) should be positive
        difficulty_scores = [x[0] for x in simulated_results]
        d_scores          = [x[1] for x in simulated_results]

        from scipy.stats import spearmanr
        corr, pval = spearmanr(difficulty_scores, d_scores)

        # Hard cases (top quartile by D(q)) should align with high difficulty
        d_threshold = np.percentile(d_scores, 75)
        flagged_as_hard = [i for i, d in enumerate(d_scores) if d >= d_threshold]
        high_difficulty = [i for i, diff in enumerate(difficulty_scores) if diff >= np.percentile(difficulty_scores, 75)]
        overlap = len(set(flagged_as_hard) & set(high_difficulty))
        overlap_ratio = overlap / max(len(flagged_as_hard), 1)

        status = "✅ PASS" if overlap_ratio >= 0.3 else "❌ FAIL"
        print(f"  Spearman corr(difficulty, D(q)) = {corr:.3f}  (p={pval:.3f})")
        print(f"  Top-quartile overlap ratio: {overlap_ratio:.2f}")
        print(f"  Expected: overlap >= 0.3   →  {status}")
        results.append(("Test 4 — Hard case flagging", overlap_ratio >= 0.3))

    except FileNotFoundError:
        print("  ⚠️  mmlu_pro_hard_sample_50.json not found — run Task 1 first.")
        results.append(("Test 4 — Hard case flagging", False))

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("UNIT TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'✅' if ok else '❌'}  {name}")
    print(f"\n{passed}/{len(results)} tests passed.")

    if passed == len(results):
        print("\n✅ All tests passed. Safe to proceed to Task 3.")
    else:
        print("\n❌ Some tests failed. Do NOT proceed until all pass.")

    return passed == len(results)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    all_passed = run_unit_tests()

    # Quick demo: score one example question
    print("\n" + "=" * 60)
    print("DEMO — Score a single question")
    print("=" * 60)
    scorer = DisagreementScorer(threshold=0.5)
    demo_outputs = [
        AgentOutput("R", "The integral of x^2 is x^3/3 plus a constant.", 0.85),
        AgentOutput("D", "Using integration rules, the answer would be x^3 divided by 3.", 0.60),
        AgentOutput("C", "I am not certain but it might be related to polynomial integration.", 0.30),
    ]
    result = scorer.score("demo_1", "What is the integral of x squared?", demo_outputs)
    print(f"  D_semantic:   {result.d_semantic}")
    print(f"  D_confidence: {result.d_confidence}")
    print(f"  D(q):         {result.d_score}")
    print(f"  Hard case:    {result.is_hard_case}")