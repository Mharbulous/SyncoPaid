# Enhance User Manual Generator Skill with Research Best Practices - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 21.1 | **Created:** 2025-12-23 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Enhance the user-manual-generator skill with research-backed best practices for sentence length, paragraph structure, screenshots, progressive disclosure, searchability, anti-patterns, and authoritative references.

**Approach:** Add new sections to existing skill documentation files (phases/04-content-generation.md, phases/05-static-site-setup.md, reference/best-practices.md) with specific guidance from technical writing research. No code changes—only markdown documentation updates.

**Tech Stack:** Markdown documentation files within `.claude/skills/user-manual-generator/`

---

## Story Context

**Title:** Enhance Skill with Research Best Practices

**Description:** As a documentation maintainer, I want the user-manual-generator skill to incorporate all verified best practices from our research so that every generated manual automatically follows industry standards.

**Acceptance Criteria:**
- [ ] Add sentence length guidance (15-20 word average) to content generation phase
- [ ] Add paragraph structure guidance (2-3 sentences, one topic per paragraph)
- [ ] Add screenshot annotation rules (3-4 max annotations, only for non-obvious elements)
- [ ] Add progressive disclosure patterns (accordions, expandable sections, max 2 levels)
- [ ] Add searchability requirements to SSG setup phase
- [ ] Add explicit anti-pattern warnings (lengthy intros, walls of text, mixing content types)
- [ ] Reference authoritative sources (Google/Microsoft style guides, Diataxis, Plain Language Act)

## Prerequisites

- [ ] Virtual environment activated: `venv\Scripts\activate` (or `source venv/bin/activate` on Linux)
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `.claude/skills/user-manual-generator/phases/04-content-generation.md` | Modify | Add sentence/paragraph/screenshot/anti-pattern guidance |
| `.claude/skills/user-manual-generator/phases/05-static-site-setup.md` | Modify | Add searchability requirements and progressive disclosure |
| `.claude/skills/user-manual-generator/reference/best-practices.md` | Modify | Add authoritative sources section |
| `tests/test_skill_content.py` | Create | Verify skill files contain required best practices |

## TDD Tasks

### Task 1: Create Test File for Best Practices Verification (~3 min)

**Files:**
- Create: `tests/test_skill_content.py`

**Context:** Before modifying skill files, we create a test that verifies the expected best practices content exists. This test will initially fail (RED), then pass after we add the content.

**Step 1 - RED:** Write failing test

```python
# tests/test_skill_content.py
"""Tests to verify user-manual-generator skill contains required best practices."""
import os


def read_file(path: str) -> str:
    """Read file content as string."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


class TestContentGenerationPhase:
    """Tests for phases/04-content-generation.md content."""

    PHASE_FILE = '.claude/skills/user-manual-generator/phases/04-content-generation.md'

    def test_sentence_length_guidance_exists(self):
        """Verify sentence length guidance (15-20 words) is documented."""
        content = read_file(self.PHASE_FILE)
        assert '15-20' in content or '15 to 20' in content, \
            "Missing sentence length guidance (15-20 word average)"
        assert 'sentence' in content.lower(), \
            "Missing sentence length section"

    def test_paragraph_structure_guidance_exists(self):
        """Verify paragraph structure guidance (2-3 sentences) is documented."""
        content = read_file(self.PHASE_FILE)
        assert '2-3 sentence' in content.lower() or '2 to 3 sentence' in content.lower(), \
            "Missing paragraph structure guidance (2-3 sentences per paragraph)"

    def test_screenshot_annotation_rules_exist(self):
        """Verify screenshot annotation rules (3-4 max) are documented."""
        content = read_file(self.PHASE_FILE)
        assert 'annotation' in content.lower(), \
            "Missing screenshot annotation guidance"
        assert '3-4' in content or '3 to 4' in content, \
            "Missing annotation limit (3-4 max)"

    def test_anti_pattern_warnings_exist(self):
        """Verify explicit anti-pattern warnings are documented."""
        content = read_file(self.PHASE_FILE)
        assert 'anti-pattern' in content.lower() or 'avoid' in content.lower(), \
            "Missing anti-pattern warnings section"
        # Check for specific anti-patterns
        content_lower = content.lower()
        assert 'wall' in content_lower or 'lengthy intro' in content_lower, \
            "Missing specific anti-pattern examples"


class TestStaticSiteSetupPhase:
    """Tests for phases/05-static-site-setup.md content."""

    PHASE_FILE = '.claude/skills/user-manual-generator/phases/05-static-site-setup.md'

    def test_searchability_requirements_exist(self):
        """Verify searchability requirements are documented."""
        content = read_file(self.PHASE_FILE)
        assert 'search' in content.lower(), \
            "Missing searchability requirements"

    def test_progressive_disclosure_patterns_exist(self):
        """Verify progressive disclosure patterns are documented."""
        content = read_file(self.PHASE_FILE)
        content_lower = content.lower()
        assert 'progressive disclosure' in content_lower or 'accordion' in content_lower or 'expandable' in content_lower, \
            "Missing progressive disclosure patterns"


class TestBestPracticesReference:
    """Tests for reference/best-practices.md content."""

    REF_FILE = '.claude/skills/user-manual-generator/reference/best-practices.md'

    def test_authoritative_sources_exist(self):
        """Verify authoritative sources are referenced."""
        content = read_file(self.REF_FILE)
        content_lower = content.lower()
        # Check for key authoritative sources
        has_google = 'google' in content_lower
        has_microsoft = 'microsoft' in content_lower
        has_diataxis = 'diataxis' in content_lower
        has_plain_language = 'plain language' in content_lower

        assert has_google or has_microsoft, \
            "Missing reference to Google or Microsoft style guides"
        assert has_diataxis, \
            "Missing reference to Diataxis framework"
        assert has_plain_language, \
            "Missing reference to Plain Language Act/guidelines"
```

