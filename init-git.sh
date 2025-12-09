#!/bin/bash
# TimeLogger Git Initialization Script for Unix/Linux/macOS
# This script sets up a new Git repository and pushes to GitHub

set -e  # Exit on error

echo ""
echo "========================================"
echo "TimeLogger Git Setup for Unix/Linux/macOS"
echo "========================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "ERROR: Git is not installed"
    echo "Please install Git:"
    echo "  - macOS: brew install git"
    echo "  - Ubuntu/Debian: sudo apt-get install git"
    echo "  - Fedora: sudo dnf install git"
    exit 1
fi

# Check if already a git repo
if [ -d .git ]; then
    echo "WARNING: This directory is already a Git repository"
    echo ""
    read -p "Continue anyway? (y/n): " continue
    if [[ ! "$continue" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    echo ""
else
    echo "Initializing Git repository..."
    git init
    echo "✓ Git repository initialized"
    echo ""
fi

# Configure Git user if not set
if ! git config user.name &> /dev/null; then
    echo ""
    echo "Git user not configured. Please enter your details:"
    read -p "Your name: " gitname
    read -p "Your email: " gitemail
    git config user.name "$gitname"
    git config user.email "$gitemail"
    echo "✓ Git user configured"
    echo ""
fi

# Add all files (respecting .gitignore)
echo "Adding files to Git..."
git add .
echo "✓ Files added"
echo ""

# Show what will be committed
echo "Files to be committed:"
git status --short
echo ""

# Create initial commit
echo "Creating initial commit..."
git commit -m "Initial commit: TimeLogger MVP implementation

- Window tracking with pywin32 API
- Idle detection (3-minute threshold)
- SQLite database storage
- JSON export for LLM categorization
- System tray interface
- Full documentation and setup guides

Ready for testing and GitHub deployment."

echo "✓ Initial commit created"
echo ""

# Prompt for GitHub repository URL
echo "========================================"
echo "GitHub Setup"
echo "========================================"
echo ""
echo "Before continuing, create a new PRIVATE repository on GitHub:"
echo "  1. Go to https://github.com/new"
echo "  2. Repository name: TimeLogger"
echo "  3. Description: Windows 11 automatic time tracker for legal billing"
echo "  4. Visibility: PRIVATE (important - contains activity data structure)"
echo "  5. Do NOT initialize with README, .gitignore, or license"
echo "  6. Click 'Create repository'"
echo ""

read -p "Enter your GitHub repository URL (e.g., https://github.com/username/TimeLogger.git): " repourl

if [ -z "$repourl" ]; then
    echo "No URL provided. You can add the remote later with:"
    echo "  git remote add origin YOUR_REPO_URL"
    echo "  git push -u origin main"
    exit 0
fi

# Add remote
echo ""
echo "Adding remote repository..."
if git remote add origin "$repourl" 2>/dev/null; then
    echo "✓ Remote added"
else
    echo "WARNING: Remote already exists, updating URL..."
    git remote set-url origin "$repourl"
    echo "✓ Remote URL updated"
fi
echo ""

# Rename branch to main if needed
git branch -M main

# Push to GitHub
echo "Pushing to GitHub..."
echo "(You may be prompted for GitHub credentials)"
echo ""

if git push -u origin main; then
    echo ""
    echo "========================================"
    echo "✓ SUCCESS!"
    echo "========================================"
    echo ""
    echo "Your TimeLogger repository is now on GitHub!"
    echo "Repository: $repourl"
    echo ""
    echo "Next steps:"
    echo "  1. Run: python -m lawtime.tracker   (test window capture)"
    echo "  2. Run: python -m lawtime           (full app with tray icon)"
    echo "  3. Review QUICKSTART.md for usage instructions"
    echo ""
else
    echo ""
    echo "ERROR: Failed to push to GitHub"
    echo "This might be due to:"
    echo "  - Incorrect repository URL"
    echo "  - Authentication failure"
    echo "  - Network issues"
    echo ""
    echo "You can try pushing manually:"
    echo "  git push -u origin main"
    exit 1
fi
