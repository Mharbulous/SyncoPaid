# First-Run Model Download & Cache Management - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 14.5 | **Created:** 2025-12-23 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Implement automatic model download on first use with custom cache directory, progress indication, and cache management utilities.

**Approach:** Create a `ModelDownloader` class that downloads HuggingFace models to app data directory (not default HF cache). Use huggingface_hub for downloads with progress callbacks. Pin model revision for reproducibility. Add offline detection and resume capability.

**Tech Stack:** huggingface_hub, tqdm (progress), pathlib, existing config system, config_paths.py for app data location

**Related Plans:**
- `036_moondream2-integration.md` - Uses ModelDownloader in Task 6 to ensure model is downloaded before worker loads it

---

## Story Context

**Title:** First-Run Model Download & Cache Management

**User Story:**
> As a user, I want the AI model to download automatically on first use, so that I don't need to manually configure model paths.

**Acceptance Criteria:**
- [ ] Model downloads to app data directory (not HuggingFace default cache)
- [ ] Progress indicator during ~7.6GB download (full repository)
- [ ] Pinned model revision for reproducibility
- [ ] Cache clearing utility for troubleshooting
- [ ] Offline detection with clear error message
- [ ] Resume capability for interrupted downloads

## Prerequisites

- [ ] Story 14.1 (VisionEngine interface) implemented
- [ ] Story 14.2 (Hardware detection) implemented
- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_model_downloader.py` | Create | Unit tests for download manager |
| `src/syncopaid/model_downloader.py` | Create | Model download logic |
| `src/syncopaid/config_paths.py` | Modify | Add model cache path function |
| `src/syncopaid/config_dataclass.py` | Modify | Add model cache config fields |

## TDD Tasks

### Task 1: Add Model Cache Path Function (~2 min)

**Files:**
- Modify: `tests/test_config_paths.py` (create if needed)
- Modify: `src/syncopaid/config_paths.py`

**Context:** SyncoPaid uses `%LOCALAPPDATA%\SyncoPaid\` for user data. Models should go in a `models\` subdirectory to keep them separate from config/db.

**Step 1 - RED:** Write failing test

```python
# tests/test_config_paths.py
"""Tests for configuration path utilities."""
import pytest
from pathlib import Path
from syncopaid.config_paths import get_model_cache_path


def test_get_model_cache_path_returns_path():
    """get_model_cache_path returns a Path object."""
    result = get_model_cache_path()
    assert isinstance(result, Path)


def test_get_model_cache_path_in_syncopaid_dir():
    """Model cache is inside SyncoPaid app data directory."""
    result = get_model_cache_path()
    # Should be in SyncoPaid directory regardless of platform
    assert "SyncoPaid" in str(result)
    assert result.name == "models"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config_paths.py::test_get_model_cache_path_returns_path -v
```
Expected: `FAILED` (no function get_model_cache_path)

**Step 3 - GREEN:** Add model cache path function

```python
# src/syncopaid/config_paths.py (add after get_default_database_path)

def get_model_cache_path() -> Path:
    """
    Get the model cache directory path for the current platform.

    Models are stored separately from config/db in a 'models' subdirectory.
    This avoids polluting the default HuggingFace cache.

    Returns:
        Path object pointing to models directory
    """
    if sys.platform == 'win32':
        appdata = os.environ.get('LOCALAPPDATA')
        if not appdata:
            appdata = Path.home() / 'AppData' / 'Local'
        else:
            appdata = Path(appdata)
        models_dir = appdata / 'SyncoPaid' / 'models'
    else:
        models_dir = Path.home() / '.local' / 'share' / 'SyncoPaid' / 'models'

    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config_paths.py -v
