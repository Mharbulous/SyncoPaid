"""Batch analysis progress dialog."""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from typing import Callable, Optional

from syncopaid.batch_analysis_progress import BatchAnalysisProgress


class BatchAnalysisDialog:
    """
    Dialog showing batch screenshot analysis progress.

    Features:
    - Progress bar with percentage
    - Status text (X of Y processed)
    - Cancel button
    - Performance warning before starting
    - Runs analysis in background thread
    """

    def __init__(
        self,
        parent: Optional[tk.Tk],
        night_processor,
        get_pending_count: Callable[[], int]
    ):
        """
        Initialize batch analysis dialog.

        Args:
            parent: Parent tkinter window (or None for standalone)
            night_processor: NightProcessor instance with process_batch_with_progress
            get_pending_count: Function returning count of pending screenshots
        """
        self.night_processor = night_processor
        self.get_pending_count = get_pending_count
        self.total_pending = get_pending_count()

        self.progress = BatchAnalysisProgress(
            total=self.total_pending,
            on_progress=self._update_ui
        )

        self._processing_thread: Optional[threading.Thread] = None
        self._create_window(parent)

    def _create_window(self, parent: Optional[tk.Tk]):
        """Create the dialog window."""
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()

        self.window.title("Analyze Screenshots")
        self.window.geometry("400x180")
        self.window.resizable(False, False)

        # Main frame with padding
        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Status label
        self.status_var = tk.StringVar(value=f"Ready to analyze {self.total_pending} screenshots")
        ttk.Label(frame, textvariable=self.status_var).pack(pady=(0, 10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            frame,
            orient=tk.HORIZONTAL,
            length=350,
            mode='determinate'
        )
        self.progress_bar.pack(pady=10)

        # Percentage label
        self.percent_var = tk.StringVar(value="0%")
        ttk.Label(frame, textvariable=self.percent_var).pack()

        # Warning label
        self.warning_var = tk.StringVar(value="⚠ This may slow down your computer while processing")
        ttk.Label(frame, textvariable=self.warning_var, foreground='orange').pack(pady=(10, 0))

        # Button frame
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(15, 0))

        self.start_btn = ttk.Button(btn_frame, text="Start Analysis", command=self._on_start)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self._on_cancel)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_start(self):
        """Start the analysis process."""
        if self.total_pending == 0:
            messagebox.showinfo("No Screenshots", "No screenshots pending analysis.")
            self.window.destroy()
            return

        self.start_btn.config(state=tk.DISABLED)
        self.status_var.set(f"Processing 0 of {self.total_pending}...")
        self.warning_var.set("Processing in progress...")

        # Start processing in background thread
        self._processing_thread = threading.Thread(
            target=self._run_analysis,
            daemon=True
        )
        self._processing_thread.start()

    def _run_analysis(self):
        """Run analysis in background thread."""
        try:
            self.night_processor.process_batch_with_progress(self.progress)
        except Exception as e:
            logging.error(f"Batch analysis error: {e}")
            self.progress.is_complete = True
        finally:
            self.window.after(0, self._on_complete)

    def _update_ui(self, progress: BatchAnalysisProgress):
        """Update UI from progress callback (called from background thread)."""
        def update():
            self.progress_bar['value'] = progress.percent_complete
            self.percent_var.set(f"{progress.percent_complete:.0f}%")
            self.status_var.set(
                f"Processing {progress.processed} of {progress.total}... "
                f"({progress.failed} failed)"
            )
        self.window.after(0, update)

    def _on_cancel(self):
        """Handle cancel button click."""
        self.progress.cancel()
        self.status_var.set("Cancelling...")
        self.cancel_btn.config(state=tk.DISABLED)

    def _on_complete(self):
        """Handle completion of analysis."""
        if self.progress.is_cancelled:
            msg = f"Cancelled after processing {self.progress.processed} screenshots."
        else:
            msg = f"Completed! Processed {self.progress.processed} screenshots ({self.progress.failed} failed)."

        self.status_var.set(msg)
        self.warning_var.set("")
        self.progress_bar['value'] = 100
        self.percent_var.set("Done")
        self.cancel_btn.config(text="Close", state=tk.NORMAL, command=self.window.destroy)
        self.start_btn.pack_forget()

    def _on_close(self):
        """Handle window close."""
        if self._processing_thread and self._processing_thread.is_alive():
            self.progress.cancel()
            # Wait briefly for thread to finish
            self._processing_thread.join(timeout=1.0)
        self.window.destroy()

    def show(self):
        """Show the dialog and wait for it to close."""
        self.window.grab_set()
        self.window.wait_window()