**Step 2 - Verify RED:**
```bash
python -m pytest tests/test_skill_content.py -v
```
Expected output: `FAILED` - tests fail because best practices content doesn't exist yet in skill files

**Step 3 - GREEN:** No implementation yet (tests are meant to fail initially)

**Step 4 - Verify RED confirmed:**
```bash
python -m pytest tests/test_skill_content.py -v 2>&1 | head -40
```
Expected output: Multiple `FAILED` assertions

**Step 5 - COMMIT:**
```bash
git add tests/test_skill_content.py && git commit -m "test: add verification tests for skill best practices content"
```

---

### Task 2: Add Sentence and Paragraph Guidance to Content Generation (~3 min)

**Files:**
- Modify: `.claude/skills/user-manual-generator/phases/04-content-generation.md:7-25`

**Context:** Add specific guidance on sentence length (15-20 words average) and paragraph structure (2-3 sentences, one topic per paragraph) to the Writing Guidelines section.

**Step 1 - Locate insertion point:** After line 10 (after "### 1. User-Focused Language" section starts)

**Step 2 - GREEN:** Add new content by replacing the existing "### 1. User-Focused Language" section with enhanced version

Find this block (lines 7-10):
```markdown
### 1. User-Focused Language
- Use "you" and "your" (not "the user")
- Active voice ("Click the button" not "The button should be clicked")
- Present tense ("The system saves your data" not "will save")
```

Replace with:
```markdown
### 1. User-Focused Language
- Use "you" and "your" (not "the user")
- Active voice ("Click the button" not "The button should be clicked")
- Present tense ("The system saves your data" not "will save")
- Simple words (avoid jargon or explain it immediately)
- **Sentence length:** Target 15-20 words average per sentence. Vary length for rhythm but break up sentences over 25 words.
- **Paragraph structure:** Keep paragraphs to 2-3 sentences maximum. Each paragraph covers one topic only. Use blank lines between paragraphs.
```

**Step 3 - Verify partial GREEN:**
```bash
python -m pytest tests/test_skill_content.py::TestContentGenerationPhase::test_sentence_length_guidance_exists -v
python -m pytest tests/test_skill_content.py::TestContentGenerationPhase::test_paragraph_structure_guidance_exists -v
```
Expected output: Both tests `PASSED`

**Step 4 - COMMIT:**
```bash
git add .claude/skills/user-manual-generator/phases/04-content-generation.md && git commit -m "docs: add sentence length and paragraph structure guidance to content generation"
```

---

### Task 3: Add Screenshot Annotation Rules (~3 min)

**Files:**
- Modify: `.claude/skills/user-manual-generator/phases/04-content-generation.md:57-70`

**Context:** Add screenshot annotation guidance after the existing "## Placeholder Format" section with specific rules about annotation limits.

**Step 1 - Locate insertion point:** After the "## Placeholder Format" section (around line 70)

**Step 2 - GREEN:** Add new section after the placeholder format section. Find line 70 that ends with:
```markdown
> **Duration**: [Suggested length, e.g., "2-3 minutes"]
```

