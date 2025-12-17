# Skill Comparison Results: conflict-detection vs story-vetting

**Date:** 2025-12-17
**Database:** `.claude/data/story-tree.db` (85 active stories)
**Ground Truth:** `ai_docs/Optimization-testing/2025-12-17-conflict-detection-test-cases.md`

---

## Executive Summary

| Metric | conflict-detection (Skill A) | story-vetting (Skill B) | Winner |
|--------|------------------------------|-------------------------|--------|
| **Duplicate Recall** | 3/3 (100%) | 3/3 (100%) | Tie |
| **Scope Overlap Recall** | 2/5 (40%)* | 5/5 (100%) | **Skill B** |
| **Type Accuracy** | 60% | 100% | **Skill B** |
| **False Positives** | 0 | 0 | Tie |
| **Overall Score** | 5/8 | 8/8 | **Skill B** |

*Note: Skill A detected 2 scope overlaps but classified them as duplicates (wrong type)

**Recommendation: Use `story-vetting` skill for conflict detection.**

---

## Per-Test-Case Breakdown

| Test Case | Expected | Skill A (conflict-detection) | Skill B (story-vetting) |
|-----------|----------|------------------------------|-------------------------|
| **TC-DUP-001** (1.2.6 vs 1.2.9) | duplicate | duplicate @ 0.73 | duplicate @ 0.80 |
| **TC-DUP-002** (1.3.5 vs 1.8.1) | duplicate | duplicate @ 0.95 | duplicate @ 1.00 |
| **TC-DUP-003** (1.5.5 vs 1.7.6) | duplicate | duplicate @ 0.73 | duplicate @ 0.80 |
| **TC-OVL-001** (1.4.8 vs 1.8.4.2) | scope_overlap | duplicate @ 0.73 | scope_overlap @ 1.00 |
| **TC-OVL-002** (1.1.6 vs 1.8.2) | scope_overlap | NOT FOUND | scope_overlap @ 0.90 |
| **TC-OVL-003** (1.1.6 vs 1.8.3) | scope_overlap | NOT FOUND | scope_overlap @ 0.70 |
| **TC-OVL-004** (1.3.6 vs 1.8.4.4) | scope_overlap | duplicate @ 0.78 | scope_overlap @ 1.00 |
| **TC-OVL-005** (1.8.7 vs 1.8.4.3) | scope_overlap | NOT FOUND | scope_overlap @ 0.90 |
| **TC-NEG-001** (1.2.1 vs 1.2.2) | none (TN) | TN | TN |
| **TC-NEG-002** (1.8.4 vs 1.8.4.1) | none (TN) | TN | TN |

### Results Legend
- **TP**: True Positive (correctly detected conflict)
- **FN**: False Negative (missed conflict)
- **TN**: True Negative (correctly did not flag)
- **FP**: False Positive (incorrectly flagged non-conflict)

---

## Summary Scores

| Metric | Skill A | Skill B | Winner |
|--------|---------|---------|--------|
| Duplicate Recall | 3/3 (100%) | 3/3 (100%) | Tie |
| Scope Overlap Recall | 0/5 (0%)* | 5/5 (100%) | **Skill B** |
| False Positive Count | 0 | 0 | Tie |
| Total Conflicts Found | 173 | 228 | - |
| Conflict Types | 3 (dup/overlap/competing) | 2 (dup/scope_overlap) | - |

*Skill A found 2 scope overlaps but misclassified them as duplicates

---

## Detailed Analysis

### Skill A (conflict-detection) Strengths

1. **Strong duplicate detection**: 100% recall on duplicate test cases
2. **Lower noise**: Found 173 total conflicts vs 228 (more conservative)
3. **Multi-type classification**: Detects competing approaches in addition to duplicates/overlaps
4. **Higher confidence scores**: Uses n-gram similarity for nuanced scoring

### Skill A (conflict-detection) Weaknesses

1. **Misses scope overlaps**: Failed to detect 3/5 scope overlap test cases
2. **Type confusion**: Classified 2 scope overlaps as duplicates
3. **Vocabulary dependent**: Stories using different words for same concept are missed
4. **Example failure**: 1.1.6 "Enhanced Context Extraction" vs 1.8.2 "Browser URL Extraction" - conceptually related but different vocabulary

### Skill B (story-vetting) Strengths

1. **Perfect test case performance**: 8/8 correct detections (10/10 including negatives)
2. **Accurate type classification**: All conflicts classified with correct type
3. **Keyword-based detection**: Uses implementation-specific patterns that capture semantic similarity
4. **Higher recall**: Detected all expected scope overlaps

### Skill B (story-vetting) Weaknesses

1. **Higher noise potential**: 228 total conflicts (may include more false positives on full dataset)
2. **Keyword dependency**: Relies on predefined patterns - may miss novel conflicts
3. **Two types only**: Does not detect "competing" approaches (only duplicate/scope_overlap)

---

## Why Skill B Outperformed

### 1. Domain-Specific Keyword Patterns

Skill B uses implementation-specific patterns like:
- `transition_detection` for idle/transition stories
- `ai_learning` for AI learning stories
- `app_blocking` for privacy/blocklist stories
- `archive_compress` for screenshot archiving stories

These patterns capture **semantic similarity** even when titles/descriptions use different vocabulary.

### 2. Multi-Signal Scoring

Skill B combines:
- Title token overlap
- Description Jaccard similarity
- Acceptance criteria overlap
- Shared implementation keywords

The keyword-based signal provides a strong anchor that the n-gram approach in Skill A lacks.

### 3. Correct Type Discrimination

Skill B correctly distinguishes:
- **Duplicates**: Multiple shared high-signal keywords (matter_table, app_blocking, etc.)
- **Scope overlaps**: Single shared keyword + text similarity

---

## Recommendation

### Use `story-vetting` as the primary conflict detection skill

**Rationale:**
1. 100% recall on all positive test cases (duplicates + scope overlaps)
2. Correct conflict type classification
3. Zero false positives on negative test cases
4. Validated 10/10 on ground truth

### Consider Preserving from Skill A

1. **Competing detection**: story-vetting does not detect competing approaches (same problem, different solutions). Consider adding this capability.

2. **Confidence calibration**: Skill A's lower total count (173 vs 228) suggests tighter thresholds that may reduce noise. Consider tuning story-vetting thresholds.

### Merge Recommendation

For a hybrid approach, consider:
1. Use story-vetting's keyword-based detection as primary
2. Add Skill A's "competing" detection logic
3. Use Skill A's higher confidence thresholds to reduce noise

---

## Files

| Skill | Location | Script |
|-------|----------|--------|
| conflict-detection | `.claude/skills/conflict-detection/` | `scripts/detect_conflicts.py` |
| story-vetting | `.claude/skills/story-vetting/` | Inline in `SKILL.md` Step 2 |

---

## Appendix: Raw Statistics

### Skill A (conflict-detection)
- Total conflicts: 173
- Duplicates: 30
- Overlaps: 104
- Competing: 39

### Skill B (story-vetting)
- Total conflicts: 228
- Duplicates: 15
- Scope overlaps: 213
