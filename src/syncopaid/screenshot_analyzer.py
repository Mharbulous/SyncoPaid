# src/syncopaid/screenshot_analyzer.py
"""AI-powered screenshot analysis for automatic context extraction."""
import json
import logging
import base64
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path


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
