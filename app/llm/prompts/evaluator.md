Reference only — not loaded or versioned like support.md.

The Phase 2 evaluation judge (`app/evaluation/deepeval_metrics.py`,
`app/evaluation/ragas_metrics.py`) uses DeepEval's and Ragas's built-in
grading prompts for faithfulness, hallucination, context precision, and
context recall. Neither library exposes a simple override point for these
internal prompts, so there's nothing here to version — this file exists to
document that choice, not to configure it.