```

**Step 5 - COMMIT:**
```bash
git add tests/test_config_paths.py src/syncopaid/config_paths.py && git commit -m "feat: add get_model_cache_path for custom model storage"
```

---

### Task 2: Create ModelDownloader Class Skeleton (~3 min)

**Files:**
- Create: `tests/test_model_downloader.py`
- Create: `src/syncopaid/model_downloader.py`

**Context:** ModelDownloader manages downloading HuggingFace models to local cache. It wraps huggingface_hub with progress callbacks and custom cache location.

**Step 1 - RED:** Write failing test

```python
# tests/test_model_downloader.py
"""Tests for model download manager."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from syncopaid.model_downloader import ModelDownloader


def test_model_downloader_init():
    """ModelDownloader initializes with default settings."""
    downloader = ModelDownloader()
    assert downloader.cache_dir is not None
    assert isinstance(downloader.cache_dir, Path)


def test_model_downloader_custom_cache_dir(tmp_path):
    """ModelDownloader accepts custom cache directory."""
    downloader = ModelDownloader(cache_dir=tmp_path)
    assert downloader.cache_dir == tmp_path
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_model_downloader.py::test_model_downloader_init -v
```
Expected: `FAILED` (module not found)

**Step 3 - GREEN:** Create skeleton class

```python
# src/syncopaid/model_downloader.py
"""Model download manager for HuggingFace models.

Handles downloading vision models to local cache with progress indication,
pinned revisions, and resume capability.
"""
import logging
from pathlib import Path
from typing import Optional, Callable

from syncopaid.config_paths import get_model_cache_path


class ModelDownloader:
    """Manages downloading and caching HuggingFace models.

    Attributes:
        cache_dir: Directory for storing downloaded models
        progress_callback: Optional callback for download progress
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ):
        """Initialize model downloader.

        Args:
            cache_dir: Custom cache directory (uses app data if None)
            progress_callback: Callback(downloaded_bytes, total_bytes, filename)
        """
        self.cache_dir = cache_dir or get_model_cache_path()
        self.progress_callback = progress_callback
        self._logger = logging.getLogger(__name__)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_model_downloader.py -v
```

**Step 5 - COMMIT:**
```bash
git add tests/test_model_downloader.py src/syncopaid/model_downloader.py && git commit -m "feat: add ModelDownloader skeleton class"
```

---

### Task 3: Add Offline Detection (~3 min)

**Files:**
- Modify: `tests/test_model_downloader.py`
- Modify: `src/syncopaid/model_downloader.py`

**Context:** Before attempting download, check network connectivity. Fail fast with clear error if offline.

**Step 1 - RED:** Write failing test

```python
# tests/test_model_downloader.py (append)

def test_is_online_returns_bool():
    """is_online returns boolean indicating network status."""
    downloader = ModelDownloader()
    result = downloader.is_online()
    assert isinstance(result, bool)


@patch('syncopaid.model_downloader.socket.create_connection')
def test_is_online_returns_false_when_offline(mock_socket):
    """is_online returns False when network unreachable."""
    mock_socket.side_effect = OSError("Network unreachable")

    downloader = ModelDownloader()
    assert downloader.is_online() is False


@patch('syncopaid.model_downloader.socket.create_connection')
def test_is_online_returns_true_when_connected(mock_socket):
    """is_online returns True when network reachable."""
    mock_socket.return_value = MagicMock()

    downloader = ModelDownloader()
    assert downloader.is_online() is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_model_downloader.py::test_is_online_returns_bool -v
```

**Step 3 - GREEN:** Add network check

```python
# src/syncopaid/model_downloader.py (add import and method)
import socket

# In ModelDownloader class:
    def is_online(self, timeout: float = 3.0) -> bool:
        """Check if network is available.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if can connect to HuggingFace, False otherwise
        """
        try:
            # Try to connect to HuggingFace CDN
            socket.create_connection(("huggingface.co", 443), timeout=timeout)
            return True
        except (socket.timeout, OSError):
            return False
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_model_downloader.py -v
```

**Step 5 - COMMIT:**
```bash
git add tests/test_model_downloader.py src/syncopaid/model_downloader.py && git commit -m "feat: add offline detection to ModelDownloader"
```

---

### Task 4: Add Model Info and Existence Check (~3 min)

**Files:**
- Modify: `tests/test_model_downloader.py`
- Modify: `src/syncopaid/model_downloader.py`

**Context:** Check if model is already downloaded before attempting download. Track model metadata (revision, size).

**Step 1 - RED:** Write failing test

```python
# tests/test_model_downloader.py (append)
from dataclasses import dataclass

