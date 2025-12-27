# Moondream 2 Integration (CPU-Friendly) - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 14.6.1 | **Created:** 2025-12-23 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Implement Moondream 2 as the local vision LLM engine for screenshot analysis on CPU-only systems (8GB RAM minimum).

**Approach:** Use a **subprocess worker architecture** where Moondream runs in a separate process (`moondream_worker.py`) that can be spawned on demand and killed to reclaim memory. The `MoondreamEngine` class implements the `VisionEngine` interface and communicates with the worker via JSON over stdin/stdout. This keeps the main SyncoPaid app lightweight (~50MB) while allowing the 4GB+ model to be loaded only when needed and freed by terminating the worker.

**Architecture:**
```
SyncoPaid.exe (lightweight, ~50MB)
    └── spawns moondream_worker.py when analysis needed
            └── loads 3.85GB model into RAM
            └── processes analysis requests via JSON IPC
            └── can be killed to reclaim memory
```

**Tech Stack:** transformers, torch (CPU), einops, Pillow, subprocess, json, existing VisionEngine interface (from 14.1), HardwareInfo (from 14.2)

---

## Story Context

**Title:** Moondream 2 Integration (CPU-Friendly)

**User Story:**
> As a user without a dedicated GPU, I want screenshot analysis powered by Moondream 2, so that I get local AI categorization on standard hardware (8GB RAM minimum).

**Acceptance Criteria:**
- [ ] Moondream 2 model loads successfully on CPU via worker subprocess
- [ ] float32 precision used for CPU compatibility
- [ ] Image encoding cache for multiple queries per screenshot
- [ ] Inference completes within 25 seconds on minimum spec
- [ ] Graceful fallback on out-of-memory conditions
- [ ] Apache 2.0 license attribution included
- [ ] No network calls during inference (privacy compliance)
- [ ] Worker process can be spawned on demand
- [ ] Worker process can be killed to reclaim 4GB+ RAM
- [ ] Main app remains responsive while worker processes

## Prerequisites

- [ ] Story 14.1 (Local LLM Engine Architecture) must be implemented - provides VisionEngine base class
- [ ] Story 14.2 (Hardware Detection & Model Selection) must be implemented - provides hardware info
- [ ] Story 14.5 (Model Download & Cache) must be implemented - see `037_first-run-model-download-cache.md`
- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_moondream_engine.py` | Create | Unit tests for Moondream integration |
| `tests/test_moondream_worker.py` | Create | Unit tests for worker subprocess |
| `src/syncopaid/moondream_engine.py` | Create | Engine class (spawns/manages worker) |
| `src/syncopaid/moondream_worker.py` | Create | Subprocess that loads model and processes requests |
| `src/syncopaid/vision_engine.py` | Modify | Register Moondream engine |
| `src/syncopaid/config_defaults.py` | Modify | Add Moondream-specific config |
| `src/syncopaid/config_dataclass.py` | Modify | Add Moondream config fields |

## TDD Tasks

### Task 1: Create MoondreamEngine Class Skeleton (~3 min)

**Files:**
- Create: `tests/test_moondream_engine.py`
- Create: `src/syncopaid/moondream_engine.py`

**Context:** MoondreamEngine uses a subprocess architecture - it spawns `moondream_worker.py` on demand rather than loading the 3.85GB model in the main process. This keeps the main app lightweight and allows killing the worker to reclaim memory.

**Step 1 - RED:** Write failing test

```python
# tests/test_moondream_engine.py
"""Tests for Moondream 2 vision engine."""
import pytest
from unittest.mock import MagicMock, patch
from syncopaid.moondream_engine import MoondreamEngine
from syncopaid.vision_engine import VisionEngine


def test_moondream_engine_is_vision_engine():
    """MoondreamEngine implements VisionEngine interface."""
    assert issubclass(MoondreamEngine, VisionEngine)


def test_moondream_engine_init_does_not_spawn_worker():
    """MoondreamEngine does not spawn worker during __init__."""
    engine = MoondreamEngine()
    assert engine._worker_process is None
    assert engine._worker_running is False


def test_moondream_engine_name():
    """MoondreamEngine has correct engine name."""
    engine = MoondreamEngine()
    assert engine.name == "moondream2"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_engine.py::test_moondream_engine_is_vision_engine -v
