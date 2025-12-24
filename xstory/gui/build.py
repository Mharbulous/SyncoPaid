#!/usr/bin/env python3
"""
Build script for Xstory.
Creates a standalone executable using PyInstaller.
"""

import subprocess
import sys
import shutil
from pathlib import Path


def main():
    """Build the executable."""
    script_dir = Path(__file__).parent
    main_script = script_dir / 'xstory.py'
    dist_dir = script_dir / 'dist'
    build_dir = script_dir / 'build'

    # Check if PyInstaller is available
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # Build command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name', 'Xstory',
        '--distpath', str(dist_dir),
        '--workpath', str(build_dir),
        '--specpath', str(build_dir),
        str(main_script)
    ]

    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=script_dir)

    if result.returncode == 0:
        exe_path = dist_dir / 'Xstory.exe'
        if exe_path.exists():
            print(f"\nBuild successful!")
            print(f"Executable: {exe_path}")
        else:
            # On Linux, it won't have .exe extension
            exe_path = dist_dir / 'Xstory'
            if exe_path.exists():
                print(f"\nBuild successful!")
                print(f"Executable: {exe_path}")
            else:
                print("\nBuild completed but executable not found.")
    else:
        print(f"\nBuild failed with return code {result.returncode}")
        sys.exit(1)


if __name__ == '__main__':
    main()
