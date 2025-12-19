"""Test context extraction from window titles."""
import sys
sys.path.insert(0, 'src')

from syncopaid.context_extraction import extract_url_from_browser, extract_subject_from_outlook

def test_extract_url_chrome_with_url():
    """Extract URL from Chrome title with embedded URL."""
    title = "Smith vs Jones - CanLII - https://canlii.ca/t/abc123 - Google Chrome"
    result = extract_url_from_browser("chrome.exe", title)
    assert result == "https://canlii.ca/t/abc123"

def test_extract_url_chrome_without_url():
    """Return None when no URL pattern found."""
    title = "New Tab - Google Chrome"
    result = extract_url_from_browser("chrome.exe", title)
    assert result is None

def test_extract_url_edge():
    """Extract URL from Edge title."""
    title = "Case Law - https://www.courts.gov.bc.ca/decisions - Microsoft Edge"
    result = extract_url_from_browser("msedge.exe", title)
    assert result == "https://www.courts.gov.bc.ca/decisions"

def test_extract_url_firefox():
    """Extract URL from Firefox title."""
    title = "Research Document - https://example.com/doc - Mozilla Firefox"
    result = extract_url_from_browser("firefox.exe", title)
    assert result == "https://example.com/doc"

def test_extract_url_non_browser():
    """Return None for non-browser apps."""
    title = "Document.docx - Word"
    result = extract_url_from_browser("WINWORD.EXE", title)
    assert result is None

def test_extract_subject_inbox_format():
    """Extract subject from Outlook inbox view."""
    title = "Inbox - RE: Smith vs Jones Settlement - user@lawfirm.com - Outlook"
    result = extract_subject_from_outlook("OUTLOOK.EXE", title)
    assert result == "RE: Smith vs Jones Settlement"

def test_extract_subject_message_format():
    """Extract subject from Outlook message window."""
    title = "FW: Discovery Documents - Message (HTML) - Outlook"
    result = extract_subject_from_outlook("OUTLOOK.EXE", title)
    assert result == "FW: Discovery Documents"

def test_extract_subject_generic_inbox():
    """Return None for generic inbox without specific subject."""
    title = "Inbox - user@lawfirm.com - Outlook"
    result = extract_subject_from_outlook("OUTLOOK.EXE", title)
    assert result is None

def test_extract_subject_non_outlook():
    """Return None for non-Outlook apps."""
    title = "Email Subject - Thunderbird"
    result = extract_subject_from_outlook("thunderbird.exe", title)
    assert result is None

if __name__ == "__main__":
    print("Running context extraction tests...")
    test_extract_url_chrome_with_url()
    test_extract_url_chrome_without_url()
    test_extract_url_edge()
    test_extract_url_firefox()
    test_extract_url_non_browser()
    test_extract_subject_inbox_format()
    test_extract_subject_message_format()
    test_extract_subject_generic_inbox()
    test_extract_subject_non_outlook()
    print("All tests passed!")
