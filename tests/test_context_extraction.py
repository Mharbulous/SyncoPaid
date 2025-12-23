"""Tests for context extraction from window titles."""
import pytest
from syncopaid.context_extraction import (
    extract_context,
    extract_url_from_browser,
    extract_subject_from_outlook,
    extract_filepath_from_office,
)


class TestBrowserURLExtraction:
    """Test browser URL extraction from titles."""

    def test_chrome_with_url_in_title(self):
        result = extract_url_from_browser("chrome.exe", "Google - https://google.com - Google Chrome")
        assert result == "https://google.com"

    def test_non_browser_returns_none(self):
        result = extract_url_from_browser("notepad.exe", "test.txt - Notepad")
        assert result is None


class TestOutlookSubjectExtraction:
    """Test Outlook email subject extraction."""

    def test_inbox_format(self):
        result = extract_subject_from_outlook("OUTLOOK.EXE", "Inbox - Meeting Request - user@law.com - Outlook")
        assert result == "Meeting Request"


class TestOfficeFilepathExtraction:
    """Test Office file path extraction."""

    def test_word_document(self):
        result = extract_filepath_from_office("WINWORD.EXE", "Smith-Contract.docx - Word")
        assert result == "Smith-Contract.docx"
