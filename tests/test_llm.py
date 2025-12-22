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
