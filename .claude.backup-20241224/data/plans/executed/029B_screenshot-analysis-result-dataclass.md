# 029B: Screenshot Analysis Result Dataclass
Story ID: 15.1

## Task
Create the AnalysisResult dataclass for representing screenshot analysis data.

## Context
This is the second sub-plan of 029 (Automatic Screenshot Analysis). Creates the data structure for storing and serializing screenshot analysis results.

## Scope
- Create `src/syncopaid/screenshot_analyzer.py` module
- Implement AnalysisResult dataclass with JSON serialization
- Unit tests for serialization/deserialization

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/screenshot_analyzer.py` | Create new module |
| `tests/test_screenshot_analyzer.py` | Create test file |

## TDD Tasks

### Task 1: Create AnalysisResult dataclass with JSON serialization

**Test first:**
```python
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
```

**Implementation:**
```python
# src/syncopaid/screenshot_analyzer.py
"""AI-powered screenshot analysis for automatic context extraction."""
import json
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class AnalysisResult:
    """Result of screenshot analysis."""
    application: Optional[str] = None
    document_name: Optional[str] = None
    case_numbers: List[str] = field(default_factory=list)
    email_subject: Optional[str] = None
    webpage_title: Optional[str] = None
    visible_text: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_json(self) -> str:
        """Serialize to JSON for database storage."""
        return json.dumps({
            'application': self.application,
            'document_name': self.document_name,
            'case_numbers': self.case_numbers,
            'email_subject': self.email_subject,
            'webpage_title': self.webpage_title,
            'visible_text': self.visible_text,
            'confidence': self.confidence
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'AnalysisResult':
        """Deserialize from JSON."""
        data = json.loads(json_str)
        return cls(
            application=data.get('application'),
            document_name=data.get('document_name'),
            case_numbers=data.get('case_numbers', []),
            email_subject=data.get('email_subject'),
            webpage_title=data.get('webpage_title'),
            visible_text=data.get('visible_text', []),
            confidence=float(data.get('confidence', 0.0))
        )
```

### Task 2: Handle edge cases in JSON parsing

**Test first:**
```python
def test_analysis_result_from_json_missing_fields():
    """Test from_json handles missing optional fields."""
    json_str = json.dumps({
        'application': 'Word',
        'confidence': 0.5
    })

    result = AnalysisResult.from_json(json_str)

    assert result.application == 'Word'
    assert result.document_name is None
    assert result.case_numbers == []
    assert result.confidence == 0.5


def test_analysis_result_from_json_empty_object():
    """Test from_json handles empty JSON object."""
    result = AnalysisResult.from_json('{}')

    assert result.application is None
    assert result.confidence == 0.0
    assert result.case_numbers == []
```

**Implementation:**
- The `from_json` method already uses `.get()` with defaults

## Verification

```bash
venv\Scripts\activate
pytest tests/test_screenshot_analyzer.py -v
python -c "from syncopaid.screenshot_analyzer import AnalysisResult; print('OK')"
```

## Notes
- Uses dataclass for clean, minimal boilerplate
- JSON serialization enables database storage in TEXT column
- confidence field ranges 0.0-1.0 for reliability indication