```
Expected: `FAILED` (module not found)

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/moondream_engine.py
"""Moondream 2 vision engine using subprocess worker architecture.

Uses a separate worker process (moondream_worker.py) that loads the 3.85GB
model. This keeps the main SyncoPaid app lightweight and allows killing
the worker to reclaim 4GB+ RAM when not needed.

Model: Mharbulous/moondream2-syncopaid (frozen from vikhyatk/moondream2, Apache 2.0 license)
Requirements: 8GB RAM minimum, ~25 second inference on CPU
"""
import subprocess
import json
from typing import Optional
from pathlib import Path

from syncopaid.vision_engine import VisionEngine, AnalysisResult


class MoondreamEngine(VisionEngine):
    """Moondream 2 vision engine using subprocess worker.

    Spawns moondream_worker.py on demand for analysis, communicating
    via JSON over stdin/stdout. Worker can be killed to reclaim memory.

    Attributes:
        name: Engine identifier ("moondream2")
        _worker_process: The spawned worker subprocess (or None)
        _worker_running: Whether worker is currently running
    """

    name = "moondream2"

    def __init__(self):
        """Initialize engine without spawning worker."""
        self._worker_process: Optional[subprocess.Popen] = None
        self._worker_running = False

    def analyze(self, image_path: Path) -> AnalysisResult:
        """Analyze screenshot via worker subprocess."""
        raise NotImplementedError("Worker communication not yet implemented")

    def is_available(self) -> bool:
        """Check if worker script exists."""
        worker_path = Path(__file__).parent / "moondream_worker.py"
        return worker_path.exists()

    def kill_worker(self) -> bool:
        """Kill worker process to reclaim memory.

        Returns:
            True if worker was killed, False if not running
        """
        if self._worker_process and self._worker_running:
            self._worker_process.terminate()
            self._worker_process.wait()
            self._worker_process = None
            self._worker_running = False
            return True
        return False
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_engine.py -v
```

---

### Task 2: Create Worker Subprocess (~5 min)

**Files:**
- Create: `tests/test_moondream_worker.py`
- Create: `src/syncopaid/moondream_worker.py`

**Context:** The worker is a standalone Python script that loads the Moondream model and processes requests via JSON over stdin/stdout. It runs in a separate process so the main app stays lightweight. The model uses float32 on CPU (float16 causes LayerNormKernelImpl errors).

**Step 1 - RED:** Add failing tests

```python
# tests/test_moondream_worker.py
"""Tests for Moondream worker subprocess."""
import pytest
import json
from unittest.mock import MagicMock, patch


def test_worker_protocol_request_format():
    """Worker accepts JSON request with image_path."""
    from syncopaid.moondream_worker import parse_request

    request = {"action": "analyze", "image_path": "/path/to/image.png"}
    result = parse_request(json.dumps(request))

    assert result["action"] == "analyze"
    assert result["image_path"] == "/path/to/image.png"


def test_worker_protocol_response_format():
    """Worker returns JSON response with analysis result."""
    from syncopaid.moondream_worker import format_response

    result = {
        "description": "User editing document",
        "activity_type": "document_editing",
        "confidence": 0.85,
        "raw_output": "User is editing..."
    }

    response = format_response(result)
    parsed = json.loads(response)

    assert parsed["status"] == "success"
    assert parsed["result"]["description"] == "User editing document"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_worker.py -v
```
Expected: `FAILED` (module not found)

**Step 3 - GREEN:** Create worker subprocess