def test_model_info_dataclass():
    """ModelInfo holds model metadata."""
    from syncopaid.model_downloader import ModelInfo

    info = ModelInfo(
        model_id="Mharbulous/moondream2-syncopaid",
        revision="2025-06-21",
        size_bytes=3_850_000_000,
        is_downloaded=False
    )
    assert info.model_id == "Mharbulous/moondream2-syncopaid"
    assert info.size_bytes == 3_850_000_000
    assert info.size_gb == pytest.approx(3.58, rel=0.1)


def test_is_model_downloaded_false_when_not_exists(tmp_path):
    """is_model_downloaded returns False when model not in cache."""
    downloader = ModelDownloader(cache_dir=tmp_path)

    result = downloader.is_model_downloaded("Mharbulous/moondream2-syncopaid")
    assert result is False


def test_is_model_downloaded_true_when_exists(tmp_path):
    """is_model_downloaded returns True when model in cache."""
    # Create marker file that huggingface_hub uses
    model_dir = tmp_path / "models--Mharbulous--moondream2-syncopaid"
    model_dir.mkdir(parents=True)
    (model_dir / "refs" / "main").parent.mkdir(parents=True)
    (model_dir / "refs" / "main").write_text("abc123")

    downloader = ModelDownloader(cache_dir=tmp_path)
    result = downloader.is_model_downloaded("Mharbulous/moondream2-syncopaid")
    assert result is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_model_downloader.py::test_model_info_dataclass -v
```

**Step 3 - GREEN:** Add ModelInfo and existence check

```python
# src/syncopaid/model_downloader.py (add dataclass and methods)
from dataclasses import dataclass

@dataclass
class ModelInfo:
    """Metadata about a downloadable model.

    Attributes:
        model_id: HuggingFace model ID (e.g., "Mharbulous/moondream2-syncopaid")
        revision: Git revision/tag for pinned version
        size_bytes: Approximate download size in bytes
        is_downloaded: Whether model is already in cache
    """
    model_id: str
    revision: str
    size_bytes: int
    is_downloaded: bool

    @property
    def size_gb(self) -> float:
        """Size in gigabytes."""
        return self.size_bytes / (1024 ** 3)


# In ModelDownloader class:
    def is_model_downloaded(self, model_id: str) -> bool:
        """Check if a model is already downloaded to cache.

        Args:
            model_id: HuggingFace model ID

        Returns:
            True if model exists in cache
        """
        # huggingface_hub cache structure: models--{org}--{repo}
        cache_name = model_id.replace("/", "--")
        model_dir = self.cache_dir / f"models--{cache_name}"

        # Check for refs/main which indicates completed download
        refs_file = model_dir / "refs" / "main"
        return refs_file.exists()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_model_downloader.py -v
```

**Step 5 - COMMIT:**
```bash
git add tests/test_model_downloader.py src/syncopaid/model_downloader.py && git commit -m "feat: add ModelInfo dataclass and download existence check"
```

---

### Task 5: Implement Download with Progress (~5 min)

**Files:**
- Modify: `tests/test_model_downloader.py`
- Modify: `src/syncopaid/model_downloader.py`

**Context:** Use huggingface_hub's snapshot_download with custom cache and progress. Pin revision for reproducibility.

**Step 1 - RED:** Write failing test

```python
# tests/test_model_downloader.py (append)

@patch('syncopaid.model_downloader.snapshot_download')
def test_download_model_calls_snapshot_download(mock_download, tmp_path):
    """download_model uses huggingface_hub snapshot_download."""
    mock_download.return_value = str(tmp_path / "model")

    downloader = ModelDownloader(cache_dir=tmp_path)
    result = downloader.download_model(
        model_id="Mharbulous/moondream2-syncopaid",
        revision="2025-06-21"
    )

    mock_download.assert_called_once()
    call_kwargs = mock_download.call_args[1]
    assert call_kwargs["repo_id"] == "Mharbulous/moondream2-syncopaid"
    assert call_kwargs["revision"] == "2025-06-21"
    assert call_kwargs["cache_dir"] == tmp_path


