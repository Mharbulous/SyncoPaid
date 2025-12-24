# Establish Consistency Maintenance Workflow - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 21.7 | **Created:** 2025-12-24 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create a workflow and tooling for keeping SyncoPaid documentation consistent as it grows, including style guide compliance checks, terminology linting, scalable navigation, and update procedures.

**Approach:** Enhance the user-manual-generator skill's QA phase with style guide compliance, create a terminology linter script, define navigation structure patterns, and establish documentation update procedures. All deliverables are configuration/documentation files and one Python script for terminology checking.

**Tech Stack:** Markdown documentation, Python 3.11+ (linter script), user-manual-generator skill

---

## Story Context

**Title:** Establish Consistency Maintenance Workflow

**Description:** As a documentation maintainer, I want a workflow for keeping documentation consistent as it grows, so that style, terminology, and navigation remain coherent across all sections.

**Acceptance Criteria:**
- [ ] Add style guide compliance check to skill's QA phase
- [ ] Create terminology linting (flag inconsistent terms)
- [ ] Define navigation structure that scales (sidebar categories, breadcrumbs)
- [ ] Establish update workflow: code change → doc impact → update procedure
- [ ] Add "last reviewed" timestamps to each document
- [ ] Create checklist for adding new documentation sections

## Prerequisites

- [ ] docs/ directory exists (created by story 21.2 or 21.3)
- [ ] docs/STYLE-GUIDE.md exists with terminology glossary (story 21.2)
- [ ] user-manual-generator skill exists at .claude/skills/user-manual-generator/

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `.claude/skills/user-manual-generator/phases/06-quality-assurance.md` | Modify | Add style guide compliance section |
| `scripts/lint-terminology.py` | Create | Script to check terminology consistency |
| `docs/MAINTENANCE.md` | Create | Update workflow and procedures |
| `docs/CONTRIBUTING-DOCS.md` | Create | Checklist for adding new docs |

## Reference Material

**Terminology to check (from STYLE-GUIDE.md):**
- Use "SyncoPaid" (not "Syncopaid" or "syncopaid")
- Use "tracking" (not "monitoring" for user-facing text)
- Use "activity" (not "event" for user-facing text)
- Use "system tray" (not "notification area" or "taskbar icons")
- Use "client matter" (not "project" or "case number")

**QA Phase location:** `.claude/skills/user-manual-generator/phases/06-quality-assurance.md`

**Existing QA checks:**
- Completeness check
- Link validation
- Code sample validation
- Accessibility check
- Content quality review
- Build test

---

## TDD Tasks

### Task 1: Add style guide compliance to QA phase (~5 min)

**Files:**
- Modify: `.claude/skills/user-manual-generator/phases/06-quality-assurance.md`

**Context:** The QA phase already has completeness, link, and accessibility checks. Add a new section specifically for style guide compliance that references the project's STYLE-GUIDE.md and checks terminology, formatting, and voice consistency.

**Step 1 - RED:** Verify style guide compliance section doesn't exist
```bash
grep -q "## Style Guide Compliance" .claude/skills/user-manual-generator/phases/06-quality-assurance.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Add style guide compliance section after the accessibility check section (before "## Content Quality Review")

Find the line containing "## Content Quality Review" and insert the new section before it:

```markdown

## Style Guide Compliance

Before content review, verify consistency with project style guide:

### Terminology Check

```bash
# Check for common terminology violations
# Run from project root where docs/ exists

# Check capitalization
grep -rni "syncopaid" docs/ | grep -v "SyncoPaid" | head -10

# Check for "monitoring" instead of "tracking"
grep -rni "monitoring" docs/ | head -5

# Check for "event" instead of "activity" in user text
grep -rni "\bevent\b" docs/ | grep -v "ActivityEvent" | head -5

# Check for "notification area" instead of "system tray"
grep -rni "notification area" docs/ | head -5
```

### Formatting Standards

- [ ] Headings follow hierarchy (H1 → H2 → H3, no skipping)
- [ ] Lists use consistent style (dashes for bullets, numbers for sequences)
- [ ] Code blocks specify language
- [ ] Callouts use consistent format (> **Note:**, > **Warning:**, > **Tip:**)
- [ ] Steps numbered with format: `1. **Action verb phrase**\n   Detail underneath`

