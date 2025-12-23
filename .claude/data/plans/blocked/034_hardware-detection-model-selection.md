# Hardware Detection & Model Selection - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 14.2 | **Created:** 2025-12-23 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Auto-detect GPU/CPU capabilities and recommend optimal vision LLM engine for the user's hardware.

**Approach:** Create a hardware detection module that probes CUDA availability, VRAM, CPU cores, and RAM. Use detection results to recommend the best engine from the registry. Integrate with config system for manual override.

**Tech Stack:** Python subprocess, ctypes, psutil, existing vision_engine registry (from 14.1), config system

---

## Story Context

**Title:** Hardware Detection & Model Selection

**Acceptance Criteria:**
- [ ] Detect CUDA availability and version
- [ ] Estimate available VRAM
- [ ] Detect CPU capabilities (cores, RAM)
- [ ] Recommend appropriate model based on hardware
- [ ] Allow manual override in settings
- [ ] Display hardware detection results in UI

## Prerequisites

- [ ] Story 14.1 (Local LLM Engine Architecture) must be implemented
- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_hardware_detection.py` | Create | Unit tests for hardware detection |
| `src/syncopaid/hardware_detection.py` | Create | Hardware detection logic |
| `src/syncopaid/config_defaults.py` | Modify | Add hardware override settings |
| `src/syncopaid/config_dataclass.py` | Modify | Add hardware config fields |

## TDD Tasks

### Task 1: Create Hardware Info Dataclass (~2 min)

**Files:**
- Create: `tests/test_hardware_detection.py`
- Create: `src/syncopaid/hardware_detection.py`

**Context:** A dataclass to hold detected hardware specs - GPU, VRAM, CPU cores, RAM. This forms the foundation for model recommendations.

**Step 1 - RED:** Write failing test

```python
# tests/test_hardware_detection.py
"""Tests for hardware detection module."""
import pytest
from syncopaid.hardware_detection import HardwareInfo


def test_hardware_info_dataclass():
    """HardwareInfo holds detected hardware specifications."""
    info = HardwareInfo(
        cuda_available=True,
        cuda_version="12.1",
        gpu_name="NVIDIA RTX 3060",
        vram_mb=12288,
        cpu_cores=8,
        ram_mb=32768
    )
    assert info.cuda_available is True
    assert info.cuda_version == "12.1"
    assert info.gpu_name == "NVIDIA RTX 3060"
    assert info.vram_mb == 12288
    assert info.cpu_cores == 8
    assert info.ram_mb == 32768


