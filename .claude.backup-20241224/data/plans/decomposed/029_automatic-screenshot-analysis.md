# 029: Automatic Screenshot Analysis
Story ID: 15.1

## Task
Add AI-powered screenshot analysis to extract contextual information from captured screenshots.

## Context
SyncoPaid already captures screenshots at regular intervals (screenshot.py). This story adds AI analysis to extract: application names, document/file names, visible case numbers, email subjects, and webpage titles from the captured images. This enables automatic time categorization without manual user input.

## Scope
- Create `src/syncopaid/screenshot_analyzer.py` module
- Add `analysis_data` column to screenshots table
- Integrate with existing ScreenshotWorker flow
- Queue screenshots for background AI analysis
- Store extracted data alongside timestamp and window title

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/screenshot_analyzer.py` | New module (CREATE) |
| `src/syncopaid/database_schema.py` | Add analysis_data column |
| `src/syncopaid/database_screenshots.py` | Add analysis methods |
| `src/syncopaid/screenshot_worker_actions.py` | Queue for analysis |
| `tests/test_screenshot_analyzer.py` | Create test file |

## Prerequisites
- Existing screenshot capture (already implemented)
- LLM API client (019A) should be implemented first
- Screenshots table exists with file_path, window_app, window_title

## Implementation

### 1. Database Migration

```python
# src/syncopaid/database_schema.py - Add to _create_screenshots_table()
# After existing screenshots table creation, add migration:
def _migrate_screenshots_table(self, cursor):
    """Apply migrations to screenshots table."""
    cursor.execute("PRAGMA table_info(screenshots)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'analysis_data' not in columns:
        cursor.execute("ALTER TABLE screenshots ADD COLUMN analysis_data TEXT")
        logging.info("Migration: Added analysis_data column to screenshots")

    if 'analysis_status' not in columns:
        cursor.execute("ALTER TABLE screenshots ADD COLUMN analysis_status TEXT DEFAULT 'pending'")
        logging.info("Migration: Added analysis_status column to screenshots")
```

### 2. Screenshot Analyzer Module

```python
# src/syncopaid/screenshot_analyzer.py (CREATE)
"""AI-powered screenshot analysis for automatic context extraction."""
import base64
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from PIL import Image
import io


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
        return cls(**data)


class ScreenshotAnalyzer:
    """
    Analyzes screenshots using vision-capable LLM.
    Extracts contextual information for time categorization.
    """

    def __init__(self, llm_client):
        """
        Initialize analyzer.

        Args:
            llm_client: LLM client with vision capabilities
        """
        self.llm_client = llm_client
        self._analysis_prompt = self._build_prompt()

    def _build_prompt(self) -> str:
        """Build the analysis prompt for vision LLM."""
        return """Analyze this screenshot from a lawyer's computer. Extract:
1. Application name visible
2. Document or file name if visible
3. Any case/matter numbers (format: YYYY BCSC 1234, Matter-123, etc.)
4. Email subject if this is an email
5. Webpage title if this is a browser
6. Key visible text that indicates work context

Respond in JSON:
{"application": "...", "document_name": "...", "case_numbers": [...], "email_subject": "...", "webpage_title": "...", "visible_text": [...], "confidence": 0.0-1.0}

Only include fields where information is visible. Confidence indicates how clearly the content is readable."""

    def analyze(self, image_path: Path) -> AnalysisResult:
        """
        Analyze a screenshot image.

        Args:
            image_path: Path to screenshot file

        Returns:
            AnalysisResult with extracted information
        """
        try:
            image_data = self._encode_image(image_path)
            response = self.llm_client.analyze_image(
                image_data=image_data,
                prompt=self._analysis_prompt
            )
            return self._parse_response(response)
        except Exception as e:
            logging.error(f"Screenshot analysis failed: {e}")
            return AnalysisResult(confidence=0.0)

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64 for API."""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def _parse_response(self, response: str) -> AnalysisResult:
        """Parse LLM response into AnalysisResult."""
        try:
            data = json.loads(response)
            return AnalysisResult(
                application=data.get('application'),
                document_name=data.get('document_name'),
                case_numbers=data.get('case_numbers', []),
                email_subject=data.get('email_subject'),
                webpage_title=data.get('webpage_title'),
                visible_text=data.get('visible_text', []),
                confidence=float(data.get('confidence', 0.0))
            )
        except json.JSONDecodeError:
            logging.warning("Failed to parse LLM response as JSON")
            return AnalysisResult(confidence=0.0)
```

### 3. Database Methods

```python
# src/syncopaid/database_screenshots.py - Add methods
def update_screenshot_analysis(
    self,
    screenshot_id: int,
    analysis_data: str,
    analysis_status: str = 'completed'
):
    """
    Update screenshot with analysis results.

    Args:
        screenshot_id: ID of screenshot record
        analysis_data: JSON string of analysis results
        analysis_status: 'pending', 'completed', or 'failed'
    """
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE screenshots
            SET analysis_data = ?, analysis_status = ?
            WHERE id = ?
        """, (analysis_data, analysis_status, screenshot_id))