```python
# src/syncopaid/moondream_worker.py
"""Moondream 2 worker subprocess for screenshot analysis.

This script runs as a separate process, loading the 3.85GB model into RAM.
It communicates with the main SyncoPaid app via JSON over stdin/stdout.

Usage: python -m syncopaid.moondream_worker
Protocol:
  Request:  {"action": "analyze", "image_path": "/path/to/image.png"}
  Response: {"status": "success", "result": {...}} or {"status": "error", "message": "..."}
"""
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import torch
    from transformers import AutoModelForCausalLM
    from PIL import Image
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

# Frozen copy of vikhyatk/moondream2 tag 2025-06-21
MODEL_ID = "Mharbulous/moondream2-syncopaid"
MODEL_REVISION = "2025-06-21"


def parse_request(line: str) -> Dict[str, Any]:
    """Parse JSON request from stdin."""
    return json.loads(line.strip())


def format_response(result: Dict[str, Any], error: Optional[str] = None) -> str:
    """Format response as JSON for stdout."""
    if error:
        return json.dumps({"status": "error", "message": error})
    return json.dumps({"status": "success", "result": result})


class MoondreamWorker:
    """Worker that loads model and processes analysis requests."""

    def __init__(self):
        self._model = None
        self._device = None
        self._dtype = None
        self._loaded = False

    def load_model(self) -> None:
        """Load Moondream 2 model with CPU/GPU detection."""
        if self._loaded:
            return

        if not DEPENDENCIES_AVAILABLE:
            raise RuntimeError("Required dependencies not installed")

        # Detect hardware
        use_cuda = torch.cuda.is_available()
        self._device = "cuda" if use_cuda else "cpu"
        self._dtype = torch.float16 if use_cuda else torch.float32

        logging.info(f"Loading Moondream 2 on {self._device}")

        load_kwargs = {
            "revision": MODEL_REVISION,
            "trust_remote_code": True,
            "torch_dtype": self._dtype,
        }

        if use_cuda:
            load_kwargs["device_map"] = {"": "cuda"}

        self._model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            **load_kwargs
        )

        if not use_cuda:
            self._model = self._model.to(self._device)

        self._loaded = True
        logging.info("Model loaded successfully")

    def analyze(self, image_path: str) -> Dict[str, Any]:
        """Analyze screenshot and return structured result."""
        if not self._loaded:
            self.load_model()

        image = Image.open(image_path)
        encoded = self._model.encode_image(image)

        prompt = (
            "Describe what the user is doing on this screen. "
            "Focus on: application, activity type, visible document names."
        )
        response = self._model.query(encoded, prompt)
        raw_output = response.get("answer", "")

        return {
            "description": raw_output[:200],
            "activity_type": self._classify_activity(raw_output),
            "confidence": min(0.9, 0.5 + len(raw_output) / 200),
            "raw_output": raw_output
        }

    def _classify_activity(self, text: str) -> str:
        """Classify activity type from model output."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["email", "outlook", "mail"]):
            return "email"
        if any(w in text_lower for w in ["document", "word", "editing"]):
            return "document_editing"
        if any(w in text_lower for w in ["browser", "chrome", "web"]):
            return "web_browsing"
        if any(w in text_lower for w in ["research", "westlaw", "canlii"]):
            return "legal_research"
        return "general"


def main():
    """Main loop: read requests from stdin, write responses to stdout."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    worker = MoondreamWorker()

    # Signal ready
    print(json.dumps({"status": "ready"}), flush=True)

    for line in sys.stdin:
        try:
            request = parse_request(line)
            action = request.get("action")

            if action == "analyze":
                result = worker.analyze(request["image_path"])
                print(format_response(result), flush=True)
            elif action == "quit":
                break
            else:
                print(format_response(None, f"Unknown action: {action}"), flush=True)

        except Exception as e:
            print(format_response(None, str(e)), flush=True)


if __name__ == "__main__":
    main()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_worker.py -v
```

---

### Task 3: Implement Worker Spawning and Communication (~5 min)

**Files:**
- Modify: `tests/test_moondream_engine.py`
- Modify: `src/syncopaid/moondream_engine.py`

**Context:** MoondreamEngine spawns the worker subprocess on first analysis request. It communicates via JSON over stdin/stdout pipes. The worker stays alive for subsequent requests until explicitly killed.

**Step 1 - RED:** Add failing tests

