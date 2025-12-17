# Compare Conflict Detection Skills

## Task

Run isolated parallel tests comparing two story conflict detection skills against the same ground truth. Determine which performs better on the actual database.

## Skills to Compare

| Skill | Location | Approach |
|-------|----------|----------|
| `conflict-detection` | `.claude/skills/conflict-detection/` | Domain synonym expansion + acceptance criteria + multi-signal scoring |
| `story-vetting` | `.claude/skills/story-vetting/` | Implementation keyword patterns (regex) + high-signal keyword matching |

Both use Python sqlite3, no external deps.

## Ground Truth

**Test cases:** `ai_docs/Optimization-testing/2025-12-17-conflict-detection-test-cases.md`

Contains:
- 3 expected duplicates (TC-DUP-001 to TC-DUP-003)
- 5 expected scope overlaps (TC-OVL-001 to TC-OVL-005)
- 2 negative cases (TC-NEG-001, TC-NEG-002)

## Test Execution

### Phase 1: Parallel Isolated Runs

Launch two sub-agents in parallel with `run_in_background: true`. Each agent runs ONE skill only - no access to the other skill or its results.

**Agent A prompt:**
> Run the conflict-detection skill against the story-tree database. Execute: `python .claude/skills/conflict-detection/scripts/detect_conflicts.py --format json --min-confidence 0.50`. Return the full JSON output. Do NOT read or run the story-vetting skill.

**Agent B prompt:**
> Run the story-vetting skill against the story-tree database. Execute the Python code from Step 2 of `.claude/skills/story-vetting/SKILL.md`. Return the full JSON output. Do NOT read or run the conflict-detection skill.

### Phase 2: Main Agent Judges Results

After both agents complete, the main agent:

1. **Collects results** from both sub-agents via `TaskOutput`
2. **Loads ground truth** from test cases file
3. **Scores each skill** against ground truth:
   - What conflicts did it correctly detect? (True Positives)
   - What conflicts did it miss? (False Negatives)
   - What non-conflicts did it incorrectly flag? (False Positives)
4. **Compares performance** side-by-side
5. **Recommends** which skill to use (or whether to merge approaches)

## Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Duplicate Recall | TP_dup / 3 | ≥80% |
| Scope Overlap Recall | TP_overlap / 5 | ≥60% |
| Precision | TP / (TP + FP) | ≥80% |
| False Positive Count | Total FP on test cases | 0 |

## Key Files

| File | Purpose |
|------|---------|
| `.claude/data/story-tree.db` | Database to scan |
| `ai_docs/Optimization-testing/2025-12-17-conflict-detection-test-cases.md` | Ground truth |
| `.claude/skills/conflict-detection/scripts/detect_conflicts.py` | Skill A script |
| `.claude/skills/story-vetting/SKILL.md` | Skill B inline code (Step 2) |

## Do Not Read During Test

- `ai_docs/Reports/2025-12-17-story-conflict-analysis.md` - May bias results

## Previous Findings

**conflict-detection skill** (developed in session 031):
- 100% on duplicates, 40% on scope overlaps
- Overall: 62% recall, 100% precision on test cases
- Limitation: Lexical similarity fails when stories use different vocabulary for same concept
- Example miss: "Enhanced Context Extraction" vs "Browser URL Extraction" (18% combined similarity)

**story-vetting skill** claims 10/10 validation - needs verification.

## Expected Output

Main agent produces a detailed comparison report including:

### Per-Test-Case Breakdown

| Test Case | Expected | Skill A | Skill B |
|-----------|----------|---------|---------|
| TC-DUP-001 (1.2.6 vs 1.2.9) | duplicate | TP/FN | TP/FN |
| TC-DUP-002 (1.3.5 vs 1.8.1) | duplicate | TP/FN | TP/FN |
| ... | ... | ... | ... |
| TC-NEG-001 (1.2.1 vs 1.2.2) | None | TN/FP | TN/FP |

### Summary Scores

| Metric | Skill A | Skill B | Winner |
|--------|---------|---------|--------|
| Duplicate Recall | X/3 | Y/3 | ? |
| Scope Overlap Recall | X/5 | Y/5 | ? |
| False Positives | N | M | ? |
| Total Conflicts Found | N | M | - |

### Recommendation

- Which skill to use going forward
- Whether approaches should be merged
- Any specific strengths to preserve from each

Save to `ai_docs/Reports/2025-12-17-skill-comparison-results.md`
