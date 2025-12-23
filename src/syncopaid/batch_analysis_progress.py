"""Batch analysis progress tracking."""
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class BatchAnalysisProgress:
    """
    Tracks progress of batch screenshot analysis.

    Attributes:
        total: Total screenshots to process
        processed: Number successfully processed
        failed: Number that failed
        is_cancelled: True if user cancelled
        is_complete: True when processing finished
        on_progress: Optional callback for progress updates
    """
    total: int
    processed: int = 0
    failed: int = 0
    is_cancelled: bool = False
    is_complete: bool = False
    on_progress: Optional[Callable[['BatchAnalysisProgress'], None]] = field(default=None, repr=False)

    @property
    def percent_complete(self) -> float:
        """Get completion percentage."""
        if self.total == 0:
            return 100.0
        return (self.processed / self.total) * 100.0

    def cancel(self):
        """Request cancellation of processing."""
        self.is_cancelled = True

    def update(self, processed: int = None, failed: int = None):
        """Update progress and trigger callback."""
        if processed is not None:
            self.processed = processed
        if failed is not None:
            self.failed = failed
        if self.on_progress:
            self.on_progress(self)
