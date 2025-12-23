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
