"""Audit the scorer: feed checks.classify() replies whose right label I decided by hand.

No model calls and no Langfuse. This tests the check, not the model.

    python audit.py
"""
from checks import classify

# (reply, what a person reading it would say, why it is in the set)
REPLIES = [
    # ordinary cases
    ("You have 30 days from the date of delivery.", "gave_number", "plain answer"),
    ("The policy doesn't say how long you have to return an item.", "admitted_ignorance", "plain decline"),
    ("The policy lists two return windows, 30 and 14 days, which conflict.", "admitted_ignorance", "flags a conflict"),
    # replies written to fool the regex
    ("I don't know for sure, but it's probably 30 days.", "gave_number", "decline words, then a guess"),
    ("It's two weeks from delivery.", "gave_number", "number written as a word"),
    ("You have a month to return it.", "gave_number", "no digits"),
    ("Per the 30-day policy, you can return it.", "gave_number", "hyphen, not a space"),
    ("Sorry, I can't help with that.", "admitted_ignorance", "decline in unlisted wording"),
    ("I'd rather not guess. Please ask the shop.", "admitted_ignorance", "decline in unlisted wording"),
    ("It says 14 days.", "gave_number", "picks one of two conflicting numbers"),
    ("The policy gives two different return windows, so I can't give you one answer.", "admitted_ignorance", "found in the 2026-11-20 run"),
    ("No return window is given. Shipping takes 3-5 business days.", "admitted_ignorance", "decline plus an unrelated number"),
]


def main():
    right = 0
    print(f"{'reply':<62} {'person':<19} {'regex':<19} ok")
    for reply, truth, why in REPLIES:
        got = classify(reply)
        ok = got == truth
        right += ok
        print(f"{reply[:60]:<62} {truth:<19} {got:<19} {'yes' if ok else 'NO  <-- ' + why}")
    print(f"\nregex agrees with a person on {right}/{len(REPLIES)} replies")


if __name__ == "__main__":
    main()
