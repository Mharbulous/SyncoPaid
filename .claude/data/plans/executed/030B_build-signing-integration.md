# 030B: Build Signing Integration
Story ID: 6.4

## Task
Modify build.sh to include optional code signing step after PyInstaller.

## Context
Part of Windows Code Signing Integration (030). This sub-plan integrates the signing script (030A) into the local build process.

## Scope
- Modify `build.sh` to call signing script when certificate environment variables are set
- Signing is optional for local builds (skip if no certificate configured)

## Key Files

| File | Purpose |
|------|---------|
| `build.sh` | Add signing step after PyInstaller build (MODIFY) |

## Prerequisites
- 030A completed (signing script exists at `scripts/sign_exe.py`)

## Implementation

### Step 1: Modify build.sh

Add signing step after successful PyInstaller build. Signing is optional and skipped if certificate environment variables are not set.

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

## Verification

```bash
# Test build without signing (should show skip message)
./build.sh

# Test build with signing (requires actual certificate)
export CODE_SIGNING_CERT="path/to/certificate.pfx"
export CODE_SIGNING_PASSWORD="password"
./build.sh
```

## Dependencies
- 030A: Signing script must exist

## Notes
- Signing is optional for local development builds
- Build fails with clear error message if signing is configured but fails
- Uses environment variables for certificate credentials (not hardcoded)
