# Moondream 2 Integration (CPU-Friendly) - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 14.6.1 | **Created:** 2025-12-23 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Implement Moondream 2 as the local vision LLM engine for screenshot analysis on CPU-only systems (8GB RAM minimum).

**Approach:** Create a `MoondreamEngine` class implementing the `VisionEngine` interface from story 14.1. Use HuggingFace transformers with float32 precision for CPU compatibility. Implement image encoding cache for multiple queries per screenshot. Add graceful OOM handling.

**Tech Stack:** transformers, torch (CPU), einops, Pillow, existing VisionEngine interface (from 14.1), HardwareInfo (from 14.2)

---

## Story Context

**Title:** Moondream 2 Integration (CPU-Friendly)

**User Story:**
> As a user without a dedicated GPU, I want screenshot analysis powered by Moondream 2, so that I get local AI categorization on standard hardware (8GB RAM minimum).

**Acceptance Criteria:**
- [ ] Moondream 2 model loads successfully on CPU
- [ ] float32 precision used for CPU compatibility
- [ ] Image encoding cache for multiple queries per screenshot
- [ ] Inference completes within 25 seconds on minimum spec
- [ ] Graceful fallback on out-of-memory conditions
- [ ] Apache 2.0 license attribution included
- [ ] No network calls during inference (privacy compliance)

## Prerequisites

- [ ] Story 14.1 (Local LLM Engine Architecture) must be implemented - provides VisionEngine base class
- [ ] Story 14.2 (Hardware Detection & Model Selection) must be implemented - provides hardware info
- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_moondream_engine.py` | Create | Unit tests for Moondream integration |
| `src/syncopaid/moondream_engine.py` | Create | Moondream 2 engine implementation |
| `src/syncopaid/vision_engine.py` | Modify | Register Moondream engine |
| `src/syncopaid/config_defaults.py` | Modify | Add Moondream-specific config |
| `src/syncopaid/config_dataclass.py` | Modify | Add Moondream config fields |

## TDD Tasks

### Task 1: Create MoondreamEngine Class Skeleton (~3 min)

**Files:**
- Create: `tests/test_moondream_engine.py`
- Create: `src/syncopaid/moondream_engine.py`

**Context:** Moondream 2 is a 3.85GB vision model that runs on CPU with float32 precision. This task creates the engine class that implements VisionEngine interface. The model is loaded lazily on first use.

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


def test_moondream_engine_init_does_not_load_model():
    """MoondreamEngine does not load model during __init__."""
    engine = MoondreamEngine()
    assert engine._model is None
    assert engine._loaded is False


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
"""Moondream 2 vision engine for CPU-friendly screenshot analysis.

Implements the VisionEngine interface using Moondream 2, a 3.85GB
vision language model that runs on CPU with float32 precision.

Model: vikhyatk/moondream2 (Apache 2.0 license)
Requirements: 8GB RAM minimum, ~25 second inference on CPU
"""
from typing import Optional
from pathlib import Path

from syncopaid.vision_engine import VisionEngine, AnalysisResult


class MoondreamEngine(VisionEngine):
    """Moondream 2 vision engine for CPU screenshot analysis.

    Attributes:
        name: Engine identifier ("moondream2")
        _model: Lazy-loaded HuggingFace model
        _loaded: Whether model is currently loaded
    """

    name = "moondream2"

    def __init__(self):
        """Initialize engine without loading model."""
        self._model = None
        self._loaded = False

    def analyze(self, image_path: Path) -> AnalysisResult:
        """Analyze screenshot and return structured result."""
        raise NotImplementedError("Model loading not yet implemented")

    def is_available(self) -> bool:
        """Check if engine dependencies are available."""
        return False
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_engine.py -v
```

---

### Task 2: Implement Model Loading with CPU/GPU Detection (~5 min)

**Files:**
- Modify: `tests/test_moondream_engine.py`
- Modify: `src/syncopaid/moondream_engine.py`

**Context:** The model must use float32 on CPU (float16 causes LayerNormKernelImpl errors). Model revision pinned to "2025-06-21" for reproducibility. Loading uses trust_remote_code=True required by Moondream.

