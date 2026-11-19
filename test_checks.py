from checks import classify, is_silent_failure


def test_gave_number():
    assert classify("You have 30 days from the date of delivery.") == "gave_number"


def test_admitted_ignorance():
    assert classify("I don't have a return window in the shop policy.") == "admitted_ignorance"


def test_ignorance_beats_unrelated_number():
    assert classify("The policy doesn't say. Shipping takes 3-5 business days.") == "admitted_ignorance"


def test_conflict_is_a_decline():
    assert classify("The policy gives conflicting windows, 30 and 14 days.") == "admitted_ignorance"


def test_other():
    assert classify("Happy to help!") == "other"


def test_silent_failure_only_when_context_cannot_support_a_number():
    assert is_silent_failure("gave_number", "admitted_ignorance")
    assert not is_silent_failure("admitted_ignorance", "admitted_ignorance")
    assert not is_silent_failure("gave_number", "gave_number")
