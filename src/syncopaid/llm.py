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

    def generate_narrative(self, activity_summary: str) -> str:
        """
        Generate professional billing narrative from activity summary.

        Args:
            activity_summary: Combined description of activities

        Returns:
            Professional billing narrative string
        """
        prompt = f"""Convert these work activities into a professional billing narrative:

Activities: {activity_summary}

Respond with only the narrative text, no JSON. Keep it concise (1-2 sentences)."""

        return self._call_api(prompt).strip()

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
