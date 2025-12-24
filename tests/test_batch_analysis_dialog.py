import pytest
from unittest.mock import MagicMock, patch


def test_batch_analysis_dialog_initialization():
    """Test dialog initializes without errors."""
    with patch('syncopaid.batch_analysis_dialog.tk.Toplevel'):
        from syncopaid.batch_analysis_dialog import BatchAnalysisDialog

        mock_processor = MagicMock()
        mock_processor.batch_size = 10

        mock_get_pending = MagicMock(return_value=50)

        dialog = BatchAnalysisDialog(
            parent=None,
            night_processor=mock_processor,
            get_pending_count=mock_get_pending
        )

        assert dialog.total_pending == 50


def test_batch_analysis_dialog_cancel_sets_flag():
    """Test cancel button sets cancellation flag."""
    with patch('syncopaid.batch_analysis_dialog.tk.Toplevel'):
        from syncopaid.batch_analysis_dialog import BatchAnalysisDialog

        mock_processor = MagicMock()
        mock_get_pending = MagicMock(return_value=10)

        dialog = BatchAnalysisDialog(
            parent=None,
            night_processor=mock_processor,
            get_pending_count=mock_get_pending
        )

        dialog._on_cancel()

        assert dialog.progress.is_cancelled is True
