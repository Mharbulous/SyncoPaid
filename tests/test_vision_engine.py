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
