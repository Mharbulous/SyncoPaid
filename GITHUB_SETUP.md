# GitHub Setup Guide for SyncoPaid

This guide walks you through setting up your SyncoPaid repository on GitHub and establishing a development workflow.

## Table of Contents

- [Initial Setup (First Time)](#initial-setup-first-time)
- [Daily Git Workflow](#daily-git-workflow)
- [Important Security Notes](#important-security-notes)
- [Troubleshooting](#troubleshooting)

## Initial Setup (First Time)

### Prerequisites

- Git installed on your system
- GitHub account created
- SyncoPaid code copied to your workspace

### Automated Setup (Recommended)

We provide scripts that automate the entire setup process:

**Windows:**
```powershell
.\init-git.bat
```

**Unix/Linux/macOS:**
```bash
./init-git.sh
```

These scripts will:
1. Initialize the Git repository
2. Configure your Git user (if needed)
3. Add all files (respecting `.gitignore`)
4. Create the initial commit
5. Prompt you to create a GitHub repository
6. Add the remote and push your code

### Manual Setup

If you prefer to set up Git manually:

#### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Configure your repository:
   - **Repository name:** `SyncoPaid`
   - **Description:** `Windows 11 automatic time tracker for legal billing`
   - **Visibility:** **PRIVATE** (critical - this is personal activity tracking code)
   - **Do NOT** check "Initialize with README" (we already have one)
   - **Do NOT** add .gitignore or license (already included)
3. Click "Create repository"
4. Copy the repository URL (e.g., `https://github.com/yourusername/TimeLogger.git`)

#### Step 2: Initialize Local Repository

```bash
# Initialize Git
git init

# Configure user (if not already set globally)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: TimeLogger MVP implementation"

# Rename branch to main
git branch -M main

# Add GitHub remote
git remote add origin https://github.com/yourusername/TimeLogger.git

# Push to GitHub
git push -u origin main
```

## Daily Git Workflow

### Making Changes

```bash
# 1. Check what files you've changed
git status

# 2. Review your changes
git diff

# 3. Add files to staging
git add lawtime/tracker.py          # Add specific file
git add lawtime/                    # Add entire directory
git add .                           # Add all changes

# 4. Commit your changes
git commit -m "Descriptive commit message"

# Examples of good commit messages:
# - "Fix idle detection threshold bug"
# - "Add export filter for date ranges"
# - "Update documentation for tray icon usage"
# - "Improve database query performance"
```

### Pushing to GitHub

```bash
# Push your commits to GitHub
git push

# First time pushing a new branch
git push -u origin feature-branch-name
```

### Viewing History

```bash
# View commit history
git log

# Compact view
git log --oneline

# View changes in last commit
git show
```

### Creating Branches (Optional)

For experimental features, create a branch:

```bash
# Create and switch to new branch
git checkout -b feature-llm-integration

# Make your changes, commit them
git add .
git commit -m "Add LLM integration prototype"

# Push branch to GitHub
git push -u origin feature-llm-integration

# Switch back to main branch
git checkout main

# Merge feature when ready
git merge feature-llm-integration
```

## Important Security Notes

### What Gets Committed vs. Ignored

The `.gitignore` file is configured to **NEVER** commit:

**Protected (NEVER committed):**
- `*.db` - Your activity database (contains sensitive work data)
- `*.json` - Exported activity data
- `venv/` - Virtual environment (too large, user-specific)
- `.env` - Environment variables
- `__pycache__/` - Python bytecode

**Committed (safe to share):**
- All `.py` source files
- Documentation (`.md` files)
- `requirements.txt`
- Configuration templates
- Setup scripts

### Verifying Before Push

**Always check what you're about to commit:**

```bash
# See what files are staged
git status

# See actual changes being committed
git diff --cached

# If you see .db or .json files, STOP!
# They should be ignored by .gitignore
```

### If You Accidentally Commit Sensitive Data

If you accidentally commit a database or JSON file:

```bash
# Remove from Git but keep local file
git rm --cached lawtime.db
git commit -m "Remove database file from repository"
git push

# If already pushed, you may need to rewrite history
# (This is advanced - consult Git documentation)
```

## Troubleshooting

### Authentication Issues

**GitHub deprecated password authentication in 2021.** You must use:

1. **Personal Access Token (PAT):**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `repo` scope
   - Use token as password when prompted

2. **SSH Keys (recommended):**
   ```bash
   # Generate SSH key
   ssh-keygen -t ed25519 -C "your.email@example.com"

   # Add to GitHub: Settings → SSH and GPG keys

   # Change remote URL to SSH
   git remote set-url origin git@github.com:yourusername/TimeLogger.git
   ```

### "Repository Not Found" Error

- Verify the repository URL: `git remote -v`
- Ensure the repository is created on GitHub
- Check you have access to the repository

### Merge Conflicts

If you get conflicts (rare when working solo):

```bash
# See conflicting files
git status

# Open conflicting files and manually resolve
# Look for conflict markers: <<<<<<<, =======, >>>>>>>

# After resolving
git add resolved-file.py
git commit -m "Resolve merge conflict"
```

### Undoing Changes

```bash
# Discard changes to a file (DESTRUCTIVE)
git checkout -- lawtime/tracker.py

# Unstage a file (keep changes)
git reset HEAD lawtime/tracker.py

# Undo last commit (keep changes)
git reset --soft HEAD^

# Undo last commit (discard changes) - DESTRUCTIVE
git reset --hard HEAD^
```

### Large File Warnings

If you see warnings about large files:

- Check if `.db` or `.json` files are being committed
- Verify `.gitignore` is working: `git check-ignore -v lawtime.db`
- These files should show as ignored

## Best Practices

### Commit Often
- Commit after completing a logical unit of work
- Don't wait until end of day - commit incrementally
- Small, focused commits are easier to review and undo

### Write Descriptive Messages
```bash
# Good
git commit -m "Fix idle detection resetting incorrectly after resume from sleep"

# Bad
git commit -m "fix bug"
git commit -m "updates"
```

### Pull Before Push (Multi-Device)

If working across multiple computers:

```bash
# Always pull latest changes first
git pull

# Then push your changes
git push
```

### Backup Strategy

- GitHub acts as your backup
- Push regularly (at least daily)
- Consider enabling GitHub repository backup/mirror

## Next Steps

After completing GitHub setup:

1. **Test window capture:** `python -m lawtime.tracker`
2. **Run full application:** `python -m lawtime`
3. **Review documentation:** See `QUICKSTART.md` and `README.md`
4. **Start overnight test:** Run for 8+ hours to validate stability

## Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

---

**Remember:** Your activity data (`*.db`, `*.json`) is **NEVER** committed to Git. The `.gitignore` file protects your privacy by excluding these files from version control.