Add after it:
```markdown

### Screenshot Annotation Guidelines

When annotating screenshots for documentation:

- **Limit annotations:** Maximum 3-4 annotations per screenshot. More creates visual clutter.
- **Annotate only non-obvious elements:** Skip labeling clearly visible buttons with clear text labels.
- **Use consistent annotation style:** Choose one style (arrows, numbered callouts, highlight boxes) per document.
- **Place annotations outside key content:** Don't obscure important UI elements.

**Good annotation targets:**
- Hidden menus or dropdowns
- Small icons without labels
- Settings in crowded interfaces
- Non-obvious interaction points

**Skip annotating:**
- Large, labeled buttons
- Text that speaks for itself
- Standard browser/OS elements
```

**Step 3 - Verify GREEN:**
```bash
python -m pytest tests/test_skill_content.py::TestContentGenerationPhase::test_screenshot_annotation_rules_exist -v
```
Expected output: `PASSED`

**Step 4 - COMMIT:**
```bash
git add .claude/skills/user-manual-generator/phases/04-content-generation.md && git commit -m "docs: add screenshot annotation rules (3-4 max, non-obvious only)"
```

---

### Task 4: Add Anti-Pattern Warnings (~3 min)

**Files:**
- Modify: `.claude/skills/user-manual-generator/phases/04-content-generation.md`

**Context:** Add explicit anti-pattern warnings section before the "## Quality Checklist Per File" section.

**Step 1 - Locate insertion point:** Before "## Quality Checklist Per File" (around line 72)

**Step 2 - GREEN:** Add new section. Find the line:
```markdown
## Quality Checklist Per File
```

Add before it:
```markdown
## Anti-Patterns to Avoid

These common mistakes reduce documentation effectiveness:

| Anti-Pattern | Problem | Instead |
|-------------|---------|---------|
| Lengthy introductions | Readers skip to content | Start with what they'll accomplish |
| Walls of text | Readers skim and miss info | Break into 2-3 sentence paragraphs |
| Mixing content types | Confuses reader expectations | Keep tutorials separate from reference |
| Clever headings | Readers can't scan | Use descriptive, action-oriented headings |
| Burying the lead | Key info gets missed | Put most important point first |
| Over-explaining basics | Wastes expert time | Link to prerequisites instead |

**Warning signs you're writing an anti-pattern:**
- Paragraph has more than 4 sentences
- Introduction is longer than 2 sentences
- Same page has step-by-step instructions AND reference tables
- Heading requires reading the content to understand

```

**Step 3 - Verify GREEN:**
```bash
python -m pytest tests/test_skill_content.py::TestContentGenerationPhase::test_anti_pattern_warnings_exist -v
```
Expected output: `PASSED`

**Step 4 - COMMIT:**
```bash
git add .claude/skills/user-manual-generator/phases/04-content-generation.md && git commit -m "docs: add explicit anti-pattern warnings section"
```

---

### Task 5: Add Searchability Requirements to SSG Setup (~3 min)

**Files:**
- Modify: `.claude/skills/user-manual-generator/phases/05-static-site-setup.md`

**Context:** Add searchability requirements to the static site setup phase, ensuring generated documentation is discoverable.

**Step 1 - Locate insertion point:** After "## Common Setup Steps" section header (around line 27)

**Step 2 - GREEN:** Find the line:
```markdown
## Common Setup Steps
```

Add after it (before "### 1. Create Documentation Directory"):
```markdown

### Search Configuration

Enable and optimize search functionality:

| SSG | Search Solution | Configuration |
|-----|-----------------|---------------|
| MkDocs Material | Built-in search | Enabled by default, add `search` to plugins |
| Docusaurus | Algolia or local | Configure in `docusaurus.config.js` |
| VitePress | Built-in search | Enabled by default |
| Plain Markdown | GitHub search | No configuration needed |

**Searchability requirements:**
- Enable full-text search across all documentation
- Ensure headings and code blocks are indexed
- Configure search to show context snippets
- Add `meta` descriptions to each page for search relevance

```

**Step 3 - Verify GREEN:**
```bash
python -m pytest tests/test_skill_content.py::TestStaticSiteSetupPhase::test_searchability_requirements_exist -v
```
Expected output: `PASSED`

**Step 4 - COMMIT:**
```bash
git add .claude/skills/user-manual-generator/phases/05-static-site-setup.md && git commit -m "docs: add searchability requirements to SSG setup phase"
```

---

### Task 6: Add Progressive Disclosure Patterns (~3 min)

**Files:**
- Modify: `.claude/skills/user-manual-generator/phases/05-static-site-setup.md`

**Context:** Add progressive disclosure patterns (accordions, expandable sections) guidance to help structure complex information.

**Step 1 - Locate insertion point:** After the searchability section added in Task 5