def test_hardware_info_cpu_only():
    """HardwareInfo can represent CPU-only systems."""
    info = HardwareInfo(
        cuda_available=False,
        cuda_version=None,
        gpu_name=None,
        vram_mb=0,
        cpu_cores=4,
        ram_mb=16384
    )
    assert info.cuda_available is False
    assert info.cuda_version is None
    assert info.gpu_name is None
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_hardware_detection.py -v
```
Expected output: `FAILED` (module syncopaid.hardware_detection not found)

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/hardware_detection.py
"""Hardware detection for optimal vision engine selection.

Detects GPU capabilities, VRAM, CPU cores, and RAM to recommend
the best vision LLM engine configuration.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class HardwareInfo:
    """Detected hardware specifications.

    Attributes:
        cuda_available: Whether CUDA-capable GPU is available
        cuda_version: CUDA version string (e.g., "12.1") or None
        gpu_name: GPU model name (e.g., "NVIDIA RTX 3060") or None
        vram_mb: Available GPU VRAM in megabytes (0 if no GPU)
        cpu_cores: Number of CPU cores
        ram_mb: Available system RAM in megabytes
    """
    cuda_available: bool
    cuda_version: Optional[str]
    gpu_name: Optional[str]
    vram_mb: int
    cpu_cores: int
    ram_mb: int
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_hardware_detection.py -v
```
Expected output: `PASSED` (both tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_hardware_detection.py src/syncopaid/hardware_detection.py && git commit -m "feat: add HardwareInfo dataclass for hardware detection"
```

---

### Task 2: Add CPU Detection (~3 min)

**Files:**
- Modify: `tests/test_hardware_detection.py`
- Modify: `src/syncopaid/hardware_detection.py`

**Context:** Detect CPU cores and RAM using psutil (already in requirements). This works on all systems and provides baseline info.

**Step 1 - RED:** Write failing test

```python
# tests/test_hardware_detection.py (append)

def test_detect_cpu_info():
    """detect_cpu_info returns CPU cores and RAM."""
    from syncopaid.hardware_detection import detect_cpu_info

    cores, ram_mb = detect_cpu_info()

    # Should return positive values on any system
    assert cores >= 1
    assert ram_mb >= 1024  # At least 1GB RAM expected
    assert isinstance(cores, int)
    assert isinstance(ram_mb, int)
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_hardware_detection.py::test_detect_cpu_info -v
```
Expected output: `FAILED` (no function detect_cpu_info)

**Step 3 - GREEN:** Add CPU detection function

```python
# src/syncopaid/hardware_detection.py (append after HardwareInfo class)
import psutil


def detect_cpu_info() -> tuple[int, int]:
    """Detect CPU cores and available RAM.

    Returns:
        Tuple of (cpu_cores, ram_mb)
    """
    cpu_cores = psutil.cpu_count(logical=True) or 1
    ram_bytes = psutil.virtual_memory().total
    ram_mb = int(ram_bytes / (1024 * 1024))

    return cpu_cores, ram_mb
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_hardware_detection.py -v
```
Expected output: `PASSED` (all tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_hardware_detection.py src/syncopaid/hardware_detection.py && git commit -m "feat: add CPU and RAM detection using psutil"
```

---

### Task 3: Add CUDA Detection (~4 min)

**Files:**
- Modify: `tests/test_hardware_detection.py`
- Modify: `src/syncopaid/hardware_detection.py`

**Context:** Detect CUDA availability by checking for nvidia-smi command. This is the most reliable cross-platform method that doesn't require CUDA toolkit installed.

**Step 1 - RED:** Write failing test

```python
# tests/test_hardware_detection.py (append)

def test_detect_gpu_info_returns_tuple():
    """detect_gpu_info returns expected tuple structure."""
    from syncopaid.hardware_detection import detect_gpu_info

    result = detect_gpu_info()

    # Should return (cuda_available, cuda_version, gpu_name, vram_mb)
    assert len(result) == 4
    cuda_available, cuda_version, gpu_name, vram_mb = result

    assert isinstance(cuda_available, bool)
    # cuda_version is str or None
    assert cuda_version is None or isinstance(cuda_version, str)
    # gpu_name is str or None
    assert gpu_name is None or isinstance(gpu_name, str)
    assert isinstance(vram_mb, int)
    assert vram_mb >= 0


def test_detect_gpu_info_no_gpu_graceful():
    """detect_gpu_info handles missing nvidia-smi gracefully."""
    from syncopaid.hardware_detection import detect_gpu_info
    from unittest.mock import patch

    # Mock subprocess to simulate no nvidia-smi
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()

        cuda_available, cuda_version, gpu_name, vram_mb = detect_gpu_info()

        assert cuda_available is False
        assert cuda_version is None
        assert gpu_name is None
        assert vram_mb == 0
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_hardware_detection.py::test_detect_gpu_info_returns_tuple -v
```
Expected output: `FAILED` (no function detect_gpu_info)

**Step 3 - GREEN:** Add GPU detection function

```python
# src/syncopaid/hardware_detection.py (append after detect_cpu_info)
import subprocess
import re


def detect_gpu_info() -> tuple[bool, Optional[str], Optional[str], int]:
    """Detect NVIDIA GPU and CUDA capabilities.

    Uses nvidia-smi command which is available on any system with
    NVIDIA drivers installed. Does not require CUDA toolkit.

    Returns:
        Tuple of (cuda_available, cuda_version, gpu_name, vram_mb)
    """
    try:
        # Query GPU info using nvidia-smi
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,driver_version',
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return False, None, None, 0

        output = result.stdout.strip()
        if not output:
            return False, None, None, 0

        # Parse: "NVIDIA GeForce RTX 3060, 12288, 535.154.05"
        parts = output.split(',')
        if len(parts) >= 3:
            gpu_name = parts[0].strip()
            vram_mb = int(float(parts[1].strip()))
            driver_version = parts[2].strip()

            # Get CUDA version from nvidia-smi header
            cuda_version = _get_cuda_version()

            return True, cuda_version, gpu_name, vram_mb

        return False, None, None, 0

    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False, None, None, 0


def _get_cuda_version() -> Optional[str]:
    """Extract CUDA version from nvidia-smi."""
    try:
        result = subprocess.run(
            ['nvidia-smi'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            # Look for "CUDA Version: 12.1"
            match = re.search(r'CUDA Version:\s*(\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)

        return None
    except Exception:
        return None
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_hardware_detection.py -v
```
Expected output: `PASSED` (all tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_hardware_detection.py src/syncopaid/hardware_detection.py && git commit -m "feat: add CUDA/GPU detection via nvidia-smi"
```

---

### Task 4: Add Full Hardware Detection Function (~2 min)

**Files:**
- Modify: `tests/test_hardware_detection.py`
- Modify: `src/syncopaid/hardware_detection.py`

**Context:** Combine CPU and GPU detection into a single function that returns HardwareInfo.

**Step 1 - RED:** Write failing test

```python
# tests/test_hardware_detection.py (append)

def test_detect_hardware():
    """detect_hardware returns complete HardwareInfo."""
    from syncopaid.hardware_detection import detect_hardware, HardwareInfo

    info = detect_hardware()

    assert isinstance(info, HardwareInfo)
    assert info.cpu_cores >= 1
    assert info.ram_mb >= 1024


def test_detect_hardware_caches_result():
    """detect_hardware caches result for performance."""
    from syncopaid.hardware_detection import detect_hardware, _hardware_cache

    # Clear any existing cache
    _hardware_cache.clear()

    info1 = detect_hardware()
    info2 = detect_hardware()

    # Should be the same cached object
    assert info1 is info2
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_hardware_detection.py::test_detect_hardware -v
```
Expected output: `FAILED` (no function detect_hardware)

**Step 3 - GREEN:** Add detect_hardware function

```python
# src/syncopaid/hardware_detection.py (append at end)

# Cache for hardware detection (doesn't change during runtime)
_hardware_cache: dict[str, HardwareInfo] = {}


def detect_hardware(force_refresh: bool = False) -> HardwareInfo:
    """Detect all hardware capabilities.

    Results are cached since hardware doesn't change during runtime.

    Args:
        force_refresh: If True, bypass cache and re-detect

    Returns:
        HardwareInfo with all detected specs
    """
    cache_key = "current"

    if not force_refresh and cache_key in _hardware_cache:
        return _hardware_cache[cache_key]

    # Detect CPU/RAM
    cpu_cores, ram_mb = detect_cpu_info()

    # Detect GPU/CUDA
    cuda_available, cuda_version, gpu_name, vram_mb = detect_gpu_info()

    info = HardwareInfo(
        cuda_available=cuda_available,
        cuda_version=cuda_version,
        gpu_name=gpu_name,
        vram_mb=vram_mb,
        cpu_cores=cpu_cores,
        ram_mb=ram_mb
    )

    _hardware_cache[cache_key] = info
    return info
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_hardware_detection.py -v
```
Expected output: `PASSED` (all tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_hardware_detection.py src/syncopaid/hardware_detection.py && git commit -m "feat: add detect_hardware function with caching"
```

---

### Task 5: Add Engine Recommendation Logic (~4 min)

**Files:**
- Modify: `tests/test_hardware_detection.py`
- Modify: `src/syncopaid/hardware_detection.py`

**Context:** Based on detected hardware, recommend the best available vision engine. Uses thresholds to match hardware to engine requirements.

**Step 1 - RED:** Write failing test

```python
# tests/test_hardware_detection.py (append)

def test_recommend_engine_cpu_only():
    """recommend_engine returns CPU-friendly engine for non-GPU systems."""
    from syncopaid.hardware_detection import recommend_engine, HardwareInfo

    cpu_only = HardwareInfo(
        cuda_available=False,
        cuda_version=None,
        gpu_name=None,
        vram_mb=0,
        cpu_cores=4,
        ram_mb=16384
    )

    recommendation = recommend_engine(cpu_only)

    assert recommendation.engine_id == "moondream2"
    assert "CPU" in recommendation.reason


def test_recommend_engine_low_vram_gpu():
    """recommend_engine recommends CPU mode for low VRAM GPUs."""
    from syncopaid.hardware_detection import recommend_engine, HardwareInfo

    low_vram = HardwareInfo(
        cuda_available=True,
        cuda_version="12.1",
        gpu_name="NVIDIA GTX 1050",
        vram_mb=2048,  # 2GB - too low for most vision models
        cpu_cores=4,
        ram_mb=16384
    )

    recommendation = recommend_engine(low_vram)

    # Should recommend CPU mode despite having GPU
    assert "moondream2" in recommendation.engine_id
    assert "VRAM" in recommendation.reason or "CPU" in recommendation.reason


def test_recommend_engine_high_vram_gpu():
    """recommend_engine recommends GPU mode for high VRAM GPUs."""
    from syncopaid.hardware_detection import recommend_engine, HardwareInfo

    high_vram = HardwareInfo(
        cuda_available=True,
        cuda_version="12.1",
        gpu_name="NVIDIA RTX 3080",
        vram_mb=10240,  # 10GB - plenty for vision models
        cpu_cores=8,
        ram_mb=32768
    )

    recommendation = recommend_engine(high_vram)

    # Should recommend GPU-accelerated model
    assert "GPU" in recommendation.reason or "CUDA" in recommendation.reason


def test_engine_recommendation_dataclass():
    """EngineRecommendation holds recommendation details."""
    from syncopaid.hardware_detection import EngineRecommendation

    rec = EngineRecommendation(
        engine_id="moondream2",
        reason="CPU-only system, Moondream 2 runs efficiently on CPU",
        confidence="high"
    )

    assert rec.engine_id == "moondream2"
    assert "CPU" in rec.reason
    assert rec.confidence == "high"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_hardware_detection.py::test_recommend_engine_cpu_only -v
```
Expected output: `FAILED` (no function recommend_engine)

**Step 3 - GREEN:** Add recommendation logic

```python
# src/syncopaid/hardware_detection.py (add after HardwareInfo class)

@dataclass
class EngineRecommendation:
    """Recommendation for which vision engine to use.

    Attributes:
        engine_id: ID of recommended engine (e.g., "moondream2", "moondream3")
        reason: Human-readable explanation of why this was chosen
        confidence: "high", "medium", or "low" based on certainty
    """
    engine_id: str
    reason: str
    confidence: str


# Hardware thresholds for model selection
VRAM_THRESHOLD_GPU_MOONDREAM3 = 6144  # 6GB for GPU-accelerated Moondream 3
VRAM_THRESHOLD_GPU_MOONDREAM2 = 4096  # 4GB for GPU-accelerated Moondream 2
RAM_THRESHOLD_CPU = 8192  # 8GB RAM for CPU inference


def recommend_engine(hardware: HardwareInfo) -> EngineRecommendation:
    """Recommend the best vision engine based on detected hardware.

    Decision tree:
    1. If CUDA + 6GB+ VRAM → moondream3 (GPU mode)
    2. If CUDA + 4GB+ VRAM → moondream2 (GPU mode)
    3. If 8GB+ RAM → moondream2 (CPU mode)
    4. Fallback → moondream2 (CPU mode, may be slow)

    Args:
        hardware: Detected hardware specs

    Returns:
        EngineRecommendation with engine_id, reason, confidence
    """
    # Check for high VRAM GPU
    if hardware.cuda_available and hardware.vram_mb >= VRAM_THRESHOLD_GPU_MOONDREAM3:
        return EngineRecommendation(
            engine_id="moondream3",
            reason=f"GPU detected ({hardware.gpu_name}) with {hardware.vram_mb}MB VRAM - "
                   f"using GPU-accelerated Moondream 3 for best performance",
            confidence="high"
        )

    # Check for medium VRAM GPU
    if hardware.cuda_available and hardware.vram_mb >= VRAM_THRESHOLD_GPU_MOONDREAM2:
        return EngineRecommendation(
            engine_id="moondream2-gpu",
            reason=f"GPU detected ({hardware.gpu_name}) with {hardware.vram_mb}MB VRAM - "
                   f"using GPU-accelerated Moondream 2",
            confidence="high"
        )

    # Check for adequate RAM for CPU mode
    if hardware.ram_mb >= RAM_THRESHOLD_CPU:
        reason = "CPU-only system" if not hardware.cuda_available else \
                 f"GPU VRAM ({hardware.vram_mb}MB) too low for GPU acceleration"
        return EngineRecommendation(
            engine_id="moondream2",
            reason=f"{reason} - using Moondream 2 in CPU mode ({hardware.ram_mb}MB RAM available)",
            confidence="high"
        )

    # Fallback - low resources but we can try
    return EngineRecommendation(
        engine_id="moondream2",
        reason=f"Limited resources ({hardware.ram_mb}MB RAM) - "
               f"using Moondream 2 in CPU mode (may be slow)",
        confidence="low"
    )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_hardware_detection.py -v
```
Expected output: `PASSED` (all tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_hardware_detection.py src/syncopaid/hardware_detection.py && git commit -m "feat: add engine recommendation based on hardware detection"
```

---

### Task 6: Add Config Settings for Manual Override (~3 min)

**Files:**
- Modify: `tests/test_config.py`
- Modify: `src/syncopaid/config_defaults.py`
- Modify: `src/syncopaid/config_dataclass.py`

**Context:** Add config settings to allow manual engine selection, overriding auto-detection.

**Step 1 - RED:** Write failing test

```python
# tests/test_config.py (append at end of file)

def test_vision_engine_config_defaults():
    """Vision engine settings exist in DEFAULT_CONFIG."""
    from syncopaid.config_defaults import DEFAULT_CONFIG

    assert "vision_engine_enabled" in DEFAULT_CONFIG
    assert "vision_engine" in DEFAULT_CONFIG
    assert "vision_engine_auto_select" in DEFAULT_CONFIG

    assert DEFAULT_CONFIG["vision_engine_enabled"] is False  # Off until model downloaded
    assert DEFAULT_CONFIG["vision_engine"] == "moondream2"   # Default engine
    assert DEFAULT_CONFIG["vision_engine_auto_select"] is True  # Auto-select by default


def test_config_dataclass_has_vision_engine_fields():
    """Config dataclass includes vision engine fields."""
    from syncopaid.config_dataclass import Config

    config = Config()

    assert hasattr(config, 'vision_engine_enabled')
    assert hasattr(config, 'vision_engine')
    assert hasattr(config, 'vision_engine_auto_select')

    assert config.vision_engine_enabled is False
    assert config.vision_engine == "moondream2"
    assert config.vision_engine_auto_select is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config.py::test_vision_engine_config_defaults -v
```
Expected output: `FAILED` (vision_engine_enabled not in DEFAULT_CONFIG)

**Step 3 - GREEN:** Add config settings

```python
# src/syncopaid/config_defaults.py (add at end before closing brace)
    # Vision engine settings (local LLM for screenshot analysis)
    "vision_engine_enabled": False,       # Disabled until model downloaded
    "vision_engine": "moondream2",        # Default/selected engine
    "vision_engine_auto_select": True,    # Auto-select based on hardware
```

```python
# src/syncopaid/config_dataclass.py (add after night_processing fields, before to_dict)
    # Vision engine settings
    vision_engine_enabled: bool = False
    vision_engine: str = "moondream2"
    vision_engine_auto_select: bool = True
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config.py -v
```
Expected output: `PASSED` (all tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_config.py src/syncopaid/config_defaults.py src/syncopaid/config_dataclass.py && git commit -m "feat: add vision engine config settings with auto-select option"
```

---

### Task 7: Add get_effective_engine Function (~3 min)

**Files:**
- Modify: `tests/test_hardware_detection.py`
- Modify: `src/syncopaid/hardware_detection.py`

**Context:** Function that respects config override while falling back to auto-detection.

**Step 1 - RED:** Write failing test

```python
# tests/test_hardware_detection.py (append)

def test_get_effective_engine_with_auto_select():
    """get_effective_engine uses recommendation when auto_select is True."""
    from syncopaid.hardware_detection import get_effective_engine
    from unittest.mock import MagicMock

    mock_config = MagicMock()
    mock_config.vision_engine_auto_select = True
    mock_config.vision_engine = "some_other_engine"

    # Should use auto-detection, not config value
    result = get_effective_engine(mock_config)

    assert result.engine_id is not None
    # When auto-selecting, should not necessarily match config value


def test_get_effective_engine_with_manual_override():
    """get_effective_engine uses config value when auto_select is False."""
    from syncopaid.hardware_detection import get_effective_engine
    from unittest.mock import MagicMock

    mock_config = MagicMock()
    mock_config.vision_engine_auto_select = False
    mock_config.vision_engine = "custom_engine"

    result = get_effective_engine(mock_config)

    assert result.engine_id == "custom_engine"
    assert "manual" in result.reason.lower() or "override" in result.reason.lower()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_hardware_detection.py::test_get_effective_engine_with_auto_select -v
```
Expected output: `FAILED` (no function get_effective_engine)

**Step 3 - GREEN:** Add get_effective_engine function

```python
# src/syncopaid/hardware_detection.py (append at end)
from typing import Any


def get_effective_engine(config: Any) -> EngineRecommendation:
    """Get the engine to use, respecting config override.

    If auto_select is True, uses hardware detection to recommend engine.
    If auto_select is False, uses the manually configured engine.

    Args:
        config: Config object with vision_engine_auto_select and vision_engine

    Returns:
        EngineRecommendation with the effective engine to use
    """
    if config.vision_engine_auto_select:
        hardware = detect_hardware()
        return recommend_engine(hardware)
    else:
        return EngineRecommendation(
            engine_id=config.vision_engine,
            reason=f"Manual override: using '{config.vision_engine}' as configured",
            confidence="high"
        )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_hardware_detection.py -v
```
Expected output: `PASSED` (all tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_hardware_detection.py src/syncopaid/hardware_detection.py && git commit -m "feat: add get_effective_engine respecting config override"
```

---

### Task 8: Add Hardware Info Formatting for UI (~2 min)

**Files:**
- Modify: `tests/test_hardware_detection.py`
- Modify: `src/syncopaid/hardware_detection.py`

**Context:** Format hardware info as human-readable string for display in UI/logs.

**Step 1 - RED:** Write failing test

```python
# tests/test_hardware_detection.py (append)

def test_hardware_info_to_display_string_with_gpu():
    """HardwareInfo formats nicely for display with GPU."""
    from syncopaid.hardware_detection import HardwareInfo

    info = HardwareInfo(
        cuda_available=True,
        cuda_version="12.1",
        gpu_name="NVIDIA RTX 3060",
        vram_mb=12288,
        cpu_cores=8,
        ram_mb=32768
    )

    display = info.to_display_string()

    assert "RTX 3060" in display
    assert "12GB" in display or "12288" in display
    assert "CUDA 12.1" in display
    assert "8 cores" in display or "8" in display
    assert "32GB" in display or "32768" in display


def test_hardware_info_to_display_string_cpu_only():
    """HardwareInfo formats nicely for CPU-only systems."""
    from syncopaid.hardware_detection import HardwareInfo

    info = HardwareInfo(
        cuda_available=False,
        cuda_version=None,
        gpu_name=None,
        vram_mb=0,
        cpu_cores=4,
        ram_mb=16384
    )

    display = info.to_display_string()

    assert "No GPU" in display or "CPU only" in display
    assert "4 cores" in display or "4" in display
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_hardware_detection.py::test_hardware_info_to_display_string_with_gpu -v
```
Expected output: `FAILED` (HardwareInfo has no method to_display_string)

**Step 3 - GREEN:** Add to_display_string method to HardwareInfo

```python
# src/syncopaid/hardware_detection.py (add method to HardwareInfo class)

    def to_display_string(self) -> str:
        """Format hardware info for UI display.

        Returns:
            Human-readable multi-line string describing hardware
        """
        lines = []

        if self.cuda_available:
            gpu_ram = f"{self.vram_mb // 1024}GB" if self.vram_mb >= 1024 else f"{self.vram_mb}MB"
            lines.append(f"GPU: {self.gpu_name} ({gpu_ram} VRAM)")
            lines.append(f"CUDA: {self.cuda_version}")
        else:
            lines.append("GPU: No GPU detected (CPU only)")

        sys_ram = f"{self.ram_mb // 1024}GB" if self.ram_mb >= 1024 else f"{self.ram_mb}MB"
        lines.append(f"CPU: {self.cpu_cores} cores, {sys_ram} RAM")

        return "\n".join(lines)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_hardware_detection.py -v
```
Expected output: `PASSED` (all tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_hardware_detection.py src/syncopaid/hardware_detection.py && git commit -m "feat: add to_display_string for hardware info UI display"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest -v                          # All tests pass
python -c "from syncopaid.hardware_detection import detect_hardware, recommend_engine; hw = detect_hardware(); print(hw.to_display_string()); print(recommend_engine(hw))"
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- This story builds on 14.1 (VisionEngine registry) but can be implemented independently
- Actual model integration (Moondream 2/3) is in story 14.6.1
- The recommendation logic uses conservative thresholds to avoid OOM issues
- nvidia-smi approach works without CUDA toolkit installed
- Consider adding AMD ROCm detection in future if needed
