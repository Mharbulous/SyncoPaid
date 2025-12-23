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


class TestCanadianCitationExtraction:
    """Test Canadian case citation extraction."""

    @pytest.mark.parametrize("title,expected", [
        ("CanLII - 2024 BCSC 1234 - Google Chrome", "2024 BCSC 1234"),
        ("Westlaw - 2023 SCC 15 - Smith v Jones", "2023 SCC 15"),
        ("2022 ONCA 456 - Court of Appeal", "2022 ONCA 456"),
        ("R v Smith, 2021 ABQB 789", "2021 ABQB 789"),
        ("Decision - 2024 FC 100 - Federal Court", "2024 FC 100"),
    ])
    def test_neutral_citation_extraction(self, title, expected):
        from syncopaid.context_extraction import extract_canadian_citation
        assert extract_canadian_citation(title) == expected

    def test_no_citation_returns_none(self):
        from syncopaid.context_extraction import extract_canadian_citation
        assert extract_canadian_citation("CanLII - Search Results") is None


class TestUSCitationExtraction:
    """Test US case citation extraction."""

    @pytest.mark.parametrize("title,expected", [
        ("Westlaw - Brown v. Board of Education", "Brown v. Board of Education"),
        ("Smith v. Jones - LexisNexis", "Smith v. Jones"),
        ("Re: Matter of Johnson", "Matter of Johnson"),
        ("In re Application of Smith", "In re Application of Smith"),
    ])
    def test_case_name_extraction(self, title, expected):
        from syncopaid.context_extraction import extract_case_name
        assert extract_case_name(title) == expected

    def test_no_case_name_returns_none(self):
        from syncopaid.context_extraction import extract_case_name
        assert extract_case_name("Westlaw - Home Page") is None


class TestDocketNumberExtraction:
    """Test court docket/file number extraction."""

    @pytest.mark.parametrize("title,expected", [
        ("Case No. 2024-CV-12345", "2024-CV-12345"),
        ("Docket: 1:24-cv-00123", "1:24-cv-00123"),
        ("File No. CV-2024-001234", "CV-2024-001234"),
        ("Court File No. SC-24-123456", "SC-24-123456"),
    ])
    def test_docket_extraction(self, title, expected):
        from syncopaid.context_extraction import extract_docket_number
        assert extract_docket_number(title) == expected

    def test_no_docket_returns_none(self):
        from syncopaid.context_extraction import extract_docket_number
        assert extract_docket_number("General Legal Document") is None


class TestLegalContextIntegration:
    """Test legal context integration in main extract_context function."""

    def test_canlii_citation_extracted(self):
        result = extract_context("chrome.exe", "CanLII - 2024 BCSC 1234 - Google Chrome")
        assert "2024 BCSC 1234" in result

    def test_westlaw_case_name_extracted(self):
        result = extract_context("chrome.exe", "Westlaw - Smith v. Jones - Edge")
        assert "Smith v. Jones" in result

    def test_docket_number_extracted(self):
        result = extract_context("chrome.exe", "Case No. 2024-CV-12345 - Court Portal")
        assert "2024-CV-12345" in result

    def test_legal_desktop_app(self):
        result = extract_context("westlaw.exe", "Research: Smith v. Jones - 2024 SCC 15")
        assert result is not None