**Step 1 - RED:** Add failing tests

```python
# tests/test_moondream_engine.py (add to existing file)

@patch('syncopaid.moondream_engine.torch')
@patch('syncopaid.moondream_engine.AutoModelForCausalLM')
def test_moondream_engine_load_model_cpu(mock_model_class, mock_torch):
    """MoondreamEngine loads model with float32 on CPU."""
    mock_torch.cuda.is_available.return_value = False
    mock_torch.float32 = 'float32'
    mock_model = MagicMock()
    mock_model_class.from_pretrained.return_value = mock_model

    engine = MoondreamEngine()
    engine._load_model()

    mock_model_class.from_pretrained.assert_called_once()
    call_kwargs = mock_model_class.from_pretrained.call_args[1]
    assert call_kwargs['torch_dtype'] == 'float32'
    assert call_kwargs['trust_remote_code'] is True
    assert call_kwargs['revision'] == "2025-06-21"
    assert engine._loaded is True


@patch('syncopaid.moondream_engine.torch')
@patch('syncopaid.moondream_engine.AutoModelForCausalLM')
def test_moondream_engine_load_model_gpu(mock_model_class, mock_torch):
    """MoondreamEngine loads model with float16 on GPU."""
    mock_torch.cuda.is_available.return_value = True
    mock_torch.float16 = 'float16'
    mock_model = MagicMock()
    mock_model_class.from_pretrained.return_value = mock_model

    engine = MoondreamEngine()
    engine._load_model()

    call_kwargs = mock_model_class.from_pretrained.call_args[1]
    assert call_kwargs['torch_dtype'] == 'float16'
    assert call_kwargs['device_map'] == {"": "cuda"}
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_engine.py::test_moondream_engine_load_model_cpu -v
```

**Step 3 - GREEN:** Implement model loading

```python
# src/syncopaid/moondream_engine.py (replace class)
"""Moondream 2 vision engine for CPU-friendly screenshot analysis.

Implements the VisionEngine interface using Moondream 2, a 3.85GB
vision language model that runs on CPU with float32 precision.

Model: vikhyatk/moondream2 (Apache 2.0 license)
Requirements: 8GB RAM minimum, ~25 second inference on CPU
"""
import logging
from typing import Optional
from pathlib import Path

try:
    import torch
    from transformers import AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    torch = None
    AutoModelForCausalLM = None

from syncopaid.vision_engine import VisionEngine, AnalysisResult


MODEL_ID = "vikhyatk/moondream2"
MODEL_REVISION = "2025-06-21"


class MoondreamEngine(VisionEngine):
    """Moondream 2 vision engine for CPU screenshot analysis."""

    name = "moondream2"

    def __init__(self):
        """Initialize engine without loading model."""
        self._model = None
        self._loaded = False
        self._device = None
        self._dtype = None

    def _load_model(self) -> None:
        """Load Moondream 2 model with appropriate settings for CPU/GPU."""
        if self._loaded:
            return

        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("transformers library not installed")

        # Detect hardware and set appropriate dtype
        use_cuda = torch.cuda.is_available()
        self._device = "cuda" if use_cuda else "cpu"
        self._dtype = torch.float16 if use_cuda else torch.float32

        logging.info(f"Loading Moondream 2 on {self._device} with {self._dtype}")

        # Load model with pinned revision
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
        logging.info("Moondream 2 model loaded successfully")

    def analyze(self, image_path: Path) -> AnalysisResult:
        """Analyze screenshot and return structured result."""
        raise NotImplementedError("Analyze not yet implemented")

    def is_available(self) -> bool:
        """Check if engine dependencies are available."""
        return TRANSFORMERS_AVAILABLE
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_engine.py -v
```

---

### Task 3: Implement Image Encoding Cache (~4 min)

**Files:**
- Modify: `tests/test_moondream_engine.py`
- Modify: `src/syncopaid/moondream_engine.py`

