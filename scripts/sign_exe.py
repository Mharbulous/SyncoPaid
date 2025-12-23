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