@patch('syncopaid.model_downloader.snapshot_download')
def test_download_model_raises_on_offline(mock_download, tmp_path):
    """download_model raises OfflineError when network unavailable."""
    from syncopaid.model_downloader import OfflineError

    mock_download.side_effect = Exception("Connection refused")

    downloader = ModelDownloader(cache_dir=tmp_path)

    with patch.object(downloader, 'is_online', return_value=False):
        with pytest.raises(OfflineError) as exc_info:
            downloader.download_model("Mharbulous/moondream2-syncopaid", "2025-06-21")

        assert "offline" in str(exc_info.value).lower()


@patch('syncopaid.model_downloader.snapshot_download')
def test_download_model_invokes_progress_callback(mock_download, tmp_path):
    """download_model calls progress_callback during download."""
    mock_download.return_value = str(tmp_path / "model")
    progress_calls = []

    def track_progress(downloaded, total, filename):
        progress_calls.append((downloaded, total, filename))

    downloader = ModelDownloader(
        cache_dir=tmp_path,
        progress_callback=track_progress
    )

    # Note: Real progress comes from huggingface_hub internals
    # This test just verifies callback is wired up
    downloader.download_model("Mharbulous/moondream2-syncopaid", "2025-06-21")

    mock_download.assert_called_once()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_model_downloader.py::test_download_model_calls_snapshot_download -v
```

**Step 3 - GREEN:** Implement download

```python
# src/syncopaid/model_downloader.py (add imports and methods)
try:
    from huggingface_hub import snapshot_download
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    snapshot_download = None


class OfflineError(Exception):
    """Raised when download attempted while offline."""
    pass


class DownloadError(Exception):
    """Raised when model download fails."""
    pass


# In ModelDownloader class:
    def download_model(
        self,
        model_id: str,
        revision: str,
        resume: bool = True
    ) -> Path:
        """Download a model to the cache directory.

        Args:
            model_id: HuggingFace model ID
            revision: Git revision/tag to download
            resume: Whether to resume interrupted downloads

        Returns:
            Path to downloaded model directory

        Raises:
            OfflineError: If network is unavailable
            DownloadError: If download fails
        """
        if not HF_AVAILABLE:
            raise DownloadError("huggingface_hub not installed")

        # Check network first
        if not self.is_online():
            raise OfflineError(
                f"Cannot download {model_id}: network is offline. "
                "Please check your internet connection and try again."
            )

        self._logger.info(f"Downloading {model_id} (revision: {revision})")

        try:
            model_path = snapshot_download(
                repo_id=model_id,
                revision=revision,
                cache_dir=self.cache_dir,
                resume_download=resume,
                local_files_only=False
            )

            self._logger.info(f"Model downloaded to: {model_path}")
            return Path(model_path)

        except Exception as e:
            self._logger.error(f"Download failed: {e}")
            raise DownloadError(f"Failed to download {model_id}: {e}") from e
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_model_downloader.py -v
```

**Step 5 - COMMIT:**
```bash
git add tests/test_model_downloader.py src/syncopaid/model_downloader.py && git commit -m "feat: implement model download with progress and resume"
```

---

### Task 6: Add Cache Management Utilities (~3 min)

**Files:**
- Modify: `tests/test_model_downloader.py`
- Modify: `src/syncopaid/model_downloader.py`

**Context:** Provide utilities to clear cache for troubleshooting and check cache size.

**Step 1 - RED:** Write failing test

```python
# tests/test_model_downloader.py (append)
import shutil

def test_get_cache_size_returns_bytes(tmp_path):
    """get_cache_size returns total cache size in bytes."""
    # Create some files in cache
    model_dir = tmp_path / "models--test--model"
    model_dir.mkdir(parents=True)
    (model_dir / "model.bin").write_bytes(b"x" * 1000)
    (model_dir / "config.json").write_bytes(b"x" * 100)

    downloader = ModelDownloader(cache_dir=tmp_path)
    size = downloader.get_cache_size()

    assert size >= 1100  # At least our test files


