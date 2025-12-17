# Conflict Detection Test Cases

**Purpose:** Ground truth for testing conflict-detection skill accuracy
**Database:** `.claude/data/story-tree.db` (as of 2025-12-17)
**DO NOT share with skill during development**

---

## Test Cases: Clear Duplicates

### TC-DUP-001: Screenshot Archiving

| Story A | Story B |
|---------|---------|
| **ID:** 1.2.6 | **ID:** 1.2.9 |
| **Title:** Screenshot Retention & Cleanup Policy | **Title:** Monthly Screenshot Archiving |
| **Status:** planned | **Status:** approved |
| **Parent:** 1.2 | **Parent:** 1.2 |

**Expected Detection:** `duplicate`
**Severity:** High
**Notes:** Same parent (siblings), nearly identical acceptance criteria (monthly zip compression)

---

### TC-DUP-002: Matter/Client Database

| Story A | Story B |
|---------|---------|
| **ID:** 1.3.5 | **ID:** 1.8.1 |
| **Title:** Matter/Client Database Management | **Title:** Matter/Client Database |
| **Status:** concept | **Status:** approved |
| **Parent:** 1.3 (Data Management) | **Parent:** 1.8 (LLM Integration) |

**Expected Detection:** `duplicate`
**Severity:** Critical
**Notes:** Cross-branch duplicate - same SQLite table schema, same CRUD UI

---

### TC-DUP-003: Application Blocklist

| Story A | Story B |
|---------|---------|
| **ID:** 1.5.5 | **ID:** 1.7.6 |
| **Title:** Privacy Content Blocking Configuration | **Title:** Configurable Application Blocklist |
| **Status:** concept | **Status:** concept |
| **Parent:** 1.5 (Configuration) | **Parent:** 1.7 (Privacy & Security) |

**Expected Detection:** `duplicate`
**Severity:** High
**Notes:** Cross-branch duplicate - same config blocklist, same process matching

---

## Test Cases: Scope Overlap

### TC-OVL-001: Smart Prompts / Transition Detection

| Story A | Story B |
|---------|---------|
| **ID:** 1.4.8 | **ID:** 1.8.4.2 |
| **Title:** Smart Time Categorization Prompt | **Title:** Transition Detection & Smart Prompts |
| **Status:** concept | **Status:** approved |
| **Parent:** 1.4 (UI) | **Parent:** 1.8.4 (AI Disambiguation) |

**Expected Detection:** `scope_overlap`
**Severity:** Medium
**Notes:** Both detect idle return, inbox browsing, context switches; 1.8.4.2 is more comprehensive

---

### TC-OVL-002: Context Extraction (Browser URLs)

| Story A | Story B |
|---------|---------|
| **ID:** 1.1.6 | **ID:** 1.8.2 |
| **Title:** Enhanced Context Extraction from Window Titles | **Title:** Browser URL Extraction |
| **Status:** concept | **Status:** planned |
| **Parent:** 1.1 (Window Tracking) | **Parent:** 1.8 (LLM Integration) |

**Expected Detection:** `scope_overlap`
**Severity:** Medium
**Notes:** 1.1.6 is superset covering URLs+Outlook+Office; 1.8.2 is focused subset (URLs only)

---

### TC-OVL-003: Context Extraction (UI Automation)

| Story A | Story B |
|---------|---------|
| **ID:** 1.1.6 | **ID:** 1.8.3 |
| **Title:** Enhanced Context Extraction from Window Titles | **Title:** UI Automation Integration |
| **Status:** concept | **Status:** planned |
| **Parent:** 1.1 (Window Tracking) | **Parent:** 1.8 (LLM Integration) |

**Expected Detection:** `scope_overlap`
**Severity:** Medium
**Notes:** 1.1.6 covers Outlook extraction; 1.8.3 covers Outlook+Explorer via UI Automation

---

### TC-OVL-004: AI Learning from Corrections

| Story A | Story B |
|---------|---------|
| **ID:** 1.3.6 | **ID:** 1.8.4.4 |
| **Title:** AI Learning Database for Categorization Patterns | **Title:** Learning from Corrections |
| **Status:** concept | **Status:** concept |
| **Parent:** 1.3 (Data Management) | **Parent:** 1.8.4 (AI Disambiguation) |

**Expected Detection:** `scope_overlap`
**Severity:** Low
**Notes:** Both store corrections for AI learning; different perspectives (schema vs behavior)

---

### TC-OVL-005: Review Interface

| Story A | Story B |
|---------|---------|
| **ID:** 1.8.7 | **ID:** 1.8.4.3 |
| **Title:** Time Entry Review Interface | **Title:** Interactive Review UI with Screenshots |
| **Status:** concept | **Status:** concept |
| **Parent:** 1.8 | **Parent:** 1.8.4 |

**Expected Detection:** `scope_overlap` or `related`
**Severity:** Low
**Notes:** 1.8.7 is broader (list view, bulk actions); 1.8.4.3 focuses on screenshot context

---

## Test Cases: Expected Non-Conflicts (Negative Cases)

### TC-NEG-001: Sibling Stories - Different Features

| Story A | Story B |
|---------|---------|
| **ID:** 1.2.1 | **ID:** 1.2.2 |
| **Title:** Periodic Screenshot Capture | **Title:** Perceptual Hash Deduplication |

**Expected Detection:** `independent` (no conflict)
**Notes:** Different features under same parent

---

### TC-NEG-002: Parent-Child Relationship

| Story A | Story B |
|---------|---------|
| **ID:** 1.8.4 | **ID:** 1.8.4.1 |
| **Title:** AI Disambiguation with Screenshot Context | **Title:** Activity-to-Matter Matching |

**Expected Detection:** `independent` (parent-child, not conflict)
**Notes:** Child decomposition, not overlap

---

## Scoring Criteria

| Metric | Weight | Description |
|--------|--------|-------------|
| True Positives | 40% | Correctly identified conflicts |
| False Negatives | 30% | Missed conflicts (bad) |
| False Positives | 20% | Flagged non-conflicts (annoying but not critical) |
| Severity Accuracy | 10% | Correct severity classification |

**Target:** ≥80% True Positive rate on duplicates, ≥60% on scope overlaps
