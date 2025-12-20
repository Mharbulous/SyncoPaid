# 049: LLM & AI Integration - API Client

## Task
Create the LLM API client for activity classification using OpenAI/Anthropic APIs.

## Context
Creates the interface for calling LLM APIs to classify activities. Uses mocking for tests to avoid API calls during development.

## Scope
- Create `src/syncopaid/llm.py` module
- LLMClient class with classify_activity() method
- Support for OpenAI/Anthropic providers
- API key configuration

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/llm.py` | New module (CREATE) |
| `tests/test_llm.py` | Create test file |

## Prerequisites
- LLM API key configured (OpenAI or Anthropic)
- Story 8.1 (Matter/Client Database) should be implemented

## Implementation

```python
# src/syncopaid/llm.py (CREATE)
"""LLM API client for activity classification and narrative generation."""
import json
import logging
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    """Result of LLM activity classification."""
    matter_code: Optional[str]
    narrative: str
    confidence: float


class LLMClient:
    """
    Client for LLM-based activity classification.
    Supports OpenAI and Anthropic APIs.
    """

    def __init__(self, api_key: str, provider: str = 'openai'):
        """
        Initialize LLM client.

        Args:
            api_key: API key for the LLM provider
            provider: 'openai' or 'anthropic'
        """
        self.api_key = api_key
        self.provider = provider
        self._validate_provider()

    def _validate_provider(self):
        """Validate provider is supported."""
        if self.provider not in ['openai', 'anthropic']:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def classify_activity(self, activity_text: str) -> ClassificationResult:
        """
        Classify a legal work activity using LLM.

        Args:
            activity_text: Description of the activity (app, title, context)

        Returns:
            ClassificationResult with matter_code, narrative, confidence
        """
        prompt = self._build_classification_prompt(activity_text)

        try:
            response = self._call_api(prompt)
            return self._parse_classification_response(response)
        except Exception as e:
            logging.error(f"LLM classification failed: {e}")
            return ClassificationResult(
                matter_code=None,
                narrative=activity_text,
                confidence=0.0
            )

    def _build_classification_prompt(self, activity_text: str) -> str:
        """Build the prompt for activity classification."""
        return f"""Classify this legal work activity and suggest a billing matter code:

Activity: {activity_text}

Respond in JSON format:
{{"matter_code": "suggested code or null", "narrative": "billing description", "confidence": 0.0-1.0}}"""

    def _call_api(self, prompt: str) -> str:
        """Call the LLM API. Override in subclass or mock for testing."""
        if self.provider == 'openai':
            return self._call_openai(prompt)
        else:
            return self._call_anthropic(prompt)

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        import openai
        openai.api_key = self.api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        import anthropic
        client = anthropic.Client(api_key=self.api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def _parse_classification_response(self, response: str) -> ClassificationResult:
        """Parse LLM response into ClassificationResult."""
        try:
            data = json.loads(response)
            return ClassificationResult(
                matter_code=data.get('matter_code'),
                narrative=data.get('narrative', ''),
                confidence=float(data.get('confidence', 0.0))
            )
        except json.JSONDecodeError:
            return ClassificationResult(
                matter_code=None,
                narrative=response,
                confidence=0.0
            )
```

### Tests

```python
# tests/test_llm.py (CREATE)
"""Tests for LLM integration."""
import pytest
from unittest.mock import patch, MagicMock
from syncopaid.llm import LLMClient, ClassificationResult


def test_llm_client_initialization():
    client = LLMClient(api_key='test', provider='openai')
    assert client.api_key == 'test'
    assert client.provider == 'openai'


def test_llm_client_invalid_provider():
    with pytest.raises(ValueError):
        LLMClient(api_key='test', provider='invalid')


@patch('syncopaid.llm.LLMClient._call_api')
def test_classify_activity(mock_api):
    mock_api.return_value = '{"matter_code": "Matter 123", "narrative": "Research estate law", "confidence": 0.9}'

    client = LLMClient(api_key='test')
    result = client.classify_activity('Google Chrome - Estate Tax Research')

    assert result.matter_code == 'Matter 123'
    assert result.narrative == 'Research estate law'
    assert result.confidence == 0.9
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_llm.py -v
python -c "from syncopaid.llm import LLMClient; print('OK')"
```

## Dependencies
None - this is the first LLM sub-plan.

## Next Task
After this: `050_llm-billing-rounding.md`
