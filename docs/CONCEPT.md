# The idea: for LLMs you need a score, and the score needs checking too

## The problem

With ordinary code, a failure usually raises an exception. A tracing tool records it, marks the span `ERROR`, and you find it.

An LLM call can fail without raising anything. Ask a model a question its context cannot answer. It may invent an answer, or it may say it doesn't know. Both calls return normally, both spans look the same, and the trace status says "success". The failure is in the content of the reply, and tracing alone does not read content.

## What a trace gives you, and what it does not

| Situation | What the trace shows |
|---|---|
| A function raises | The failing span, the message and the input. Not where a bad value came from. |
| An exception is caught and swallowed | The error is still recorded on the span that raised it. Parent spans look clean, so you only see it inside the span tree. |
| A model call returns a bad or missing answer | Nothing unusual. Level is `DEFAULT`. You have to read the content. |

These come from `demo.py` and `llm_demo.py`.

## Idea 1: attach a score

A **score** is a judgement attached to a trace after the fact. Once replies carry a score, "read every reply" becomes "filter on a value".

## Idea 2: check the score

A score is only useful if it is right, and a scorer can be wrong in two directions:

- **False alarm.** It flags a reply that was fine. Seen in a real run: the model said "I can't give you one answer" and the regex called it a confident number.
- **Missed failure.** It passes a reply that was bad. Seen in the audit: "I don't know for sure, but it's probably 30 days" is scored as a decline, though the model gave a number.

So a score is a pointer to something to read. It does not replace reading. `audit.py` is the habit: hand-label a set of replies, run the scorer on them, and look at where they disagree.

## The Silent-Failure Detector

`detector.py` asks one question: how many days do I have to return an item? It asks under three contexts.

| Case | Context | What a trustworthy reply does |
|---|---|---|
| `good` | Policy states the return window | Gives the number |
| `missing` | Policy has no return window | Says it doesn't know |
| `conflicting` | Policy states two different windows | Says it can't tell, or flags the conflict |

Each reply gets two scores on its Langfuse trace:

- `answer_kind` (categorical): `gave_number`, `admitted_ignorance` or `other`, from a regex in `checks.py`.
- `silent_failure` (0 or 1): 1 when the context could not support a number and the reply gave one anyway.

In the Langfuse UI, filter on `silent_failure = 1` to find replies that returned normally and looked fine.

The scorer is a plain regex on purpose. It is cheap, deterministic and easy to read, so its mistakes are easy to see. An LLM judge would hide them behind a second model that also needs checking.

## Results

**Detector run** (3 cases x 3 repeats, one model, one question):

| case | expected | admitted_ignorance | gave_number | other | silent failures (as scored) |
|---|---|---|---|---|---|
| good | gave_number | 0 | 3 | 0 | 0/3 |
| missing | admitted_ignorance | 3 | 0 | 0 | 0/3 |
| conflicting | admitted_ignorance | 2 | 1 | 0 | 1/3 |

The one flagged reply was the false alarm above. Read by a person, there were 0 real silent failures in this run.

**Scorer audit** (`python audit.py`): the regex agrees with a person on 6 of 12 hand-written replies. Most of those replies were written to fool it, so this is not an error rate for real output. It lists ways the check can fail:

- Wording it does not know ("Sorry, I can't help with that" scores `other`).
- Numbers that are not `N days` ("two weeks", "30-day", "a month").
- A decline followed by a guess, which it scores as a decline.

Replies scored `other` are never flagged, so a miss in either direction is silent.

## Limits

- One model, one question. Do not read the results as a general claim about LLMs.
- Headless Claude Code adds its own system prompt, so these are not raw model calls, and input token counts in the traces are unreliable.
- The regex is a starting point, not a judge.
- In my run the model never gave a confident wrong answer in the `missing` or `conflicting` cases. That harder failure is untested.

## Where to go next

Missing `flush()`, async calls, Langfuse being unreachable, a larger hand-labelled reply set, and an LLM judge that is itself audited the same way.
