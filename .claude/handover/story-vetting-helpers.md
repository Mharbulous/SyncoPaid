# Story Vetting Handover - Helper Script Documentation

## Session Summary

Successfully completed comprehensive story vetting run that processed 238 candidate conflict pairs and resolved 2 duplicate stories.

## What Was Accomplished

### Vetting Results
- **Scanned:** 238 potential conflict pairs from 77 active stories
- **Deleted:** 2 duplicate concept stories (1.3.5, 1.4.8)
- **Classified:** 193 decisions cached (2 duplicates, 191 false positives)
- **Current State:** 75 active stories, clean story tree with no conflicts

### Helper Scripts Created

Three utility scripts were created in `.claude/skills/story-vetting/`:

1. **process_candidates.py** - Filters cached decisions, prioritizes by signal strength
2. **bulk_vetting.py** - Batch applies classification decisions from JSON input
3. **vetting_actions.py** - CLI for individual vetting actions (delete, reject, merge, cache)

### Documentation Status

✅ **COMPLETED:**
- Basic documentation added to SKILL.md (lines 542-615)
- Includes usage examples, input/output formats, function signatures
- Committed in: `b389b56` "docs(story-vetting): document helper utility scripts"

❌ **NEEDS WORK:**
The documentation exists but may need enhancement. User said "We need to document the helpers in a new chat" - suggesting current documentation may be insufficient or needs a different approach.

## Current Branch State

**Branch:** `claude/vet-stories-pQArP`
**Status:** All changes committed and pushed
**Recent commits:**
- `b389b56` - docs(story-vetting): document helper utility scripts
- `7393768` - feat(story-vetting): vet 238 candidate conflicts, resolve 2 duplicates

**Files changed:**
- `.claude/data/story-tree.db` (193 cached decisions added)
- `.claude/skills/story-vetting/SKILL.md` (documentation added)
- `.claude/skills/story-vetting/bulk_vetting.py` (new)
- `.claude/skills/story-vetting/process_candidates.py` (new)
- `.claude/skills/story-vetting/vetting_actions.py` (new)

## Next Steps

### What to Document

Consider these documentation approaches:

1. **Separate Helper README**
   - Create `.claude/skills/story-vetting/helpers/README.md`
   - More detailed explanation of each script's internals
   - Architecture diagrams showing data flow
   - Real-world usage examples from this vetting session

2. **Code Comments**
   - Add docstrings to each function (currently minimal)
   - Explain decision caching logic in detail
   - Document edge cases handled (deleted stories, version mismatches)

3. **Integration Guide**
   - How to integrate these helpers into automated workflows
   - CI/CD pipeline examples
   - Daily vetting automation setup

4. **Examples Directory**
   - `.claude/skills/story-vetting/examples/`
   - Sample input/output JSON files
   - End-to-end vetting workflow example
   - Batch processing 200+ candidates example

### Questions to Clarify

- What level of detail is needed? (User guide vs. developer documentation)
- Should examples be added from this actual vetting session?
- Is the current SKILL.md structure appropriate, or create separate docs?
- Do the scripts need inline code comments/docstrings?

## Key Technical Details

### Cache Behavior
- Uses `vetting_decisions` table with version tracking
- Pair keys normalized (smaller ID first): `"1.3.6|1.8.1"`
- Version mismatch triggers re-classification
- `decided_at` timestamp required (ISO format)

### Helper Script Internals

**process_candidates.py:**
- Scores candidates: `keywords*10 + title_sim*5 + title_overlap*3 + desc_sim*2`
- Groups into high (>20), medium (10-20), low (<10)
- Filters out cached pairs with current versions

**bulk_vetting.py:**
- Accepts JSON array of decision objects
- Executes actions: SKIP, DELETE_CONCEPT, REJECT_CONCEPT, BLOCK_CONCEPT, TRUE_MERGE
- Returns stats: deleted, rejected, blocked, merged, skipped, errors

**vetting_actions.py:**
- CLI wrapper for individual actions
- `_cache_decision_internal()` handles caching with existing DB connection
- Missing `decided_at` timestamp causes IntegrityError (add `datetime.now().isoformat()`)

## File Locations

```
.claude/skills/story-vetting/
├── SKILL.md                    # Main skill documentation (updated)
├── bulk_vetting.py            # New: Batch processor
├── process_candidates.py      # New: Cache filter & prioritizer
├── vetting_actions.py         # New: Individual action CLI
└── vetting_cache.py           # Existing: Cache management

.claude/data/
└── story-tree.db              # Modified: 193 cached decisions added
```

## Usage Examples from This Session

### High-Level Workflow
```bash
# 1. Generate candidates
python << 'PYEOF' > /tmp/candidates.json
# [Phase 1 detection script from SKILL.md]
PYEOF

# 2. Filter cached
python .claude/skills/story-vetting/process_candidates.py < /tmp/candidates.json > /tmp/prioritized.json

# 3. Classify (LLM analysis)
# [Manual classification of remaining candidates]

# 4. Execute actions
python .claude/skills/story-vetting/vetting_actions.py delete "1.3.5" "1.8.1"
python .claude/skills/story-vetting/vetting_actions.py delete "1.4.8" "1.8.4.2"

# 5. Batch cache false positives
# [Python script to cache 191 false positives]
```

## Deleted Stories (Reference)

- **1.3.5** (Matter/Client Database Management) → Duplicate of 1.8.1 (approved)
- **1.4.8** (Smart Time Categorization Prompt) → Duplicate of 1.8.4.2 (planned)

## Contact/Context

This vetting run was the first comprehensive conflict resolution after implementing the vetting cache system. All 238 candidates were processed from cold cache (0 cached decisions → 193 after completion).

Future vetting runs will be significantly faster as most pairs are cached false positives.
