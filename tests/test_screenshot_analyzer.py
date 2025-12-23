# tests/test_screenshot_analyzer.py
import pytest
import json
from syncopaid.screenshot_analyzer import AnalysisResult


def test_analysis_result_defaults():
    """Test AnalysisResult has sensible defaults."""
    result = AnalysisResult()

    assert result.application is None
    assert result.document_name is None
    assert result.case_numbers == []
    assert result.email_subject is None
    assert result.webpage_title is None
    assert result.visible_text == []
    assert result.confidence == 0.0


def test_analysis_result_to_json():
    """Test AnalysisResult serializes to JSON correctly."""
    result = AnalysisResult(
        application='Microsoft Word',
        document_name='Contract-Draft.docx',
        case_numbers=['2024 BCSC 1234'],
        confidence=0.95
    )

    json_str = result.to_json()
    data = json.loads(json_str)

    assert data['application'] == 'Microsoft Word'
    assert data['document_name'] == 'Contract-Draft.docx'
    assert data['case_numbers'] == ['2024 BCSC 1234']
    assert data['confidence'] == 0.95


def test_analysis_result_from_json():
    """Test AnalysisResult deserializes from JSON correctly."""
    json_str = json.dumps({
        'application': 'Chrome',
        'webpage_title': 'CanLII - Legal Research',
        'case_numbers': [],
        'visible_text': ['Search results'],
        'confidence': 0.9
    })

    result = AnalysisResult.from_json(json_str)

    assert result.application == 'Chrome'
    assert result.webpage_title == 'CanLII - Legal Research'
    assert result.confidence == 0.9


def test_analysis_result_roundtrip():
    """Test serialization roundtrip preserves data."""
    original = AnalysisResult(
        application='Microsoft Word',
        document_name='Contract-Draft.docx',
        case_numbers=['2024 BCSC 1234', 'Matter-456'],
        email_subject=None,
        webpage_title=None,
        visible_text=['Page 1', 'Draft'],
        confidence=0.95
    )

    json_str = original.to_json()
    restored = AnalysisResult.from_json(json_str)

    assert restored.application == original.application
    assert restored.document_name == original.document_name
    assert restored.case_numbers == original.case_numbers
    assert restored.confidence == original.confidence
    assert restored.visible_text == original.visible_text
