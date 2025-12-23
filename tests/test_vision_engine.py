"""Tests for vision engine abstraction layer."""
import pytest
from pathlib import Path
from syncopaid.vision_engine import VisionEngine, AnalysisResult


def test_vision_engine_is_abstract():
    """VisionEngine cannot be instantiated directly."""
    with pytest.raises(TypeError):
        VisionEngine()


def test_analysis_result_dataclass():
    """AnalysisResult holds structured output from vision analysis."""
    result = AnalysisResult(
        description="User editing Word document",
        activity_type="document_editing",
        confidence=0.85,
        raw_output="User is editing a Word document..."
    )
    assert result.description == "User editing Word document"
    assert result.activity_type == "document_editing"
    assert result.confidence == 0.85
    assert result.raw_output == "User is editing a Word document..."


def test_engine_registry_starts_empty():
    """Engine registry starts with no registered engines."""
    from syncopaid.vision_engine import get_registered_engines, _registry
    _registry.clear()  # Reset for test isolation
    assert get_registered_engines() == {}


def test_register_engine():
    """Engines can be registered by name."""
    from syncopaid.vision_engine import register_engine, get_registered_engines, _registry
    _registry.clear()  # Reset for test isolation

    class MockEngine(VisionEngine):
        @property
        def name(self) -> str:
            return "Mock Engine"

        @property
        def model_id(self) -> str:
            return "mock/engine"

        def is_available(self) -> bool:
            return True

        def analyze(self, image_path, prompt=None):
            return AnalysisResult("mock", "mock", 1.0, "mock")

    register_engine("mock", MockEngine)
    engines = get_registered_engines()

    assert "mock" in engines
    assert engines["mock"] == MockEngine


def test_get_engine_by_name():
    """Can retrieve and instantiate engine by name."""
    from syncopaid.vision_engine import register_engine, get_engine, _registry
    _registry.clear()

    class MockEngine(VisionEngine):
        @property
        def name(self) -> str:
            return "Mock Engine"

        @property
        def model_id(self) -> str:
            return "mock/engine"

        def is_available(self) -> bool:
            return True

        def analyze(self, image_path, prompt=None):
            return AnalysisResult("mock", "mock", 1.0, "mock")

    register_engine("mock", MockEngine)
    engine = get_engine("mock")

    assert isinstance(engine, MockEngine)
    assert engine.name == "Mock Engine"


def test_get_nonexistent_engine_returns_none():
    """Getting a non-registered engine returns None."""
    from syncopaid.vision_engine import get_engine, _registry
    _registry.clear()

    assert get_engine("nonexistent") is None