```python
# tests/test_moondream_engine.py (add to existing file)

@patch('syncopaid.moondream_engine.subprocess.Popen')
def test_moondream_engine_spawns_worker(mock_popen):
    """MoondreamEngine spawns worker subprocess on first analyze call."""
    mock_process = MagicMock()
    mock_process.stdout.readline.return_value = '{"status": "ready"}\n'
    mock_popen.return_value = mock_process

    engine = MoondreamEngine()
    engine._ensure_worker_running()

    mock_popen.assert_called_once()
    assert engine._worker_running is True


@patch('syncopaid.moondream_engine.subprocess.Popen')
def test_moondream_engine_reuses_worker(mock_popen):
    """MoondreamEngine reuses existing worker for subsequent calls."""
    mock_process = MagicMock()
    mock_process.stdout.readline.return_value = '{"status": "ready"}\n'
    mock_popen.return_value = mock_process

    engine = MoondreamEngine()
    engine._ensure_worker_running()
    engine._ensure_worker_running()

    # Should only spawn once
    assert mock_popen.call_count == 1


def test_moondream_engine_kill_worker():
    """MoondreamEngine can kill worker to reclaim memory."""
    engine = MoondreamEngine()
    engine._worker_process = MagicMock()
    engine._worker_running = True

    result = engine.kill_worker()

    assert result is True
    assert engine._worker_running is False
    engine._worker_process.terminate.assert_called_once()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_engine.py::test_moondream_engine_spawns_worker -v
```

**Step 3 - GREEN:** Implement worker spawning

```python
# src/syncopaid/moondream_engine.py (update class with worker management)

import sys
import subprocess
import json
import logging
from typing import Optional
from pathlib import Path

from syncopaid.vision_engine import VisionEngine, AnalysisResult


class MoondreamEngine(VisionEngine):
    """Moondream 2 vision engine using subprocess worker."""

    name = "moondream2"

    def __init__(self):
        """Initialize engine without spawning worker."""
        self._worker_process: Optional[subprocess.Popen] = None
        self._worker_running = False

    def _ensure_worker_running(self) -> None:
        """Spawn worker subprocess if not already running."""
        if self._worker_running:
            return

        worker_script = Path(__file__).parent / "moondream_worker.py"

        self._worker_process = subprocess.Popen(
            [sys.executable, str(worker_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Wait for ready signal
        ready_line = self._worker_process.stdout.readline()
        ready = json.loads(ready_line)

        if ready.get("status") != "ready":
            raise RuntimeError(f"Worker failed to start: {ready}")

        self._worker_running = True
        logging.info("Moondream worker subprocess started")

    def _send_request(self, request: dict) -> dict:
        """Send request to worker and get response."""
        self._ensure_worker_running()

        # Send request
        self._worker_process.stdin.write(json.dumps(request) + "\n")
        self._worker_process.stdin.flush()

        # Read response
        response_line = self._worker_process.stdout.readline()
        return json.loads(response_line)

    def kill_worker(self) -> bool:
        """Kill worker process to reclaim memory."""
        if self._worker_process and self._worker_running:
            self._worker_process.terminate()
            self._worker_process.wait()
            self._worker_process = None
            self._worker_running = False
            logging.info("Moondream worker killed, memory reclaimed")
            return True
        return False

    def is_available(self) -> bool:
        """Check if worker script exists."""
        worker_path = Path(__file__).parent / "moondream_worker.py"
        return worker_path.exists()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_engine.py -v
```

---

### Task 4: Implement analyze() via Worker Communication (~4 min)

**Files:**
- Modify: `tests/test_moondream_engine.py`
- Modify: `src/syncopaid/moondream_engine.py`

**Context:** The analyze() method sends an analysis request to the worker subprocess and converts the JSON response to an AnalysisResult. Error handling ensures graceful degradation.

**Step 1 - RED:** Add failing tests

```python
# tests/test_moondream_engine.py (add to existing file)
from syncopaid.vision_engine import AnalysisResult
from pathlib import Path

@patch('syncopaid.moondream_engine.subprocess.Popen')
def test_moondream_engine_analyze_returns_result(mock_popen):
    """MoondreamEngine.analyze() returns AnalysisResult from worker."""
    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = [
        '{"status": "ready"}\n',
        '{"status": "success", "result": {"description": "User editing Word", "activity_type": "document_editing", "confidence": 0.85, "raw_output": "User editing Word doc"}}\n'
    ]
    mock_popen.return_value = mock_process

    engine = MoondreamEngine()
    result = engine.analyze(Path("/test/screenshot.png"))

    assert isinstance(result, AnalysisResult)
    assert result.description == "User editing Word"
    assert result.activity_type == "document_editing"
    assert result.confidence == 0.85


@patch('syncopaid.moondream_engine.subprocess.Popen')
def test_moondream_engine_analyze_handles_worker_error(mock_popen):
    """MoondreamEngine.analyze() handles worker errors gracefully."""
    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = [
        '{"status": "ready"}\n',
        '{"status": "error", "message": "Model failed to load"}\n'
    ]
    mock_popen.return_value = mock_process

    engine = MoondreamEngine()
    result = engine.analyze(Path("/test/screenshot.png"))

    assert isinstance(result, AnalysisResult)
    assert result.confidence == 0.0
    assert "error" in result.description.lower() or "failed" in result.raw_output.lower()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_engine.py::test_moondream_engine_analyze_returns_result -v
```

