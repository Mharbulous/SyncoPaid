"""Screenshot archiving and retention management."""
import os
import logging
import shutil
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import zipfile


class ArchiveWorker:
    """Manages screenshot archiving and cleanup."""

    def __init__(self, screenshot_dir: Path, archive_dir: Path):
        """Initialize archiver.

        Args:
            screenshot_dir: Path to screenshots directory
            archive_dir: Path to archives directory
        """
        self.screenshot_dir = Path(screenshot_dir)
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.last_run_date = None

    def get_archivable_folders(self, reference_date: datetime) -> List[str]:
        """Get folders eligible for archiving.

        Folders are archivable if they are from a month that has completely passed
        (i.e., date < first day of previous month).

        Args:
            reference_date: Date to use as reference for calculating cutoff

        Returns:
            List of folder names eligible for archiving
        """
        # Folders with date < first day of previous month
        cutoff = (reference_date.replace(day=1) - timedelta(days=1)).replace(day=1)

        archivable = []
        if self.screenshot_dir.exists():
            for folder_name in os.listdir(self.screenshot_dir):
                folder_path = self.screenshot_dir / folder_name
                if folder_path.is_dir():
                    try:
                        # Parse date from folder name (YYYY-MM-DD format)
                        folder_date = datetime.strptime(folder_name, "%Y-%m-%d")
                        if folder_date < cutoff:
                            archivable.append(folder_name)
                    except ValueError:
                        # Skip folders that don't match expected format
                        continue

        return archivable

    @staticmethod
    def group_by_month(folders: List[str]) -> Dict[str, List[str]]:
        """Group folders by month (YYYY-MM).

        Args:
            folders: List of folder names in YYYY-MM-DD format

        Returns:
            Dictionary mapping month keys to lists of folder names
        """
        groups = {}
        for folder in folders:
            month_key = folder[:7]  # "2025-10"
            groups.setdefault(month_key, []).append(folder)
        return groups

    def create_archive(self, month_key: str, folders: List[str]) -> Path:
        """Create zip archive from folders.

        Args:
            month_key: Month identifier (YYYY-MM)
            folders: List of folder names to archive

        Returns:
            Path to created zip file
        """
        zip_path = self.archive_dir / f"{month_key}_screenshots.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for folder in folders:
                folder_path = self.screenshot_dir / folder
                for file in folder_path.rglob("*.jpg"):
                    arcname = f"{folder}/{file.name}"
                    zf.write(file, arcname)
        return zip_path

    def archive_month(self, month_key: str, folders: List[str]):
        """Archive folders for a month and clean up.

        Args:
            month_key: Month identifier (YYYY-MM)
            folders: List of folder names to archive
        """
        zip_path = self.create_archive(month_key, folders)
        # Verify zip created successfully before deleting
        if zip_path.exists() and zip_path.stat().st_size > 0:
            for folder in folders:
                shutil.rmtree(self.screenshot_dir / folder)
            logging.info(f"Archived and cleaned up {len(folders)} folders for {month_key}")

    def run_once(self):
        """Run archiving process synchronously."""
        today = datetime.now().date()
        archivable = self.get_archivable_folders(datetime.now())
        grouped = self.group_by_month(archivable)
        for month_key, folders in grouped.items():
            try:
                self.archive_month(month_key, folders)
            except Exception as e:
                self._handle_error(month_key, e)
        self.last_run_date = today

    def start_background(self):
        """Start background thread for monthly checks."""
        threading.Thread(target=self._background_loop, daemon=True).start()

    def _background_loop(self):
        while True:
            time.sleep(86400)  # Check daily
            today = datetime.now().date()
            if self.last_run_date is None or today.month != self.last_run_date.month:
                self.run_once()

    def _handle_error(self, month_key: str, error: Exception):
        """Handle archiving errors.

        Args:
            month_key: Month identifier that failed
            error: Exception that occurred
        """
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()

        message = f"Failed to archive {month_key}: {error}\n\nRetry options:"
        response = messagebox.askretrycancel(
            "Archive Failed",
            message,
            detail="Choose Retry to try again now, or Cancel to retry on next startup"
        )

        if response:  # Retry now
            archivable = self.get_archivable_folders(datetime.now())
            grouped = self.group_by_month(archivable)
            if month_key in grouped:
                self.archive_month(month_key, grouped[month_key])
        else:  # Cancel - will retry on next startup
            logging.warning(f"Archive pending for {month_key}")

        root.destroy()