def test_clear_cache_removes_all_models(tmp_path):
    """clear_cache removes all downloaded models."""
    # Create model directories
    model1 = tmp_path / "models--org1--model1"
    model2 = tmp_path / "models--org2--model2"
    model1.mkdir(parents=True)
    model2.mkdir(parents=True)
    (model1 / "file.bin").write_bytes(b"data")
    (model2 / "file.bin").write_bytes(b"data")

    downloader = ModelDownloader(cache_dir=tmp_path)
    downloader.clear_cache()

    assert not model1.exists()
    assert not model2.exists()


def test_clear_model_removes_specific_model(tmp_path):
    """clear_model removes only the specified model."""
    model1 = tmp_path / "models--org1--model1"
    model2 = tmp_path / "models--org2--model2"
    model1.mkdir(parents=True)
    model2.mkdir(parents=True)
    (model1 / "file.bin").write_bytes(b"data")
    (model2 / "file.bin").write_bytes(b"data")

    downloader = ModelDownloader(cache_dir=tmp_path)
    downloader.clear_model("org1/model1")

    assert not model1.exists()
    assert model2.exists()  # Other model untouched
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_model_downloader.py::test_get_cache_size_returns_bytes -v
```

**Step 3 - GREEN:** Add cache management methods

```python
# src/syncopaid/model_downloader.py (add imports and methods)
import shutil

# In ModelDownloader class:
    def get_cache_size(self) -> int:
        """Get total size of cached models in bytes.

        Returns:
            Total cache size in bytes
        """
        total = 0
        for path in self.cache_dir.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
        return total

    def get_cache_size_gb(self) -> float:
        """Get cache size in gigabytes."""
        return self.get_cache_size() / (1024 ** 3)

    def clear_cache(self) -> None:
        """Remove all cached models.

        Use for troubleshooting or freeing disk space.
        """
        self._logger.warning("Clearing entire model cache")
        for item in self.cache_dir.iterdir():
            if item.name.startswith("models--"):
                shutil.rmtree(item, ignore_errors=True)
                self._logger.info(f"Removed: {item.name}")

    def clear_model(self, model_id: str) -> bool:
        """Remove a specific model from cache.

        Args:
            model_id: HuggingFace model ID to remove

        Returns:
            True if model was removed, False if not found
        """
        cache_name = model_id.replace("/", "--")
        model_dir = self.cache_dir / f"models--{cache_name}"

        if model_dir.exists():
            shutil.rmtree(model_dir, ignore_errors=True)
            self._logger.info(f"Removed model: {model_id}")
            return True
        return False
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_model_downloader.py -v
```

**Step 5 - COMMIT:**
```bash
git add tests/test_model_downloader.py src/syncopaid/model_downloader.py && git commit -m "feat: add cache management utilities (clear, size check)"
```

---

### Task 7: Add Config Fields for Model Cache (~2 min)

**Files:**
- Modify: `tests/test_config.py`
- Modify: `src/syncopaid/config_dataclass.py`

**Context:** Add config fields for custom model cache path and default model revision.

**Step 1 - RED:** Write failing test

```python
# tests/test_config.py (append)

def test_config_model_cache_defaults():
    """Config has model cache settings with defaults."""
    from syncopaid.config_dataclass import Config

    config = Config()

    assert hasattr(config, 'model_cache_path')
    assert hasattr(config, 'model_default_revision')
    assert config.model_cache_path is None  # Uses app data by default
    assert config.model_default_revision == "2025-06-21"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config.py::test_config_model_cache_defaults -v
```

**Step 3 - GREEN:** Add config fields

```python
# src/syncopaid/config_dataclass.py (add after vision_engine fields)
    # Model download settings
    model_cache_path: Optional[str] = None  # Uses app data if None
    model_default_revision: str = "2025-06-21"  # Pinned for reproducibility
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config.py -v
```

**Step 5 - COMMIT:**
```bash
git add tests/test_config.py src/syncopaid/config_dataclass.py && git commit -m "feat: add model cache config fields"
```

---

### Task 8: Add Ensure Model Downloaded Convenience Function (~3 min)

**Files:**
- Modify: `tests/test_model_downloader.py`
- Modify: `src/syncopaid/model_downloader.py`

**Context:** Single function that checks if model exists, downloads if needed, returns path. Used by MoondreamEngine.

**Step 1 - RED:** Write failing test

```python
# tests/test_model_downloader.py (append)