**Context:** Moondream's encode_image() is expensive. Caching encoded images allows multiple queries per screenshot without re-encoding. Cache keyed by image path, cleared on analyze() completion.

**Step 1 - RED:** Add failing tests

```python
# tests/test_moondream_engine.py (add to existing file)

def test_moondream_engine_image_cache_init():
    """MoondreamEngine initializes with empty image cache."""
    engine = MoondreamEngine()
    assert engine._image_cache == {}


@patch('syncopaid.moondream_engine.Image')
@patch('syncopaid.moondream_engine.torch')
@patch('syncopaid.moondream_engine.AutoModelForCausalLM')
def test_moondream_engine_encode_image_cached(mock_model_class, mock_torch, mock_pil):
    """MoondreamEngine caches encoded images."""
    mock_torch.cuda.is_available.return_value = False
    mock_torch.float32 = 'float32'
    mock_model = MagicMock()
    mock_model.encode_image.return_value = "encoded_tensor"
    mock_model_class.from_pretrained.return_value = mock_model
    mock_image = MagicMock()
    mock_pil.open.return_value = mock_image

    engine = MoondreamEngine()
    engine._load_model()

    # First call should encode
    result1 = engine._get_encoded_image(Path("/test/image.png"))
    assert mock_model.encode_image.call_count == 1

    # Second call should use cache
    result2 = engine._get_encoded_image(Path("/test/image.png"))
    assert mock_model.encode_image.call_count == 1  # No additional call
    assert result1 == result2
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_engine.py::test_moondream_engine_encode_image_cached -v
```

**Step 3 - GREEN:** Implement image cache

```python
# src/syncopaid/moondream_engine.py (add imports and update class)

# Add to imports:
from PIL import Image

# Update __init__:
def __init__(self):
    """Initialize engine without loading model."""
    self._model = None
    self._loaded = False
    self._device = None
    self._dtype = None
    self._image_cache = {}

# Add method:
def _get_encoded_image(self, image_path: Path):
    """Get encoded image, using cache if available.

    Args:
        image_path: Path to image file

    Returns:
        Encoded image tensor for queries
    """
    cache_key = str(image_path)

    if cache_key in self._image_cache:
        return self._image_cache[cache_key]

    # Load and encode image
    image = Image.open(image_path)
    encoded = self._model.encode_image(image)

    # Cache for reuse
    self._image_cache[cache_key] = encoded
    return encoded

def _clear_cache(self) -> None:
    """Clear the image encoding cache."""
    self._image_cache.clear()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_engine.py -v
```

---

### Task 4: Implement analyze() Method (~5 min)

**Files:**
- Modify: `tests/test_moondream_engine.py`
- Modify: `src/syncopaid/moondream_engine.py`

**Context:** The analyze() method loads the image, encodes it, runs the query, and parses the response into AnalysisResult. It must handle the legal context prompt to extract activity type, description, and confidence.

**Step 1 - RED:** Add failing tests

```python
# tests/test_moondream_engine.py (add to existing file)
from syncopaid.vision_engine import AnalysisResult
from pathlib import Path

@patch('syncopaid.moondream_engine.Image')
@patch('syncopaid.moondream_engine.torch')
@patch('syncopaid.moondream_engine.AutoModelForCausalLM')
def test_moondream_engine_analyze_returns_result(mock_model_class, mock_torch, mock_pil):
    """MoondreamEngine.analyze() returns AnalysisResult."""
    mock_torch.cuda.is_available.return_value = False
    mock_torch.float32 = 'float32'
    mock_model = MagicMock()
    mock_model.encode_image.return_value = "encoded"
    mock_model.query.return_value = {"answer": "User is editing a legal document in Microsoft Word"}
    mock_model_class.from_pretrained.return_value = mock_model
    mock_pil.open.return_value = MagicMock()

    engine = MoondreamEngine()
    result = engine.analyze(Path("/test/screenshot.png"))

    assert isinstance(result, AnalysisResult)
    assert result.raw_output == "User is editing a legal document in Microsoft Word"
    assert result.confidence > 0


@patch('syncopaid.moondream_engine.Image')
@patch('syncopaid.moondream_engine.torch')
@patch('syncopaid.moondream_engine.AutoModelForCausalLM')
def test_moondream_engine_analyze_clears_cache(mock_model_class, mock_torch, mock_pil):
    """MoondreamEngine.analyze() clears cache after completion."""
    mock_torch.cuda.is_available.return_value = False
    mock_torch.float32 = 'float32'
    mock_model = MagicMock()
    mock_model.encode_image.return_value = "encoded"
    mock_model.query.return_value = {"answer": "Test output"}
    mock_model_class.from_pretrained.return_value = mock_model
    mock_pil.open.return_value = MagicMock()

    engine = MoondreamEngine()
    engine.analyze(Path("/test/image.png"))

    assert engine._image_cache == {}
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_engine.py::test_moondream_engine_analyze_returns_result -v
```

