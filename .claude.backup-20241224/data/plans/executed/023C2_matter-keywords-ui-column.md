# 023C2: Matter Keywords - UI Column

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.1.1 | **Created:** 2025-12-22 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add Keywords (AI) column to the MatterDialog treeview.
**Approach:** Modify MatterDialog to include keywords column and populate it with formatted keywords.
**Tech Stack:** tkinter (existing UI framework)

---

## Story Context

**Title:** Matter Keywords/Tags for AI Matching
**Description:** Keywords displayed in matter list UI (read-only, AI-managed). Users see the keywords but cannot edit them - AI has complete control.

**Acceptance Criteria (partial):**
- [ ] Keywords displayed in matter list UI (read-only, AI-managed)
- [ ] Keywords are clearly labeled as AI-generated

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 023C1 complete (formatting functions exist)
- [ ] Baseline tests pass: `python -m pytest tests/test_matter_keywords.py -v`

## TDD Tasks

### Task 1: Add Keywords column to MatterDialog treeview (~5 min)

**Files:**
- Modify: `src/syncopaid/matter_client_dialog.py`
- Test: Manual verification (UI component)

**Context:** MatterDialog uses tkinter Treeview to display matters. We need to add a "Keywords (AI)" column showing the formatted keywords. The column header indicates these are AI-managed.

**Step 1:** Locate MatterDialog class and its treeview setup

First, read the current structure:
```bash
grep -n "columns=" src/syncopaid/matter_client_dialog.py
grep -n "Treeview" src/syncopaid/matter_client_dialog.py
```

**Step 2:** Modify MatterDialog._create_treeview to add Keywords column

Find the section where treeview columns are defined and add the Keywords column. The exact line numbers depend on current file structure, but the pattern is:

```python
# In MatterDialog._create_treeview method, update columns tuple:
# Before:
# columns = ("matter_number", "client", "description", "status")
# After:
columns = ("matter_number", "client", "description", "keywords", "status")

# Add column heading:
self.tree.heading("keywords", text="Keywords (AI)")
self.tree.column("keywords", width=200, minwidth=100)
```

**Step 3:** Modify MatterDialog._refresh_list to populate keywords

Find the method that populates the treeview (usually _refresh_list or similar) and update it to include keywords:

```python
# In the method that populates treeview, use get_matters_with_keywords:
# Before:
# matters = self.db.get_matters()
# After:
matters = get_matters_with_keywords(self.db)

# When inserting into treeview, include keywords_display:
# Before:
# values=(m['matter_number'], client_name, m['description'], m['status'])
# After:
values=(m['matter_number'], client_name, m['description'], m['keywords_display'], m['status'])
```

**Step 4 - Verify:** Run the dialog manually
```bash
python -c "
from syncopaid.database import Database
from syncopaid.config import get_config
from syncopaid.matter_client_dialog import MatterDialog
import tkinter as tk

config = get_config()
db = Database(config.db_path)

root = tk.Tk()
root.withdraw()  # Hide main window
dialog = MatterDialog(root, db)
print('MatterDialog opened - check for Keywords (AI) column')
root.mainloop()
"
```

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/matter_client_dialog.py && git commit -m "feat: add Keywords (AI) column to matter list dialog"
```

---

## Final Verification

Manual UI verification:
```bash
# Run the application and open Matters dialog
python -m syncopaid
# Click on Matters in system tray menu
# Verify:
# 1. Keywords (AI) column appears
# 2. Keywords are displayed for matters that have them
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- Keywords column is read-only - no edit functionality
- Column header "Keywords (AI)" clearly indicates AI management
- Next sub-plan (023C3) will add tooltip functionality

## Next Sub-Plan

Continue with 023C3_matter-keywords-ui-tooltip.md to add keyword tooltips.