### Voice Consistency

- [ ] Second person ("you") used for instructions
- [ ] Active voice preferred over passive
- [ ] No developer jargon in user-facing content
- [ ] Consistent formality level throughout

### Reference Style Guide

If a project style guide exists (e.g., `docs/STYLE-GUIDE.md`), verify:
- [ ] Terminology matches glossary
- [ ] Formatting follows defined patterns
- [ ] Examples match approved style

```

**Step 3 - Verify GREEN:**
```bash
grep -q "## Style Guide Compliance" .claude/skills/user-manual-generator/phases/06-quality-assurance.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add .claude/skills/user-manual-generator/phases/06-quality-assurance.md
git commit -m "feat(user-manual-generator): add style guide compliance check to QA phase"
```

---

### Task 2: Create terminology linter script (~5 min)

**Files:**
- Create: `scripts/` directory (if needed)
- Create: `scripts/lint-terminology.py`

**Context:** Create a Python script that reads docs/STYLE-GUIDE.md, extracts the terminology glossary, and scans all markdown files in docs/ for violations. Outputs violations with file, line, and suggested fix.

**Step 1 - RED:** Verify script doesn't exist
```bash
test -f scripts/lint-terminology.py && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - Create scripts directory:**
```bash
mkdir -p scripts
```

**Step 3 - GREEN:** Create lint-terminology.py

```python
#!/usr/bin/env python3
"""
Terminology linter for SyncoPaid documentation.

Scans docs/ for terminology inconsistencies based on STYLE-GUIDE.md rules.
Exit code 0 = no violations, 1 = violations found.

Usage: python scripts/lint-terminology.py [--fix]
"""

import re
import sys
from pathlib import Path

# Terminology rules: (pattern_to_find, correct_term, description)
TERMINOLOGY_RULES = [
    (r'\b[Ss]yncopaid\b(?<!SyncoPaid)', 'SyncoPaid', 'Capitalize as SyncoPaid'),
    (r'\bmonitoring\b', 'tracking', 'Use "tracking" for user-facing text'),
    (r'\bnotification area\b', 'system tray', 'Use "system tray" not "notification area"'),
    (r'\btaskbar icon', 'system tray', 'Use "system tray" not "taskbar icon"'),
    (r'\bproject\b(?=.*billing)', 'client matter', 'Use "client matter" for billing contexts'),
]

# Files/patterns to skip
SKIP_PATTERNS = [
    'STYLE-GUIDE.md',  # The style guide itself defines terms
    'CHANGELOG.md',
    'TODO.md',
]


def find_violations(file_path: Path) -> list[tuple[int, str, str, str]]:
    """Find terminology violations in a file.

    Returns list of (line_number, line_content, violation, suggestion)
    """
    violations = []

    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        return violations

    lines = content.split('\n')

    for line_num, line in enumerate(lines, start=1):
        # Skip code blocks
        if line.strip().startswith('```'):
            continue

        for pattern, correct, description in TERMINOLOGY_RULES:
            matches = list(re.finditer(pattern, line, re.IGNORECASE))
            for match in matches:
                # Skip if already correct
                if match.group() == correct:
                    continue
                violations.append((
                    line_num,
                    line.strip()[:80],
                    match.group(),
                    f'{description}: use "{correct}"'
                ))

    return violations


def main():
    docs_dir = Path('docs')

    if not docs_dir.exists():
        print("No docs/ directory found. Nothing to lint.")
        return 0

    all_violations = []

    for md_file in docs_dir.rglob('*.md'):
        # Skip excluded files
        if any(skip in str(md_file) for skip in SKIP_PATTERNS):
            continue

        violations = find_violations(md_file)
        for line_num, line, found, suggestion in violations:
            all_violations.append({
                'file': str(md_file),
                'line': line_num,
                'content': line,
                'found': found,
                'suggestion': suggestion,
            })

    if not all_violations:
        print("✓ No terminology violations found")
        return 0

    print(f"Found {len(all_violations)} terminology violation(s):\n")

    current_file = None
    for v in all_violations:
        if v['file'] != current_file:
            current_file = v['file']
            print(f"\n{current_file}")
            print("-" * len(current_file))

        print(f"  Line {v['line']}: Found '{v['found']}'")
        print(f"    → {v['suggestion']}")
        print(f"    Context: {v['content']}")

    return 1


