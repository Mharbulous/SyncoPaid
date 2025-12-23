# 030A: Signing Script Core
Story ID: 6.4

## Task
Create the core signing script with signtool.exe integration and tests.

## Context
Part of Windows Code Signing Integration (030). This sub-plan creates the foundational signing utilities that will be used by the build process and CI/CD.

## Scope
- Create `scripts/sign_exe.py` with signtool discovery, signing, and verification functions
- Create unit tests with mocked subprocess calls

## Key Files

| File | Purpose |
|------|---------|
| `scripts/sign_exe.py` | Signing wrapper script (CREATE) |
| `tests/test_signing.py` | Unit tests for signing utilities (CREATE) |

## Prerequisites
- Windows SDK with signtool.exe (included in Windows development environments)

## Implementation

### Step 1: Create signing script

```python
# scripts/sign_exe.py (CREATE)
"""Sign Windows executable using signtool.exe."""
import subprocess
import sys
import os
from pathlib import Path


def find_signtool():
    """Locate signtool.exe in Windows SDK paths."""
    sdk_paths = [
        r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64",
        r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64",
        r"C:\Program Files (x86)\Windows Kits\10\bin\x64",
    ]
    for sdk_path in sdk_paths:
        signtool = Path(sdk_path) / "signtool.exe"
        if signtool.exists():
            return str(signtool)
    # Fall back to PATH
    return "signtool.exe"


def sign_executable(exe_path: str, cert_file: str, cert_password: str) -> bool:
    """
    Sign executable with Authenticode certificate.

    Args:
        exe_path: Path to .exe file
        cert_file: Path to .pfx certificate file
        cert_password: Certificate password

    Returns:
        True if signing succeeded
    """
    signtool = find_signtool()

    cmd = [
        signtool, "sign",
        "/f", cert_file,
        "/p", cert_password,
        "/fd", "SHA256",
        "/tr", "http://timestamp.digicert.com",
        "/td", "SHA256",
        "/v",
        exe_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Signing failed: {result.stderr}", file=sys.stderr)
        return False

    print(f"Successfully signed: {exe_path}")
    return True


def verify_signature(exe_path: str) -> bool:
    """Verify executable signature is valid."""
    signtool = find_signtool()

    cmd = [signtool, "verify", "/pa", "/v", exe_path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    return result.returncode == 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python sign_exe.py <exe_path> <cert_file> <cert_password>")
        sys.exit(1)

    exe = sys.argv[1]
    cert = sys.argv[2]
    password = sys.argv[3]

    if not sign_executable(exe, cert, password):
        sys.exit(1)

    if not verify_signature(exe):
        print("Warning: Signature verification failed", file=sys.stderr)
        sys.exit(1)

    print("Executable signed and verified successfully")
```

### Step 2: Create tests

```python
# tests/test_signing.py (CREATE)
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
```

## Tests

```bash
# Test signing script imports
python -c "from scripts.sign_exe import find_signtool, sign_executable; print('OK')"

# Run tests (Windows only)
pytest tests/test_signing.py -v
```

## Verification

```bash
# Verify script imports correctly
python -c "from scripts.sign_exe import find_signtool, sign_executable, verify_signature; print('OK')"

# Run tests
pytest tests/test_signing.py -v
```

## Dependencies
None - standalone module.

## Notes
- Tests are skipped on non-Windows platforms
- Subprocess calls are mocked to avoid requiring actual certificate