**Step 3 - GREEN:** Implement analyze()

```python
# src/syncopaid/moondream_engine.py (replace analyze method)

ANALYSIS_PROMPT = """Describe what the user is doing on this computer screen.
Focus on: the application being used, the type of work activity (e.g., document editing,
email, web browsing, legal research), and any visible document or file names.
Keep the description concise, under 50 words."""


def analyze(self, image_path: Path) -> AnalysisResult:
    """Analyze screenshot and return structured result.

    Args:
        image_path: Path to screenshot image file

    Returns:
        AnalysisResult with description, activity type, and confidence
    """
    try:
        # Ensure model is loaded
        self._load_model()

        # Get encoded image (cached)
        encoded = self._get_encoded_image(image_path)

        # Query the model
        response = self._model.query(encoded, ANALYSIS_PROMPT)
        raw_output = response.get("answer", "")

        # Parse response into structured result
        result = self._parse_response(raw_output)

        return result

    except Exception as e:
        logging.error(f"Moondream analysis failed: {e}")
        return AnalysisResult(
            description="Analysis failed",
            activity_type="unknown",
            confidence=0.0,
            raw_output=str(e)
        )
    finally:
        # Clear cache after analysis completes
        self._clear_cache()

def _parse_response(self, raw_output: str) -> AnalysisResult:
    """Parse model output into structured AnalysisResult.

    Args:
        raw_output: Raw text from model

    Returns:
        Structured AnalysisResult
    """
    # Extract activity type from common keywords
    activity_type = "general"
    raw_lower = raw_output.lower()

    if any(word in raw_lower for word in ["email", "outlook", "mail"]):
        activity_type = "email"
    elif any(word in raw_lower for word in ["document", "word", "editing", "writing"]):
        activity_type = "document_editing"
    elif any(word in raw_lower for word in ["browser", "chrome", "firefox", "web"]):
        activity_type = "web_browsing"
    elif any(word in raw_lower for word in ["research", "westlaw", "canlii", "legal"]):
        activity_type = "legal_research"
    elif any(word in raw_lower for word in ["excel", "spreadsheet"]):
        activity_type = "spreadsheet"

    # Confidence based on response length and specificity
    confidence = min(0.9, 0.5 + len(raw_output) / 200)

    return AnalysisResult(
        description=raw_output[:200],  # Truncate long descriptions
        activity_type=activity_type,
        confidence=confidence,
        raw_output=raw_output
    )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_engine.py -v
```

---

### Task 5: Implement OOM Error Handling (~3 min)

**Files:**
- Modify: `tests/test_moondream_engine.py`
- Modify: `src/syncopaid/moondream_engine.py`

**Context:** On systems with low RAM, model loading or inference may trigger OOM. Graceful fallback returns a failed AnalysisResult with helpful error message instead of crashing.

**Step 1 - RED:** Add failing tests