@patch('syncopaid.model_downloader.snapshot_download')
def test_ensure_model_skips_download_if_exists(mock_download, tmp_path):
    """ensure_model doesn't download if model already cached."""
    # Create marker for existing model
    model_dir = tmp_path / "models--Mharbulous--moondream2-syncopaid"
    model_dir.mkdir(parents=True)
    (model_dir / "refs" / "main").parent.mkdir(parents=True)
    (model_dir / "refs" / "main").write_text("abc123")

    downloader = ModelDownloader(cache_dir=tmp_path)
    result = downloader.ensure_model("Mharbulous/moondream2-syncopaid", "2025-06-21")

    mock_download.assert_not_called()
    assert result is not None


@patch('syncopaid.model_downloader.snapshot_download')
def test_ensure_model_downloads_if_missing(mock_download, tmp_path):
    """ensure_model downloads model if not in cache."""
    mock_download.return_value = str(tmp_path / "downloaded_model")

    downloader = ModelDownloader(cache_dir=tmp_path)
    result = downloader.ensure_model("Mharbulous/moondream2-syncopaid", "2025-06-21")

    mock_download.assert_called_once()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_model_downloader.py::test_ensure_model_skips_download_if_exists -v
```

**Step 3 - GREEN:** Add ensure_model method

```python
# src/syncopaid/model_downloader.py (add method to class)

    def ensure_model(self, model_id: str, revision: str) -> Path:
        """Ensure model is downloaded, downloading if needed.

        This is the main entry point for model loading. It checks
        cache first and only downloads if necessary.

        Args:
            model_id: HuggingFace model ID
            revision: Git revision/tag

        Returns:
            Path to model directory

        Raises:
            OfflineError: If download needed but offline
            DownloadError: If download fails
        """
        if self.is_model_downloaded(model_id):
            self._logger.debug(f"Model {model_id} already cached")
            cache_name = model_id.replace("/", "--")
            return self.cache_dir / f"models--{cache_name}"

        self._logger.info(f"Model {model_id} not found, downloading...")
        return self.download_model(model_id, revision)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_model_downloader.py -v
```

**Step 5 - COMMIT:**
```bash
git add tests/test_model_downloader.py src/syncopaid/model_downloader.py && git commit -m "feat: add ensure_model convenience function"
```

---

## Final Verification

After all tasks complete:

```bash
# Run all tests
python -m pytest -v

# Run model downloader tests
python -m pytest tests/test_model_downloader.py -v

# Manual test (requires network)
python -c "
from syncopaid.model_downloader import ModelDownloader
dl = ModelDownloader()
print(f'Cache dir: {dl.cache_dir}')
print(f'Online: {dl.is_online()}')
print(f'Cache size: {dl.get_cache_size_gb():.2f} GB')
"
```

## Acceptance Criteria Checklist

- [ ] `pytest tests/test_model_downloader.py -v` passes
- [ ] Model downloads to app data directory (not ~/.cache/huggingface)
- [ ] Offline detection raises clear OfflineError
- [ ] is_model_downloaded correctly checks cache
- [ ] clear_cache and clear_model work correctly
- [ ] ensure_model skips download if already cached
- [ ] Config fields for model_cache_path and revision exist

---

## Notes for Implementer

1. **First Download**: First use downloads ~7.6GB from HuggingFace (full repository; ~3.85GB model weights). User should see progress.

2. **Progress Integration**: The progress_callback wiring to huggingface_hub's internal progress is complex. Consider using tqdm wrapper if detailed progress needed.

3. **Cache Structure**: huggingface_hub uses `models--{org}--{repo}/` structure with `refs/main` file.

4. **Resume**: huggingface_hub supports resume_download=True for interrupted downloads.

5. **Dependencies**: Ensure huggingface_hub is in requirements.txt.

6. **MoondreamEngine Integration**: After this story, the moondream_worker.py subprocess (from `036_moondream2-integration.md`) will use `ModelDownloader.ensure_model()` to download the model on first use. See Task 6 in plan 036.
