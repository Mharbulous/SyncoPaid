import pytest
from syncopaid.batch_analysis_progress import BatchAnalysisProgress


def test_progress_initialization():
    """Test BatchAnalysisProgress initializes with correct values."""
    progress = BatchAnalysisProgress(total=100)

    assert progress.total == 100
    assert progress.processed == 0
    assert progress.failed == 0
    assert progress.is_cancelled is False
    assert progress.is_complete is False


def test_progress_update():
    """Test progress can be updated."""
    progress = BatchAnalysisProgress(total=10)

    progress.processed = 5
    progress.failed = 1

    assert progress.processed == 5
    assert progress.failed == 1
    assert progress.percent_complete == 50.0


def test_progress_cancel():
    """Test cancellation flag."""
    progress = BatchAnalysisProgress(total=10)

    progress.cancel()

    assert progress.is_cancelled is True
