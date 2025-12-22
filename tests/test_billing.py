"""Tests for billing utilities."""
import pytest
from syncopaid.billing import round_to_increment, minutes_to_hours, format_billing_time


def test_round_to_billing_increment():
    assert round_to_increment(5, 6) == 6     # 5 min -> 6 min
    assert round_to_increment(7, 6) == 12    # 7 min -> 12 min
    assert round_to_increment(120, 6) == 120  # 2 hours exact
    assert round_to_increment(1, 6) == 6     # minimum billing
    assert round_to_increment(0, 6) == 0     # zero stays zero


def test_round_to_increment_edge_cases():
    assert round_to_increment(6, 6) == 6     # exactly 6 min
    assert round_to_increment(12, 6) == 12   # exactly 12 min
    assert round_to_increment(6.5, 6) == 12  # fractional rounds up


def test_minutes_to_hours():
    assert minutes_to_hours(6) == 0.1
    assert minutes_to_hours(12) == 0.2
    assert minutes_to_hours(60) == 1.0
    assert minutes_to_hours(90) == 1.5


def test_format_billing_time():
    assert format_billing_time(6) == "0.1 hours"
    assert format_billing_time(60) == "1.0 hour"
    assert format_billing_time(90) == "1.5 hours"


def test_generate_narrative():
    from syncopaid.billing import generate_billing_narrative

    activities = [
        {'app': 'Chrome', 'title': 'Estate Tax Research'},
        {'app': 'Word', 'title': 'Trust Amendment Draft.docx'}
    ]
    narrative = generate_billing_narrative(activities)

    assert narrative != ""
    assert len(narrative) > 0


def test_generate_narrative_empty():
    from syncopaid.billing import generate_billing_narrative
    assert generate_billing_narrative([]) == ""


def test_generate_basic_narrative():
    from syncopaid.billing import _generate_basic_narrative

    activities = [
        {'app': 'WINWORD.EXE', 'title': 'Contract Review.docx'}
    ]
    narrative = _generate_basic_narrative(activities)

    assert 'document drafting' in narrative or 'Contract Review' in narrative


if __name__ == "__main__":
    test_round_to_billing_increment()
    test_round_to_increment_edge_cases()
    test_minutes_to_hours()
    test_format_billing_time()
    print("All tests passed!")