if __name__ == '__main__':
    sys.exit(main())
```

**Step 4 - Verify GREEN:**
```bash
test -f scripts/lint-terminology.py && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 5 - Test script runs:**
```bash
python3 scripts/lint-terminology.py
```
Expected: Either "No docs/ directory found" or "No terminology violations found" or a list of violations

**Step 6 - COMMIT:**
```bash
git add scripts/lint-terminology.py
git commit -m "feat(docs): add terminology linter script for consistency checking"
```

---

### Task 3: Create documentation maintenance workflow (~5 min)

**Files:**
- Create: `docs/MAINTENANCE.md`

**Context:** Define the workflow for maintaining documentation consistency: how to update docs when code changes, navigation structure guidelines, and "last reviewed" timestamp conventions.

**Step 1 - RED:** Verify file doesn't exist
```bash
test -f docs/MAINTENANCE.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Create MAINTENANCE.md

```markdown
# Documentation Maintenance Workflow

This document defines how to keep SyncoPaid documentation consistent and up-to-date.

---

## Document Metadata

Every documentation file should include a front matter block:

```yaml
---
last_reviewed: 2025-01-15
reviewed_by: [name or "automated"]
---
```

Update `last_reviewed` whenever you verify content is still accurate.

---

## Code Change → Documentation Update Workflow

When code changes affect user-facing behavior:

### 1. Identify Impact

| Code Change Type | Doc Impact | Action |
|-----------------|------------|--------|
| New feature | High | Create new how-to guide |
| Changed behavior | High | Update existing guides |
| New config option | Medium | Update configuration reference |
| Bug fix | Low | Update troubleshooting if relevant |
| Internal refactor | None | No doc changes needed |

### 2. Update Procedure

1. **Find affected docs:** Search for related terms
   ```bash
   grep -rli "feature_name" docs/
   ```

2. **Update content:** Edit affected files

3. **Run terminology linter:**
   ```bash
   python3 scripts/lint-terminology.py
   ```

4. **Update metadata:** Set `last_reviewed` to today

5. **Commit together:** Code and docs in same commit when related

---

## Navigation Structure

### Sidebar Categories

Use these categories for documentation navigation:

| Category | Purpose | Examples |
|----------|---------|----------|
| Getting Started | First-time setup | Installation, Quick Start |
| How-To Guides | Task-oriented | Track Time, Export Data, Review Activities |
| Reference | Complete information | Configuration, CLI Commands |
| Troubleshooting | Problem solving | Common Issues, FAQ |

### Breadcrumb Format

```
Home > Category > Page Title
```

Example: `Home > How-To Guides > Export Your Time Data`

### File Naming Convention

- Use lowercase with hyphens: `getting-started.md`, `export-data.md`
- Keep names short but descriptive
- Match sidebar title to filename where practical

---

## Quarterly Review Checklist

Every 3 months, perform a documentation audit:

- [ ] Run terminology linter
- [ ] Check all "last reviewed" dates older than 90 days
- [ ] Verify screenshots match current UI
- [ ] Test all command examples
- [ ] Check external links still work
- [ ] Review analytics for most-viewed/least-viewed pages
- [ ] Update version numbers if applicable

---

## Adding New Documentation

See `docs/CONTRIBUTING-DOCS.md` for the checklist when adding new sections.
```

**Step 3 - Verify GREEN:**
```bash
test -f docs/MAINTENANCE.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add docs/MAINTENANCE.md
git commit -m "docs: add documentation maintenance workflow"
```

---

### Task 4: Create new documentation checklist (~4 min)

**Files:**
- Create: `docs/CONTRIBUTING-DOCS.md`

**Context:** Create a checklist for contributors adding new documentation sections, ensuring consistency from the start.

**Step 1 - RED:** Verify file doesn't exist
```bash
test -f docs/CONTRIBUTING-DOCS.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `MISSING`

