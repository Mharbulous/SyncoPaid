# Validation - Pre-Insertion Quality Checks

Validate stories before insertion to catch issues early.

---

## Validation Checklist

Run these checks **before** inserting a story into the database:

### 1. User Story Format

```
✓ Has "As a [role]" with specific role (not generic "user")
✓ Has "I want [capability]" with concrete action
✓ Has "So that [benefit]" with measurable outcome
```

**Fail if:**
- Role is generic ("user", "someone", "anyone")
- Capability is vague ("do things", "use the system")
- Benefit is missing or circular

### 2. Acceptance Criteria

```
✓ Has 3+ acceptance criteria
✓ Each criterion is testable (can verify pass/fail)
✓ Criteria are specific (no "should work correctly")
✓ Criteria don't duplicate each other
```

**Fail if:**
- Fewer than 3 criteria
- Any criterion is untestable
- Criteria are vague or redundant

### 3. Evidence Grounding

```
✓ Story references commits OR identifies specific gap
✓ Evidence is cited in "Related context" section
✓ Evidence actually supports the story (not tangential)
```

**Fail if:**
- No evidence cited
- Evidence doesn't relate to story scope
- Story is purely speculative

### 4. Scope Containment

```
✓ Story decomposes parent scope (doesn't expand it)
✓ Story fits within parent's domain
✓ Story doesn't overlap with siblings
```

**Fail if:**
- Story scope exceeds parent scope
- Story belongs under different parent
- Story duplicates sibling functionality

### 5. ID Format

```
✓ Root children use plain integer format
✓ Nested children use parent.N format
✓ ID doesn't already exist
```

**Fail if:**
- Root child uses `root.N` format
- Nested child missing parent prefix
- ID collision with existing story

### 6. Goals Alignment (if goals files exist)

```
✓ Aligns with core capabilities in goals.md
✓ No conflict with exclusions in non-goals.md
✓ Follows guiding principles
```

**Fail if:**
- Contradicts stated goals
- Implements something in non-goals
- Violates guiding principles

---

## Validation Script

Run all checks programmatically:

```python
python -c "
import sqlite3, json, re

def validate_story(story_id, title, description, parent_id):
    errors = []

    # Check 1: User story format
    if not re.search(r'\*\*As a\*\*\s+\w+', description):
        errors.append('Missing or invalid \"As a\" clause')
    if 'as a user' in description.lower():
        errors.append('Generic \"user\" role - use specific role')
    if not re.search(r'\*\*I want\*\*\s+\w+', description):
        errors.append('Missing or invalid \"I want\" clause')
    if not re.search(r'\*\*So that\*\*\s+\w+', description):
        errors.append('Missing or invalid \"So that\" clause')

    # Check 2: Acceptance criteria
    criteria = re.findall(r'- \[ \]', description)
    if len(criteria) < 3:
        errors.append(f'Only {len(criteria)} acceptance criteria (need 3+)')

    # Check 3: Evidence (Related context)
    if 'Related context' not in description and 'Evidence' not in description:
        errors.append('Missing evidence/related context section')

    # Check 4: ID format
    if parent_id == 'root':
        if '.' in story_id:
            errors.append('Root children must use plain integer ID')
    else:
        if not story_id.startswith(parent_id + '.'):
            errors.append(f'ID must start with parent prefix: {parent_id}.')

    # Check 5: ID uniqueness
    conn = sqlite3.connect('.claude/data/story-tree.db')
    exists = conn.execute('SELECT 1 FROM story_nodes WHERE id = ?', (story_id,)).fetchone()
    if exists:
        errors.append(f'ID {story_id} already exists')
    conn.close()

    return errors

# Example usage:
# errors = validate_story('1.5', 'My Story', description_text, '1')
# if errors: print('VALIDATION FAILED:', errors)
# else: print('VALIDATION PASSED')
"
```

---

## Validation Workflow

### Before Generation

1. Check `hold_reason='polish'` stories first
2. Gather context (goals, commits, existing children)
3. Identify gaps using gap-analysis methodology

### During Generation

1. Apply user story template
2. Ensure specific role from context
3. Write testable acceptance criteria
4. Cite evidence

### After Generation, Before Insertion

1. Run validation checks
2. If any fail → fix and re-validate
3. Only insert after all checks pass

### After Insertion

1. Proceed to vetting (duplicate detection)
2. This is separate from validation

---

## Validation vs Vetting

| Aspect | Validation | Vetting |
|--------|------------|---------|
| **When** | Before insertion | After insertion |
| **What** | Story quality | Duplicate detection |
| **Checks** | Format, evidence, scope | Conflicts with existing stories |
| **Failure** | Fix and retry | Delete/merge and retry |

Both are required. Validation catches quality issues. Vetting catches conflicts.

---

## Common Validation Failures

| Failure | Fix |
|---------|-----|
| Generic "user" role | Look at goals.md or codebase for specific roles |
| Fewer than 3 criteria | Add more specific, testable criteria |
| No evidence cited | Reference commits or identify specific gap |
| Scope exceeds parent | Narrow scope or find correct parent |
| Wrong ID format | Use id-generation.md rules |
