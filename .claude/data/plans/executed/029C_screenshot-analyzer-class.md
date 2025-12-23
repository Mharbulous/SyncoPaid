# 029C: Screenshot Analyzer Class
Story ID: 15.1

## Task
Create the ScreenshotAnalyzer class that uses LLM vision API to analyze screenshots.

## Context
This is the third sub-plan of 029 (Automatic Screenshot Analysis). Implements the analyzer class that encodes images and calls the LLM client.

## Scope
- Add ScreenshotAnalyzer class to screenshot_analyzer.py
- Implement image encoding to base64
- Implement LLM response parsing
- Handle errors gracefully

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/screenshot_analyzer.py` | Add ScreenshotAnalyzer class |
| `tests/test_screenshot_analyzer.py` | Add analyzer tests |

## TDD Tasks

### Task 1: Create ScreenshotAnalyzer with LLM response parsing

**Test first:**
```python
# tests/test_screenshot_analyzer.py - Add to existing file
import json
from unittest.mock import MagicMock
from syncopaid.screenshot_analyzer import ScreenshotAnalyzer


def test_analyzer_parse_response_valid():
    """Test parsing valid LLM JSON response."""
    mock_llm = MagicMock()
    analyzer = ScreenshotAnalyzer(mock_llm)

    response = json.dumps({
        'application': 'Chrome',
        'webpage_title': 'CanLII - Legal Research',
        'case_numbers': ['2024 BCSC 100'],
        'confidence': 0.9
    })

    result = analyzer._parse_response(response)

    assert result.application == 'Chrome'
    assert result.webpage_title == 'CanLII - Legal Research'
    assert result.case_numbers == ['2024 BCSC 100']
    assert result.confidence == 0.9


def test_analyzer_parse_response_invalid_json():
    """Test handling of invalid JSON response."""
    mock_llm = MagicMock()
    analyzer = ScreenshotAnalyzer(mock_llm)

    result = analyzer._parse_response('not valid json at all')

    assert result.confidence == 0.0
    assert result.application is None


def test_analyzer_parse_response_partial():
    """Test parsing response with only some fields."""
    mock_llm = MagicMock()
    analyzer = ScreenshotAnalyzer(mock_llm)

    response = json.dumps({
        'application': 'Word',
        'confidence': 0.7
    })

    result = analyzer._parse_response(response)

    assert result.application == 'Word'
    assert result.document_name is None
    assert result.confidence == 0.7
```

**Implementation:**
```python
# src/syncopaid/screenshot_analyzer.py - Add to existing file
import logging


class ScreenshotAnalyzer:
    """
    Analyzes screenshots using vision-capable LLM.
    Extracts contextual information for time categorization.
    """

    def __init__(self, llm_client):
        """
        Initialize analyzer.

        Args:
            llm_client: LLM client with vision capabilities (analyze_image method)
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

### Task 2: Implement image encoding and analyze method

**Test first:**
```python
from unittest.mock import patch
from pathlib import Path


@patch('syncopaid.screenshot_analyzer.ScreenshotAnalyzer._encode_image')
def test_analyzer_analyze_success(mock_encode):
    """Test successful screenshot analysis."""
    mock_llm = MagicMock()
    mock_llm.analyze_image.return_value = json.dumps({
        'application': 'Word',
        'document_name': 'Brief.docx',
        'confidence': 0.85
    })
    mock_encode.return_value = 'base64imagedata'

    analyzer = ScreenshotAnalyzer(mock_llm)
    result = analyzer.analyze(Path('/fake/path.jpg'))

    assert result.application == 'Word'
    assert result.document_name == 'Brief.docx'
    assert result.confidence == 0.85
    mock_llm.analyze_image.assert_called_once()


@patch('syncopaid.screenshot_analyzer.ScreenshotAnalyzer._encode_image')
def test_analyzer_analyze_llm_error(mock_encode):
    """Test analyzer handles LLM errors gracefully."""
    mock_llm = MagicMock()
    mock_llm.analyze_image.side_effect = Exception("API error")
    mock_encode.return_value = 'base64data'

    analyzer = ScreenshotAnalyzer(mock_llm)
    result = analyzer.analyze(Path('/fake/path.jpg'))

    assert result.confidence == 0.0
    assert result.application is None
```

**Implementation:**
```python
# Add to ScreenshotAnalyzer class
import base64
from pathlib import Path


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
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_screenshot_analyzer.py -v -k "analyzer"
python -c "from syncopaid.screenshot_analyzer import ScreenshotAnalyzer; print('OK')"
```

## Notes
- LLM client interface: must have `analyze_image(image_data, prompt)` method
- Base64 encoding for API transmission
- Graceful error handling returns empty result with 0.0 confidence