def get_pending_analysis_screenshots(self, limit: int = 10) -> List[Dict]:
    """Get screenshots pending analysis."""
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_path, window_app, window_title
            FROM screenshots
            WHERE analysis_status = 'pending' OR analysis_status IS NULL
            ORDER BY captured_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
```

### 4. Tests

```python
# tests/test_screenshot_analyzer.py (CREATE)
"""Tests for screenshot analysis."""
import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from syncopaid.screenshot_analyzer import ScreenshotAnalyzer, AnalysisResult


def test_analysis_result_serialization():
    result = AnalysisResult(
        application='Microsoft Word',
        document_name='Contract-Draft.docx',
        case_numbers=['2024 BCSC 1234'],
        confidence=0.95
    )

    json_str = result.to_json()
    restored = AnalysisResult.from_json(json_str)

    assert restored.application == 'Microsoft Word'
    assert restored.document_name == 'Contract-Draft.docx'
    assert restored.case_numbers == ['2024 BCSC 1234']
    assert restored.confidence == 0.95


def test_analyzer_parse_response():
    mock_llm = MagicMock()
    analyzer = ScreenshotAnalyzer(mock_llm)

    response = json.dumps({
        'application': 'Chrome',
        'webpage_title': 'CanLII - Legal Research',
        'confidence': 0.9
    })

    result = analyzer._parse_response(response)

    assert result.application == 'Chrome'
    assert result.webpage_title == 'CanLII - Legal Research'
    assert result.confidence == 0.9


def test_analyzer_handles_invalid_json():
    mock_llm = MagicMock()
    analyzer = ScreenshotAnalyzer(mock_llm)

    result = analyzer._parse_response('not valid json')

    assert result.confidence == 0.0
    assert result.application is None


@patch('syncopaid.screenshot_analyzer.ScreenshotAnalyzer._encode_image')
def test_analyzer_analyze_success(mock_encode):
    mock_llm = MagicMock()
    mock_llm.analyze_image.return_value = json.dumps({
        'application': 'Word',
        'document_name': 'Brief.docx',
        'confidence': 0.85
    })
    mock_encode.return_value = 'base64data'

    analyzer = ScreenshotAnalyzer(mock_llm)
    result = analyzer.analyze(Path('/fake/path.jpg'))

    assert result.application == 'Word'
    assert result.document_name == 'Brief.docx'
    assert result.confidence == 0.85
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_screenshot_analyzer.py -v
python -c "from syncopaid.screenshot_analyzer import ScreenshotAnalyzer, AnalysisResult; print('OK')"
python -m syncopaid.database  # Verify migration runs
```

## Dependencies
- 019A: LLM API client (for vision-capable model)

## Notes
- Analysis runs asynchronously, not blocking screenshot capture
- Processing happens in background without interrupting user work
- Vision API required (Claude 3, GPT-4V) - configured separately
- Privacy: All processing local except LLM API call with image

## Next Steps
After this story: 15.2 (Night Processing Mode) or 15.4 (Intelligent Narrative Generation)
