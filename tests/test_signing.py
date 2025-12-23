"""Tests for code signing utilities."""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Only run on Windows
pytestmark = pytest.mark.skipif(
    sys.platform != 'win32',
    reason="Code signing tests only run on Windows"
)


def test_find_signtool_returns_path():
    """Test signtool discovery finds a path."""
    # Import after skip check
    from scripts.sign_exe import find_signtool

    result = find_signtool()
    assert result is not None
    assert 'signtool' in result.lower()


@patch('subprocess.run')
def test_sign_executable_success(mock_run):
    """Test successful signing."""
    from scripts.sign_exe import sign_executable

    mock_run.return_value = MagicMock(returncode=0, stderr='')

    result = sign_executable('test.exe', 'cert.pfx', 'password')

    assert result is True
    mock_run.assert_called_once()


@patch('subprocess.run')
def test_sign_executable_failure(mock_run):
    """Test signing failure."""
    from scripts.sign_exe import sign_executable

    mock_run.return_value = MagicMock(returncode=1, stderr='Error: certificate not found')

    result = sign_executable('test.exe', 'cert.pfx', 'password')

    assert result is False


@patch('subprocess.run')
def test_verify_signature(mock_run):
    """Test signature verification."""
    from scripts.sign_exe import verify_signature

    mock_run.return_value = MagicMock(returncode=0)

    result = verify_signature('test.exe')

    assert result is True