```python
# tests/test_moondream_engine.py (add to existing file)

@patch('syncopaid.moondream_engine.torch')
@patch('syncopaid.moondream_engine.AutoModelForCausalLM')
def test_moondream_engine_handles_oom_on_load(mock_model_class, mock_torch):
    """MoondreamEngine handles OOM during model loading."""
    mock_torch.cuda.is_available.return_value = False
    mock_torch.float32 = 'float32'
    mock_model_class.from_pretrained.side_effect = RuntimeError("CUDA out of memory")

    engine = MoondreamEngine()

    with pytest.raises(MemoryError) as exc_info:
        engine._load_model()

    assert "insufficient memory" in str(exc_info.value).lower()


@patch('syncopaid.moondream_engine.Image')
@patch('syncopaid.moondream_engine.torch')
@patch('syncopaid.moondream_engine.AutoModelForCausalLM')
def test_moondream_engine_analyze_handles_oom(mock_model_class, mock_torch, mock_pil):
    """MoondreamEngine.analyze() returns graceful result on OOM."""
    mock_torch.cuda.is_available.return_value = False
    mock_torch.float32 = 'float32'
    mock_model = MagicMock()
    mock_model.encode_image.side_effect = RuntimeError("out of memory")
    mock_model_class.from_pretrained.return_value = mock_model
    mock_pil.open.return_value = MagicMock()

    engine = MoondreamEngine()
    result = engine.analyze(Path("/test/image.png"))

    assert result.confidence == 0.0
    assert "memory" in result.raw_output.lower() or "failed" in result.description.lower()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_moondream_engine.py::test_moondream_engine_handles_oom_on_load -v
```

**Step 3 - GREEN:** Add OOM handling

```python
# src/syncopaid/moondream_engine.py (update _load_model)

def _load_model(self) -> None:
    """Load Moondream 2 model with appropriate settings for CPU/GPU.

    Raises:
        MemoryError: If system has insufficient memory to load model
        RuntimeError: If transformers library not available
    """
    if self._loaded:
        return

    if not TRANSFORMERS_AVAILABLE:
        raise RuntimeError("transformers library not installed")

    # Detect hardware and set appropriate dtype
    use_cuda = torch.cuda.is_available()
    self._device = "cuda" if use_cuda else "cpu"
    self._dtype = torch.float16 if use_cuda else torch.float32

    logging.info(f"Loading Moondream 2 on {self._device} with {self._dtype}")

    try:
        # Load model with pinned revision
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
        logging.info("Moondream 2 model loaded successfully")

    except RuntimeError as e:
        if "out of memory" in str(e).lower() or "cuda" in str(e).lower():
            raise MemoryError(
                f"Insufficient memory to load Moondream 2. "
                f"Requires 8GB RAM minimum. Error: {e}"
            ) from e
        raise
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_moondream_engine.py -v
```

---

### Task 6: Register Engine with Registry (~2 min)

**Files:**
- Modify: `tests/test_moondream_engine.py`
- Modify: `src/syncopaid/vision_engine.py`

**Context:** The VisionEngine registry (from story 14.1) needs to know about MoondreamEngine. Registration happens via decorator or explicit registration.

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

### Task 7: Add Config Settings for Moondream (~3 min)

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

    assert config.moondream_model_revision == "2025-06-21"
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
moondream_model_revision: str = "2025-06-21"
moondream_inference_timeout_seconds: int = 30
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config.py -v
```

---

### Task 8: Add Apache 2.0 License Attribution (~2 min)

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
- [ ] Model loads on CPU with float32
- [ ] Model loads on GPU with float16 (if available)
- [ ] Image encoding is cached for multiple queries
- [ ] OOM errors produce graceful AnalysisResult
- [ ] Engine is registered in vision_engine registry
- [ ] License attribution method exists
- [ ] Config settings added for Moondream

---

## Notes for Implementer

1. **Model Download**: First run will download ~3.85GB model from HuggingFace. Consider implementing progress indicator.

2. **Cache Location**: Model caches to `~/.cache/huggingface/` by default. Story 14.5 will handle custom cache paths.

3. **Dependencies**: Ensure these are in requirements.txt:
   - transformers>=4.41.0
   - torch>=2.0.0
   - einops
   - pillow

4. **Testing Without GPU**: All tests mock CUDA detection. Real GPU testing optional.

5. **Privacy**: No network calls occur during inference - model runs entirely offline after initial download.