**Step 3 - GREEN:** Implement analyze()

```python
# src/syncopaid/moondream_engine.py (add analyze method to class)

def analyze(self, image_path: Path) -> AnalysisResult:
    """Analyze screenshot via worker subprocess.

    Args:
        image_path: Path to screenshot image file

    Returns:
        AnalysisResult with description, activity type, and confidence
    """
    try:
        response = self._send_request({
            "action": "analyze",
            "image_path": str(image_path)
        })

        if response.get("status") == "success":
            result = response["result"]
            return AnalysisResult(
                description=result["description"],
                activity_type=result["activity_type"],
                confidence=result["confidence"],
                raw_output=result["raw_output"]
            )
        else:
            # Worker returned an error
            error_msg = response.get("message", "Unknown error")
            logging.error(f"Worker analysis failed: {error_msg}")
            return AnalysisResult(
                description="Analysis failed",
                activity_type="unknown",
                confidence=0.0,
                raw_output=error_msg
            )

    except Exception as e:
        logging.error(f"Moondream analysis failed: {e}")
        return AnalysisResult(
            description="Analysis failed",
            activity_type="unknown",
            confidence=0.0,
            raw_output=str(e)
        )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_engine.py -v
```

---

### Task 5: Handle Worker OOM and Restart (~3 min)

**Files:**
- Modify: `tests/test_moondream_engine.py`
- Modify: `src/syncopaid/moondream_engine.py`

**Context:** The worker may crash due to OOM when loading the model. The engine should detect this, report a graceful error, and allow restarting the worker.

**Step 1 - RED:** Add failing tests

```python
# tests/test_moondream_engine.py (add to existing file)

@patch('syncopaid.moondream_engine.subprocess.Popen')
def test_moondream_engine_handles_worker_crash(mock_popen):
    """MoondreamEngine handles worker crash gracefully."""
    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = [
        '{"status": "ready"}\n',
        ''  # Empty line indicates process died
    ]
    mock_process.poll.return_value = 1  # Non-zero exit code
    mock_popen.return_value = mock_process

    engine = MoondreamEngine()
    result = engine.analyze(Path("/test/screenshot.png"))

    assert isinstance(result, AnalysisResult)
    assert result.confidence == 0.0
    assert engine._worker_running is False  # Worker marked as not running


@patch('syncopaid.moondream_engine.subprocess.Popen')
def test_moondream_engine_restarts_after_crash(mock_popen):
    """MoondreamEngine can restart worker after crash."""
    mock_process = MagicMock()
    mock_process.stdout.readline.return_value = '{"status": "ready"}\n'
    mock_popen.return_value = mock_process

    engine = MoondreamEngine()
    engine._worker_running = False  # Simulate previous crash

    engine._ensure_worker_running()

    assert mock_popen.called
    assert engine._worker_running is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_engine.py::test_moondream_engine_handles_worker_crash -v
```

**Step 3 - GREEN:** Add crash detection and restart logic

```python
# src/syncopaid/moondream_engine.py (update _send_request method)

def _send_request(self, request: dict) -> dict:
    """Send request to worker and get response."""
    self._ensure_worker_running()

    try:
        # Send request
        self._worker_process.stdin.write(json.dumps(request) + "\n")
        self._worker_process.stdin.flush()

        # Read response
        response_line = self._worker_process.stdout.readline()

        if not response_line:
            # Worker died unexpectedly
            self._worker_running = False
            exit_code = self._worker_process.poll()
            raise RuntimeError(f"Worker crashed (exit code: {exit_code})")

        return json.loads(response_line)

    except (BrokenPipeError, OSError) as e:
        # Worker process died
        self._worker_running = False
        raise RuntimeError(f"Worker communication failed: {e}") from e
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_engine.py -v
```

