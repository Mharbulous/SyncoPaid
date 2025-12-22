"""Screenshot archiving and retention management."""
import os
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
