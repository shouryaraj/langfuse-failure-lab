# For LLMs you need a score, and the score needs checking too

I wanted to know whether tracing can explain a failed execution. I started with a Python function that fails on purpose and worked up to an LLM call that fails without raising anything. The answer changed along the way.

Code and results: https://github.com/shouryaraj/langfuse-failure-lab

## What a trace gives you

A **trace** is the record of one run. A **span** is one timed step inside it, and spans nest, so a trace is a tree of who called whom. Each span can carry its inputs and outputs, which a plain traceback lacks.

**A function that raises.** `validate_quantity` raised `ValueError: quantity must be > 0`. The trace showed the failing span, the message and the input in one view. It did not show where the bad `0` came from. It shows where a bad value flows, not where it entered.

**The same error, swallowed.** I wrapped the call in `try/except` and returned `None`. The program exited cleanly, but the error stayed on the span that raised it. Parent spans looked fine, so the failure is only visible inside the span tree. A view that shows only the top-level status would report success.

## Where it stops: a model call that raises nothing

I asked a shop-policy question through headless Claude Code, once with the return-window line in the policy and once without. Both calls returned normally and both spans were `DEFAULT`. The two traces had the same shape and differed only in content.

With an LLM, a bad or missing answer is not an error, so the span level says little. You have to read the content or score it.

## Scoring it: the Silent-Failure Detector

A **score** is a judgement attached to a trace after the fact. `detector.py` asks the same question under good, missing and conflicting context (the conflicting policy lists both 30 and 14 days). A regex labels each reply `gave_number`, `admitted_ignorance` or `other`. A second score, `silent_failure`, is 1 when the context could not support a number and the reply gave one anyway. Filter on `silent_failure = 1` and you find replies that looked fine.

I ran 3 cases x 3 repeats:

| case | expected | admitted_ignorance | gave_number | other | silent failures (as scored) |
|---|---|---|---|---|---|
| good | gave_number | 0 | 3 | 0 | 0/3 |
| missing | admitted_ignorance | 3 | 0 | 0 | 0/3 |
| conflicting | admitted_ignorance | 2 | 1 | 0 | 1/3 |

## Checking the score

The one flagged reply was not a silent failure. It read: "The policy gives two different return windows, so I can't give you one answer." It declines. My regex did not know that wording, so it called the reply a confident number. I only caught this by reading the reply.

So I audited the scorer. `audit.py` runs it on 12 replies I labelled by hand, many written to fool it. It agreed with me on 6. It fails in two directions:

- **False alarm:** the reply above.
- **Missed failure:** "I don't know for sure, but it's probably 30 days" is scored as a decline, though it gives a number.

It also misses wording it doesn't know ("Sorry, I can't help with that") and numbers that are not `N days` ("two weeks", "30-day"). Replies scored `other` are never flagged, so those misses are silent too.

## What I took from it

1. A trace gives the call tree, the inputs and the error, even when the code hides the exception.
2. For LLM calls the span level is a weak signal. Failure needs a score or a read.
3. A score is a pointer, not a verdict. Audit it against replies a person has read, in both directions.

## Limits

One model and one question, so this is not a general claim about LLMs. The check is a regex, not a judge. Headless Claude Code adds its own system prompt, so these are not raw model calls and the input token counts are unreliable. The model never gave a confident wrong answer in my runs, so that harder case is untested.

## Run it

See the repo `README.md`. The offline tests and the audit need no keys: `pytest` and `python audit.py`. For the full concept and results, see `docs/CONCEPT.md`.
