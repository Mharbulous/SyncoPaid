"""Secure deletion utilities for attorney-client privileged data."""

import os
from pathlib import Path
import logging


def secure_delete_file(file_path: Path, passes: int = 1) -> bool:
    """
    Securely delete a file by overwriting with zeros before unlinking.

    Args:
        file_path: Path to file to securely delete
        passes: Number of overwrite passes (default 1 for SSD optimization)

    Returns:
        True if file was successfully deleted, False if file didn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False

    try:
        file_size = file_path.stat().st_size

        # Overwrite with zeros
        with open(file_path, 'wb') as f:
            for _ in range(passes):
                f.seek(0)
                # Write in chunks to handle large files
                chunk_size = 65536  # 64KB chunks
                remaining = file_size
                while remaining > 0:
                    write_size = min(chunk_size, remaining)
                    f.write(b'\x00' * write_size)
                    remaining -= write_size
                f.flush()
                os.fsync(f.fileno())

        # Delete the file
        file_path.unlink()
        logging.debug(f"Securely deleted: {file_path}")
        return True

    except Exception as e:
        logging.error(f"Failed to securely delete {file_path}: {e}")
        # Fall back to regular deletion
        try:
            file_path.unlink()
            return True
        except Exception:
            return False
