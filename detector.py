"""Silent-Failure Detector.

Asks one question under good, missing and conflicting context, scores each reply
with a plain string check, and attaches the score to the Langfuse trace.

    python detector.py --repeats 3
"""
import argparse
from collections import Counter

from dotenv import load_dotenv

load_dotenv()

from langfuse import get_client, observe

from checks import classify, is_silent_failure
from llm_demo import POLICY_BROKEN, POLICY_FULL, QUESTION, ask_claude

# Same policy with two contradicting return windows.
POLICY_CONFLICT = """Shop policy:
- Standard shipping takes 3-5 business days.
- Items can be returned within 30 days of delivery.
- Items can be returned within 14 days of delivery.
- Gift cards are not refundable."""

# case name -> (context, what a trustworthy reply does)
CASES = {
    "good": (POLICY_FULL, "gave_number"),
    "missing": (POLICY_BROKEN, "admitted_ignorance"),
    "conflicting": (POLICY_CONFLICT, "admitted_ignorance"),
}


@observe()
def run_case(case, repeat):
    context, expected = CASES[case]
    reply = ask_claude(context, QUESTION)
    kind = classify(reply)
    silent = is_silent_failure(kind, expected)
    client = get_client()
    client.update_current_trace(name=f"detector:{case}", metadata={"case": case, "repeat": repeat})
    client.score_current_trace(name="answer_kind", value=kind, data_type="CATEGORICAL")
    client.score_current_trace(name="silent_failure", value=1.0 if silent else 0.0, data_type="NUMERIC")
    return kind, silent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    counts = {case: Counter() for case in CASES}
    silent_counts = Counter()
    try:
        for case in CASES:
            for i in range(args.repeats):
                kind, silent = run_case(case, i)
                counts[case][kind] += 1
                silent_counts[case] += int(silent)
                print(f"{case} #{i + 1}: {kind}{'  <-- silent failure' if silent else ''}")
    finally:
        get_client().flush()

    print("\n| case | expected | admitted_ignorance | gave_number | other | silent failures |")
    print("|---|---|---|---|---|---|")
    for case, (_, expected) in CASES.items():
        c = counts[case]
        print(
            f"| {case} | {expected} | {c['admitted_ignorance']} | {c['gave_number']} "
            f"| {c['other']} | {silent_counts[case]}/{args.repeats} |"
        )


if __name__ == "__main__":
    main()