**Step 2 - GREEN:** Create CONTRIBUTING-DOCS.md

```markdown
# Contributing Documentation

Checklist for adding new documentation sections to SyncoPaid.

---

## Before You Write

- [ ] Read `docs/STYLE-GUIDE.md` for voice and terminology
- [ ] Identify which category your doc belongs to (see `docs/MAINTENANCE.md`)
- [ ] Check if similar documentation already exists

---

## New Document Checklist

### File Setup

- [ ] Create file in `docs/` with lowercase-hyphenated name
- [ ] Add front matter with `last_reviewed` date
- [ ] Use appropriate H1 title matching file purpose

### Content Requirements

- [ ] Introduction states what reader will learn/accomplish
- [ ] Organized by task (what user wants to do), not by feature
- [ ] Uses second person ("you") for instructions
- [ ] Numbered steps for sequential actions
- [ ] Code examples tested and working
- [ ] Screenshots have alt text (if applicable)

### Terminology Compliance

- [ ] Uses "SyncoPaid" (correct capitalization)
- [ ] Uses "tracking" not "monitoring"
- [ ] Uses "activity" not "event" for user text
- [ ] Uses "system tray" not "notification area"
- [ ] Uses "client matter" not "project" for billing
- [ ] Run: `python3 scripts/lint-terminology.py`

### Formatting Standards

- [ ] Headings follow hierarchy (H1 → H2 → H3)
- [ ] Lists use dashes for bullets, numbers for sequences
- [ ] Code blocks specify language (```bash, ```python)
- [ ] Callouts use format: `> **Note:**`, `> **Warning:**`, `> **Tip:**`

### Navigation Integration

- [ ] Add to sidebar/navigation (if using SSG)
- [ ] Add cross-links to related documents
- [ ] Verify breadcrumb path is logical

### Final Checks

- [ ] Spell-check completed
- [ ] All links work (internal and external)
- [ ] Reviewed by someone unfamiliar with the feature
- [ ] `last_reviewed` date is today

---

## Quick Reference

### Callout Formats

```markdown
> **Note:** Additional context that's helpful but not critical.

> **Warning:** Important information to prevent errors or data loss.

> **Tip:** Optional optimization or shortcut.
```

### Step Format

```markdown
1. **Open the application**
   Launch SyncoPaid from your Start menu.

2. **Navigate to settings**
   Right-click the system tray icon and select "Settings."
```

### Code Block Format

```markdown
\`\`\`bash
# Description of what this command does
python -m syncopaid
\`\`\`
```

---

## Questions?

If unsure about any guideline, check `docs/STYLE-GUIDE.md` or ask before writing.
```

**Step 3 - Verify GREEN:**
```bash
test -f docs/CONTRIBUTING-DOCS.md && echo "EXISTS" || echo "MISSING"
```
Expected output: `EXISTS`

**Step 4 - COMMIT:**
```bash
git add docs/CONTRIBUTING-DOCS.md
git commit -m "docs: add checklist for contributing new documentation"
```

---

## Verification

After all tasks complete:

1. **Check all files created:**
```bash
ls -la scripts/lint-terminology.py docs/MAINTENANCE.md docs/CONTRIBUTING-DOCS.md
```

2. **Verify QA phase updated:**
```bash
grep "Style Guide Compliance" .claude/skills/user-manual-generator/phases/06-quality-assurance.md
```

3. **Test terminology linter:**
```bash
python3 scripts/lint-terminology.py
```

4. **Verify acceptance criteria:**
- [x] Add style guide compliance check to skill's QA phase (Task 1)
- [x] Create terminology linting (Task 2)
- [x] Define navigation structure (Task 3 - MAINTENANCE.md)
- [x] Establish update workflow (Task 3 - MAINTENANCE.md)
- [x] Add "last reviewed" timestamps (Task 3 - MAINTENANCE.md)
- [x] Create checklist for adding new documentation (Task 4)

---

## Rollback

If changes cause issues:

```bash
git log --oneline -10  # Find commit hashes
git revert <commit-hash>  # Revert specific commits
```

Or to revert all story changes:
```bash
git revert HEAD~4..HEAD  # Revert last 4 commits
```
