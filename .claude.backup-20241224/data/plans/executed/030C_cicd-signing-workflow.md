# 030C: CI/CD Signing Workflow and Documentation
Story ID: 6.4

## Task
Create GitHub Actions workflow for signed release builds and documentation for certificate setup.

## Context
Part of Windows Code Signing Integration (030). This sub-plan creates CI/CD automation and user documentation.

## Scope
- Create `.github/workflows/release-build.yml` for automated signed builds
- Create `docs/code-signing-setup.md` with certificate setup and renewal instructions

## Key Files

| File | Purpose |
|------|---------|
| `.github/workflows/release-build.yml` | CI workflow for signed builds (CREATE) |
| `docs/code-signing-setup.md` | Certificate setup documentation (CREATE) |

## Prerequisites
- 030A completed (signing script exists)
- GitHub repository with Secrets support

## Implementation

### Step 1: Create release workflow

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

### Step 2: Create documentation

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

## Verification

```bash
# Verify workflow file is valid YAML
python -c "import yaml; yaml.safe_load(open('.github/workflows/release-build.yml')); print('OK')"

# Verify documentation exists
ls -la docs/code-signing-setup.md
```

## Dependencies
- 030A: Signing script must exist for workflow to function

## Notes
- Workflow triggered on version tags (v*) or manual dispatch
- Certificate stored as base64 in GitHub Secrets for security
- Temporary certificate file cleaned up after signing (always step)
- DigiCert timestamp server ensures signatures remain valid after cert expiration
