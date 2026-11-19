# Terminology

There is no single standard name for this approach. It combines a few established ideas.

| What we do | Technical term |
|---|---|
| Delete or contradict a line in the context on purpose | Fault injection (controlled context perturbation) |
| Ask a question the context cannot answer, expect a decline | Abstention testing, part of groundedness (faithfulness) checking |
| A confident answer the context did not support | Ungrounded generation (hallucination) |
| The `expected` value each case carries | Ground truth, or test oracle |
| A regex labels each reply | Rule-based evaluator, as opposed to an LLM-as-judge |
| Scores attached to a trace | Trace-level scoring, or online evaluation |
| Run each case several times | Repeated sampling (LLM output varies) |
| `audit.py`: check the scorer against hand-labelled replies | Meta-evaluation ("evaluating the evaluator") on a golden set |
| False alarm, missed failure | False positive, false negative (precision, recall) |

**In one phrase:** a fault-injection eval with a rule-based scorer, plus meta-evaluation of the scorer.

## Cautions

- `silent_failure` is this project's own name, not a standard term.
- `audit.py` counts agreement on 12 replies. That is too few for real precision and recall.

## To read more

Search: "RAG groundedness evaluation", "abstention in LLMs", "LLM evaluator meta-evaluation".
