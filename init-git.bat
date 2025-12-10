@echo off
REM TimeLawg Git Initialization Script for Windows
REM This script sets up a new Git repository and pushes to GitHub

echo.
echo ========================================
echo TimeLawg Git Setup for Windows
echo ========================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git from https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Check if already a git repo
if exist .git (
    echo WARNING: This directory is already a Git repository
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" (
        echo Aborted.
        pause
        exit /b 0
    )
    echo.
) else (
    echo Initializing Git repository...
    git init
    if errorlevel 1 (
        echo ERROR: Failed to initialize Git repository
        pause
        exit /b 1
    )
    echo ✓ Git repository initialized
    echo.
)

REM Configure Git user if not set
git config user.name >nul 2>&1
if errorlevel 1 (
    echo.
    echo Git user not configured. Please enter your details:
    set /p gitname="Your name: "
    set /p gitemail="Your email: "
    git config user.name "%gitname%"
    git config user.email "%gitemail%"
    echo ✓ Git user configured
    echo.
)

REM Add all files (respecting .gitignore)
echo Adding files to Git...
git add .
if errorlevel 1 (
    echo ERROR: Failed to add files
    pause
    exit /b 1
)
echo ✓ Files added
echo.

REM Show what will be committed
echo Files to be committed:
git status --short
echo.

REM Create initial commit
echo Creating initial commit...
git commit -m "Initial commit: TimeLawg MVP implementation

- Window tracking with pywin32 API
- Idle detection (3-minute threshold)
- SQLite database storage
- JSON export for LLM categorization
- System tray interface
- Full documentation and setup guides

Ready for testing and GitHub deployment."

if errorlevel 1 (
    echo ERROR: Failed to create commit
    pause
    exit /b 1
)
echo ✓ Initial commit created
echo.

REM Prompt for GitHub repository URL
echo ========================================
echo GitHub Setup
echo ========================================
echo.
echo Before continuing, create a new PRIVATE repository on GitHub:
echo   1. Go to https://github.com/new
echo   2. Repository name: TimeLawg
echo   3. Description: Windows 11 automatic time tracker for legal billing
echo   4. Visibility: PRIVATE (important - contains activity data structure)
echo   5. Do NOT initialize with README, .gitignore, or license
echo   6. Click "Create repository"
echo.

set /p repourl="Enter your GitHub repository URL (e.g., https://github.com/username/TimeLawg.git): "

if "%repourl%"=="" (
    echo No URL provided. You can add the remote later with:
    echo   git remote add origin YOUR_REPO_URL
    echo   git push -u origin main
    pause
    exit /b 0
)

REM Add remote
echo.
echo Adding remote repository...
git remote add origin "%repourl%"
if errorlevel 1 (
    echo WARNING: Failed to add remote (may already exist)
    git remote set-url origin "%repourl%"
)
echo ✓ Remote added
echo.

REM Rename branch to main if needed
git branch -M main

REM Push to GitHub
echo Pushing to GitHub...
echo (You may be prompted for GitHub credentials)
echo.
git push -u origin main

if errorlevel 1 (
    echo.
    echo ERROR: Failed to push to GitHub
    echo This might be due to:
    echo   - Incorrect repository URL
    echo   - Authentication failure
    echo   - Network issues
    echo.
    echo You can try pushing manually:
    echo   git push -u origin main
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✓ SUCCESS!
echo ========================================
echo.
echo Your TimeLawg repository is now on GitHub!
echo Repository: %repourl%
echo.
echo Next steps:
echo   1. Run: python -m lawtime.tracker   (test window capture)
echo   2. Run: python -m lawtime           (full app with tray icon)
echo   3. Review QUICKSTART.md for usage instructions
echo.
pause
