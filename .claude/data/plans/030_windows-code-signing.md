# 030: Windows Code Signing Integration
Story ID: 6.4

## Task
Integrate Windows code signing into the build process so SyncoPaid.exe is signed with a trusted certificate.

## Context
Current build produces unsigned executable (SyncoPaid.spec line 26-47). Windows SmartScreen shows security warnings for unsigned executables. Target users (lawyers) require professional, trustworthy software.

## Scope
- Create signing script using Windows signtool.exe
- Modify build.sh to include signing step after PyInstaller
- Add CI/CD workflow for signed release builds
- Configure certificate handling via GitHub Secrets

## Key Files

| File | Purpose |
|------|---------|
| `build.sh` | Add signing step after build (MODIFY) |
| `scripts/sign_exe.py` | Signing wrapper script (CREATE) |
| `.github/workflows/release-build.yml` | CI workflow for signed builds (CREATE) |
| `docs/code-signing-setup.md` | Certificate renewal docs (CREATE) |

## Prerequisites
- Code signing certificate (EV or Standard Authenticode) from trusted CA
- Windows SDK with signtool.exe (included in Windows development environments)
- GitHub Secrets configured with certificate credentials

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

### Step 2: Modify build.sh

Add signing step after successful build. Signing is optional for local builds.

```bash
# After pyinstaller completes successfully, add:

# Optional: Sign the executable if certificate is available
if [ -n "$CODE_SIGNING_CERT" ] && [ -n "$CODE_SIGNING_PASSWORD" ]; then
    echo ""
    echo "Signing executable..."
    python scripts/sign_exe.py "dist/SyncoPaid.exe" "$CODE_SIGNING_CERT" "$CODE_SIGNING_PASSWORD"
    if [ $? -ne 0 ]; then
        echo ""
        echo "================================================"
        echo "SIGNING FAILED!"
        echo "================================================"
        exit 1
    fi
    echo "Executable signed successfully"
else
    echo ""
    echo "Note: Skipping code signing (no certificate configured)"
    echo "Set CODE_SIGNING_CERT and CODE_SIGNING_PASSWORD to enable signing"
fi
```

### Step 3: Create release workflow

```yaml
# .github/workflows/release-build.yml (CREATE)
name: Build Signed Release

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Version tag (e.g., v1.0.0)'
        required: true

jobs:
  build-signed:
    runs-on: windows-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pyinstaller
          pip install -r requirements.txt

      - name: Generate version info
        run: python generate_version.py

      - name: Build executable
        run: pyinstaller SyncoPaid.spec

      - name: Import code signing certificate
        env:
          CODE_SIGNING_CERT_BASE64: ${{ secrets.CODE_SIGNING_CERT_BASE64 }}
          CODE_SIGNING_PASSWORD: ${{ secrets.CODE_SIGNING_PASSWORD }}
        run: |
          $certBytes = [Convert]::FromBase64String($env:CODE_SIGNING_CERT_BASE64)
          $certPath = "$env:TEMP\code_signing_cert.pfx"
          [IO.File]::WriteAllBytes($certPath, $certBytes)
          echo "CERT_PATH=$certPath" >> $env:GITHUB_ENV

      - name: Sign executable
        env:
          CODE_SIGNING_PASSWORD: ${{ secrets.CODE_SIGNING_PASSWORD }}
        run: |
          python scripts/sign_exe.py "dist/SyncoPaid.exe" "$env:CERT_PATH" "$env:CODE_SIGNING_PASSWORD"

      - name: Verify signature
        run: |
          $signtool = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
          & $signtool verify /pa /v "dist/SyncoPaid.exe"

      - name: Upload signed artifact
        uses: actions/upload-artifact@v4
        with:
          name: SyncoPaid-signed
          path: dist/SyncoPaid.exe

      - name: Clean up certificate
        if: always()
        run: |
          if (Test-Path "$env:CERT_PATH") { Remove-Item "$env:CERT_PATH" -Force }
```

### Step 4: Create documentation

```markdown
# docs/code-signing-setup.md (CREATE)

# Code Signing Setup Guide

## Certificate Requirements

SyncoPaid requires an Authenticode code signing certificate from a trusted CA:
- **EV Certificate** (Extended Validation): Recommended for production. Immediate SmartScreen trust.
- **Standard Certificate**: Acceptable. Builds trust over time via SmartScreen reputation.

### Trusted Certificate Authorities
- DigiCert
- Sectigo (Comodo)
- GlobalSign
- SSL.com

## GitHub Secrets Configuration

Required secrets for CI/CD signing:

| Secret Name | Description |
|-------------|-------------|
| `CODE_SIGNING_CERT_BASE64` | Base64-encoded .pfx certificate file |
| `CODE_SIGNING_PASSWORD` | Certificate password |

### Converting certificate to base64:
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("certificate.pfx")) | Set-Clipboard
```

## Certificate Renewal

Certificates typically expire annually. To renew:

1. Purchase renewal from CA (usually discounted)
2. Generate new CSR or rekey existing certificate
3. Download renewed .pfx file
4. Update `CODE_SIGNING_CERT_BASE64` secret with new base64 value
5. Test signing with a manual workflow dispatch

### Expiration Monitoring

Set calendar reminder 30 days before expiration. Certificate details visible via:
```powershell
signtool verify /pa /v dist/SyncoPaid.exe
```

## Local Development Signing

For local signed builds:
```bash
export CODE_SIGNING_CERT="path/to/certificate.pfx"
export CODE_SIGNING_PASSWORD="your-password"
./build.sh
```
```

## Tests

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

## Verification

```bash
# Test signing script imports
python -c "from scripts.sign_exe import find_signtool, sign_executable; print('OK')"

# Run tests (Windows only)
pytest tests/test_signing.py -v

# Manual verification after build
signtool verify /pa /v dist/SyncoPaid.exe
```

## Dependencies
None - standalone feature.

## Notes
- EV certificates require hardware token (USB key) for signing
- Standard certificates can use .pfx file in CI
- Timestamp server ensures signature validity after cert expiration
- DigiCert timestamp server recommended for reliability