**Step 2 - GREEN:** Add after the searchability requirements section:
```markdown

### Progressive Disclosure Patterns

Use progressive disclosure to avoid overwhelming readers:

**Accordion/Expandable Sections:**
- Use for optional details, advanced configuration, or troubleshooting
- Maximum 2 levels of nesting (parent accordion → child content, no nested accordions)
- Default state: collapsed for optional content, expanded for required content

**Implementation by SSG:**

| SSG | Accordion Syntax |
|-----|-----------------|
| MkDocs Material | Use `??? note "Title"` or `???+ note "Title"` (expanded) |
| Docusaurus | Use `<details><summary>Title</summary>Content</details>` |
| VitePress | Use HTML `<details>` element |
| Plain Markdown | Use HTML `<details>` (GitHub renders natively) |

**When to use progressive disclosure:**
- Technical details that only power users need
- Platform-specific instructions (show only relevant platform)
- Error troubleshooting steps
- Full configuration reference (collapsed by default)

**When NOT to use:**
- Critical setup steps
- Security warnings
- Primary task instructions

```

**Step 3 - Verify GREEN:**
```bash
python -m pytest tests/test_skill_content.py::TestStaticSiteSetupPhase::test_progressive_disclosure_patterns_exist -v
```
Expected output: `PASSED`

**Step 4 - COMMIT:**
```bash
git add .claude/skills/user-manual-generator/phases/05-static-site-setup.md && git commit -m "docs: add progressive disclosure patterns (accordions, max 2 levels)"
```

---

### Task 7: Add Authoritative Sources to Best Practices (~3 min)

**Files:**
- Modify: `.claude/skills/user-manual-generator/reference/best-practices.md`

**Context:** Add a new section referencing authoritative sources for documentation best practices.

**Step 1 - Locate insertion point:** At the end of the file (after line 144)

**Step 2 - GREEN:** Add new section at end of file:
```markdown

## Authoritative Sources

This skill incorporates best practices from these established standards:

### Style Guides

| Source | Focus | Key Contributions |
|--------|-------|-------------------|
| [Google Developer Documentation Style Guide](https://developers.google.com/style) | Technical writing | Voice, formatting, word choice |
| [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/welcome/) | General and technical | Accessibility, global readiness |
| [Plain Language Action and Information Network](https://www.plainlanguage.gov/) | Government/legal | Clarity for non-technical audiences |

### Frameworks

| Framework | Purpose | Application |
|-----------|---------|-------------|
| [Diataxis](https://diataxis.fr/) | Documentation structure | Four documentation types: tutorials, how-to guides, reference, explanation |

### Research-Backed Guidelines

These specific recommendations are derived from usability research:

- **15-20 word sentences:** Based on readability studies showing comprehension drops significantly above 25 words
- **2-3 sentence paragraphs:** Web usability research shows scannable content improves task completion
- **3-4 annotation limit:** Visual attention research indicates more annotations create cognitive overload
- **Progressive disclosure:** Information architecture principle reducing initial cognitive load

When generating documentation, prioritize these sources in order:
1. Plain Language guidelines (for accessibility)
2. Diataxis framework (for structure)
3. Google/Microsoft guides (for technical accuracy)
```

**Step 3 - Verify GREEN:**
```bash
python -m pytest tests/test_skill_content.py::TestBestPracticesReference::test_authoritative_sources_exist -v
```
Expected output: `PASSED`

**Step 4 - COMMIT:**
```bash
git add .claude/skills/user-manual-generator/reference/best-practices.md && git commit -m "docs: add authoritative sources (Google, Microsoft, Diataxis, Plain Language)"
```

---

### Task 8: Run All Tests and Final Verification (~2 min)

**Files:**
- Test: `tests/test_skill_content.py`

**Context:** Verify all acceptance criteria are met by running the complete test suite.

**Step 1 - Run all tests:**
```bash
python -m pytest tests/test_skill_content.py -v
```
Expected output: All tests `PASSED` (7 tests)

**Step 2 - Verify baseline tests still pass:**
```bash
python -m pytest -v
```
Expected output: All existing tests pass

**Step 3 - Final verification - check files were modified:**
```bash
git diff --stat HEAD~7
```
Expected: Shows 4 files modified (3 skill docs + 1 test file)

**Step 4 - COMMIT (if any cleanup needed):**
```bash
# Only if cleanup was needed
git add -A && git commit -m "chore: final cleanup for story 21.1"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_skill_content.py -v   # All 7 tests pass
python -m pytest -v                                 # No regressions
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- All changes are documentation-only (markdown files)
- No Python code changes to the actual SyncoPaid application
- Tests verify content exists in skill documentation files
- Future stories (21.2-21.7) will use these enhanced best practices when generating actual user documentation