---

### Task 6: Integrate Worker with ModelDownloader (~4 min)

**Files:**
- Modify: `tests/test_moondream_worker.py`
- Modify: `src/syncopaid/moondream_worker.py`

**Context:** The worker must ensure the model is downloaded before loading. Use ModelDownloader from story 14.5 to check cache and download if needed. This provides proper progress indication and offline detection.

**Step 1 - RED:** Add failing test

```python
# tests/test_moondream_worker.py (add to existing file)

@patch('syncopaid.moondream_worker.ModelDownloader')
def test_worker_ensures_model_downloaded(mock_downloader_class):
    """Worker uses ModelDownloader to ensure model is available."""
    mock_downloader = MagicMock()
    mock_downloader.ensure_model.return_value = Path("/cache/model")
    mock_downloader_class.return_value = mock_downloader

    worker = MoondreamWorker()
    worker._ensure_model_available()

    mock_downloader.ensure_model.assert_called_once_with(
        "Mharbulous/moondream2-syncopaid",
        "2025-06-21"
    )


@patch('syncopaid.moondream_worker.ModelDownloader')
def test_worker_handles_offline_gracefully(mock_downloader_class):
    """Worker raises clear error when offline and model not cached."""
    from syncopaid.model_downloader import OfflineError

    mock_downloader = MagicMock()
    mock_downloader.ensure_model.side_effect = OfflineError("Network offline")
    mock_downloader_class.return_value = mock_downloader

    worker = MoondreamWorker()

    with pytest.raises(RuntimeError) as exc_info:
        worker._ensure_model_available()

    assert "offline" in str(exc_info.value).lower()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_worker.py::test_worker_ensures_model_downloaded -v
```

**Step 3 - GREEN:** Integrate ModelDownloader

```python
# src/syncopaid/moondream_worker.py (update imports and add method)

from syncopaid.model_downloader import ModelDownloader, OfflineError

# In MoondreamWorker class, add method:
    def _ensure_model_available(self) -> Path:
        """Ensure model is downloaded and return cache path.

        Uses ModelDownloader to check cache and download if needed.
        Provides proper offline detection and progress indication.

        Returns:
            Path to model in cache

        Raises:
            RuntimeError: If offline and model not cached
        """
        downloader = ModelDownloader()

        try:
            return downloader.ensure_model(MODEL_ID, MODEL_REVISION)
        except OfflineError as e:
            raise RuntimeError(
                f"Cannot load Moondream 2: {e}. "
                "Please connect to the internet for first-time model download."
            ) from e

# Update load_model to call _ensure_model_available:
    def load_model(self) -> None:
        """Load Moondream 2 model with CPU/GPU detection."""
        if self._loaded:
            return

        if not DEPENDENCIES_AVAILABLE:
            raise RuntimeError("Required dependencies not installed")

        # Ensure model is downloaded first
        self._ensure_model_available()

        # ... rest of existing load_model code ...
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_worker.py -v
```

---

### Task 7: Register Engine with Registry (~2 min)

**Files:**
- Modify: `tests/test_moondream_engine.py`
- Modify: `src/syncopaid/vision_engine.py`

**Context:** The VisionEngine registry (from Story 14.1) needs to know about MoondreamEngine. Registration happens via decorator or explicit registration.

**Step 1 - RED:** Add failing test

```python
# tests/test_moondream_engine.py (add to existing file)

def test_moondream_engine_registered():
    """MoondreamEngine is registered in the engine registry."""
    from syncopaid.vision_engine import get_engine, list_engines

    engines = list_engines()
    assert "moondream2" in engines

    engine = get_engine("moondream2")
    assert isinstance(engine, MoondreamEngine)
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_engine.py::test_moondream_engine_registered -v
```

**Step 3 - GREEN:** Register engine

```python
# src/syncopaid/vision_engine.py (add at end of file)

# Import and register Moondream engine
try:
    from syncopaid.moondream_engine import MoondreamEngine
    register_engine(MoondreamEngine)
except ImportError:
    pass  # Moondream dependencies not installed
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_engine.py -v
```

---

### Task 8: Add Config Settings for Moondream (~3 min)

