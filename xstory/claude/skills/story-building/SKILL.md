---
name: story-building
description: Use when user says "build stories", "generate stories", "create stories", or asks for new story ideas - combines story generation with duplicate detection in a single workflow. Generates stories, vets for conflicts, and retries up to 10 times if duplicates are detected. Does NOT commit - leaves that to the caller.
disable-model-invocation: true
---

# Story Building - Generate and Vet in One Pass

Generate user stories with built-in duplicate detection.

**Database:** `.claude/data/story-tree.db`

---

## Critical Rule

> **A story is NOT complete until vetted.**
>
> This applies to ALL stories—AI-generated or user-provided.
> Never commit after insertion alone.

---

## Select Workflow

| Context | Workflow |
|---------|----------|
| GitHub Actions / Automation | `references/ci-workflow.md` |
| User conversation / Interactive | `references/interactive-workflow.md` |

### How to Identify Context

**CI Context:**
- Running in GitHub Actions
- No user available for prompts
- Batch processing mode

**Interactive Context:**
- User is present in conversation
- User may provide story directly
- User may ask for story to be generated
- Can ask user for conflict resolution

---

## Shared Requirements

Both workflows share these requirements:

### Database Access

Use Python sqlite3 module (sqlite3 CLI unavailable):

```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()
cursor.execute('YOUR SQL HERE')
print(cursor.fetchall())
conn.close()
"
```

### Story Format

```markdown
**As a** [specific user role]
**I want** [specific capability]
**So that** [specific benefit]

**Acceptance Criteria:**
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

**Related context:** [Evidence from commits or gaps]
```

### Conflict Classification

| Type | Description |
|------|-------------|
| `duplicate` | Same capability, same scope |
| `scope_overlap` | Partial overlap in functionality |
| `competing` | Mutually exclusive approaches |
| `incompatible` | Cannot coexist in codebase |
| `false_positive` | Flagged but actually unrelated |

### Three-Field System

```
Stage:       concept → approved → planned → active → implemented → ready → released

Hold:        polish | wishlist (pauses progress, clears on resume)

Disposition: rejected | infeasible | deprecated | archived | legacy (terminal)
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Find capacity | `python .claude/scripts/story_workflow.py --ci` |
| Vet story | `python .claude/skills/story-vetting/candidate_detector.py --story-id ID` |
| View tree | `python .claude/skills/story-tree/scripts/tree-view.py` |

---

## References

- **CI Workflow:** `references/ci-workflow.md`
- **Interactive Workflow:** `references/interactive-workflow.md`
- **Story Writing:** `.claude/skills/story-writing/SKILL.md`
- **Story Vetting:** `.claude/skills/story-vetting/SKILL.md`
- **Goals:** `.claude/data/goals/goals.md`
