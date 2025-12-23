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


class TestLegalResearchDetection:
    """Test legal research application detection."""

    @pytest.mark.parametrize("app_name", [
        "Westlaw.exe", "westlaw.exe", "WestlawNext.exe",
        "LexisNexis.exe", "lexisnexis.exe",
    ])
    def test_legal_app_detection_desktop(self, app_name):
        """Desktop apps should be detected."""
        from syncopaid.context_extraction import is_legal_research_app
        assert is_legal_research_app(app_name) is True

    @pytest.mark.parametrize("title_pattern", [
        "Westlaw - Search Results",
        "CanLII - 2024 BCSC 1234",
        "LexisNexis - Case Search",
        "Fastcase - Smith v. Jones",
        "Casetext - Legal Research",
    ])
    def test_legal_app_detection_browser(self, title_pattern):
        """Browser tabs with legal sites should be detected."""
        from syncopaid.context_extraction import is_legal_research_app
        assert is_legal_research_app("chrome.exe", title_pattern) is True

    def test_non_legal_app_not_detected(self):
        from syncopaid.context_extraction import is_legal_research_app
        assert is_legal_research_app("notepad.exe") is False
        assert is_legal_research_app("chrome.exe", "YouTube - Funny Video") is False