**Files:**
- Modify: `tests/test_config.py`
- Modify: `src/syncopaid/config_dataclass.py`
- Modify: `src/syncopaid/config_defaults.py`

**Context:** Add configuration fields for Moondream-specific settings: model revision, cache directory, and inference timeout.

**Step 1 - RED:** Add failing test

```python
# tests/test_config.py (add to existing tests)

def test_config_moondream_defaults():
    """Config has Moondream-specific settings with defaults."""
    config = Config()

    assert config.moondream_repo_id == "Mharbulous/moondream2-syncopaid"
    assert config.moondream_inference_timeout_seconds == 30
    assert config.moondream_enabled is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config.py::test_config_moondream_defaults -v
```

**Step 3 - GREEN:** Add config fields

```python
# src/syncopaid/config_dataclass.py (add fields to Config class)

# After existing fields, add:
# Moondream (local vision AI) settings
moondream_enabled: bool = True
moondream_repo_id: str = "Mharbulous/moondream2-syncopaid"
moondream_inference_timeout_seconds: int = 30
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config.py -v
```

---

### Task 9: Add Apache 2.0 License Attribution (~2 min)

**Files:**
- Modify: `src/syncopaid/moondream_engine.py`

**Context:** Moondream 2 is Apache 2.0 licensed. Attribution must be included per license terms.

**Step 1 - RED:** Add failing test

```python
# tests/test_moondream_engine.py (add to existing file)

def test_moondream_engine_license_attribution():
    """MoondreamEngine includes license attribution."""
    engine = MoondreamEngine()
    attribution = engine.get_attribution()

    assert "Moondream 2" in attribution
    assert "Apache 2.0" in attribution
    assert "vikhyatk" in attribution or "moondream" in attribution.lower()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_engine.py::test_moondream_engine_license_attribution -v
```

**Step 3 - GREEN:** Add attribution method

```python
# src/syncopaid/moondream_engine.py (add method to class)

def get_attribution(self) -> str:
    """Return license attribution for Moondream 2.

    Returns:
        Attribution string for display in about/credits
    """
    return (
        "Screenshot analysis powered by Moondream 2\n"
        "Copyright (c) vikhyatk/M87 Labs\n"
        "Licensed under Apache 2.0\n"
        "https://github.com/vikhyat/moondream"
    )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_engine.py -v
```

---

## Final Verification

After all tasks complete:

```bash
# Run all tests
python -m pytest -v

# Run Moondream-specific tests
python -m pytest tests/test_moondream_engine.py -v

# Verify no network calls during inference (manual test with network disabled)
# 1. Disconnect network
# 2. Run: python -c "from syncopaid.moondream_engine import MoondreamEngine; e = MoondreamEngine(); print(e.is_available())"
# 3. Should return True if model is cached, False otherwise
```

## Acceptance Criteria Checklist

- [ ] `pytest tests/test_moondream_engine.py -v` passes
- [ ] `pytest tests/test_moondream_worker.py -v` passes
- [ ] Worker subprocess spawns on demand
- [ ] Worker loads model with float32 on CPU, float16 on GPU
- [ ] Worker can be killed to reclaim 4GB+ RAM
- [ ] Engine handles worker crashes gracefully
- [ ] OOM errors produce graceful AnalysisResult
- [ ] Engine is registered in vision_engine registry
- [ ] License attribution method exists
- [ ] Config settings added for Moondream

---

## Notes for Implementer

1. **Subprocess Architecture**: MoondreamEngine spawns a separate worker process to load the model. This keeps the main app lightweight (~50MB) and allows killing the worker to reclaim 4GB+ RAM when not needed.

2. **Model Download**: First run will download ~7.6GB from HuggingFace (full repository; ~3.85GB model weights loaded into RAM). Story 14.5 handles progress indicator and custom cache paths.

3. **Worker Communication**: Uses JSON over stdin/stdout. The worker signals "ready" when model is loaded, then processes analyze requests.

4. **Dependencies**: Ensure these are in requirements.txt:
   - transformers>=4.41.0
   - torch>=2.0.0
   - einops
   - pillow

5. **Testing Without GPU**: All tests mock CUDA detection and subprocess.Popen. Real GPU testing optional.

6. **Privacy**: No network calls occur during inference - model runs entirely offline after initial download.
