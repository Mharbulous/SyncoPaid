"""Test transition detection patterns."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from syncopaid.transition_detector import TransitionDetector


def test_detect_inbox_browsing():
    """Test detection of inbox browsing transition."""
    detector = TransitionDetector()

    # Simulate Outlook inbox window
    is_transition = detector.is_transition(
        app="OUTLOOK.EXE",
        title="Inbox - brahm@example.com - Outlook",
        prev_app="WINWORD.EXE",
        prev_title="Document1.docx",
        idle_seconds=0
    )

    assert is_transition == True, "Should detect inbox browsing transition"
    assert detector.last_transition_type == "inbox_browsing"


def test_detect_idle_return():
    """Test detection of idle return transition."""
    detector = TransitionDetector()

    # Return from 5+ minute idle
    is_transition = detector.is_transition(
        app="chrome.exe",
        title="Google Search",
        prev_app=None,
        prev_title=None,
        idle_seconds=320
    )

    assert is_transition == True, "Should detect idle return transition"
    assert detector.last_transition_type == "idle_return"


def test_no_transition_during_document_edit():
    """Test that active document editing doesn't trigger transition."""
    detector = TransitionDetector()

    # Active Word editing should not trigger
    is_transition = detector.is_transition(
        app="WINWORD.EXE",
        title="Contract.docx - Word",
        prev_app="WINWORD.EXE",
        prev_title="Contract.docx - Word",
        idle_seconds=0
    )

    assert is_transition == False, "Should not interrupt active document editing"


if __name__ == "__main__":
    test_detect_inbox_browsing()
    print("✓ test_detect_inbox_browsing PASSED")
    test_detect_idle_return()
    print("✓ test_detect_idle_return PASSED")
    test_no_transition_during_document_edit()
    print("✓ test_no_transition_during_document_edit PASSED")
    print("\nALL TESTS PASSED")
