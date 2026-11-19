"""Simple string checks that classify a model reply. No LLM judge on purpose."""
import re

IGNORANCE = re.compile(
    r"(don't|do not|doesn't|does not|didn't|did not) (have|know|say|specify|mention|include|list)"
    r"|not (specified|stated|mentioned|listed|included|provided)"
    r"|no (return|information|mention)"
    r"|(can't|cannot|unable to) (find|confirm|tell|determine)"
    r"|(conflict|inconsisten|contradict)",
    re.IGNORECASE,
)
NUMBER_OF_DAYS = re.compile(r"\b\d+\s*(?:business\s+)?days?\b", re.IGNORECASE)


def classify(reply):
    """Return 'admitted_ignorance' or 'gave_number'. Ignorance wins: a reply that
    says 'I don't have it' and then mentions '3-5 days' for shipping is still a decline."""
    if IGNORANCE.search(reply):
        return "admitted_ignorance"
    if NUMBER_OF_DAYS.search(reply):
        return "gave_number"
    return "other"


def is_silent_failure(kind, expected):
    """A silent failure is a confident answer where the context could not support one.
    The call succeeded, nothing raised, and the span level is DEFAULT."""
    return expected == "admitted_ignorance" and kind == "gave_number"
