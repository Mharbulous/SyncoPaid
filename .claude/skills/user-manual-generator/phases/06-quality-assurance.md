# Phase 6: Quality Assurance

Before finalizing documentation, perform these checks.

## Completeness Check

```bash
# List all documentation files created
find docs/ -name "*.md" | sort

# Count total words (approximate content volume)
find docs/ -name "*.md" -exec wc -w {} + | tail -1
```

### Verification Checklist

- [ ] All major features documented
- [ ] Installation guide present
- [ ] Quick start guide present
- [ ] At least 5 how-to guides
- [ ] Complete reference sections
- [ ] Troubleshooting guide present
- [ ] FAQ with at least 10 questions

## Link Validation

Check for broken internal links:

```bash
# Find all markdown links
grep -r "\[.*\](.*\.md)" docs/

# Check for common link errors
grep -r "\[.*\](.*/)" docs/  # Missing .md extension
grep -r "\[.*\](\.\..*)" docs/  # Relative paths (verify they're correct)
```

## Code Sample Validation

```bash
# Check for placeholder text that should be replaced
grep -r "TODO\|FIXME\|XXX\|\[Your.*\]" docs/

# Find all code blocks for manual testing
grep -r '```' docs/
```

If possible, extract and test code samples manually.

## Accessibility Check

- [ ] All images have alt text
- [ ] Headings follow hierarchy (no skipping levels)
- [ ] Code blocks have language specified
- [ ] Tables have headers
- [ ] Links have descriptive text (not "click here")

## Content Quality Review

For each major documentation file:

1. **Read the introduction**: Does it clearly state what the reader will learn?
2. **Check structure**: Are sections logically ordered?
3. **Verify examples**: Do they show realistic usage?
4. **Review tone**: Is it helpful and encouraging (not condescending)?
5. **Look for gaps**: Are there unexplained jumps in knowledge?

## Create TODO File

Create `docs/TODO.md` to track items needing manual work:

```markdown
# Documentation TODOs

## Screenshots Needed

- [ ] Getting Started > Installation: Screenshot of installer window
- [ ] Quick Start: Screenshot of successful first run

## Video Tutorials

- [ ] Complete walkthrough (5-10 minutes)
- [ ] [Feature] tutorial (2-3 minutes)

## Content Review

- [ ] Verify all API endpoint examples are correct
- [ ] Test all CLI command examples
- [ ] Update configuration defaults if they changed

## Confidence Levels

### High Confidence (verified against code)
- Installation requirements
- Configuration options

### Medium Confidence (inferred from patterns)
- User workflow descriptions
- Error message solutions

### Low Confidence (needs manual verification)
- [List anything uncertain]
```

## Build Test

Verify the site builds without errors:

```bash
# MkDocs
mkdocs build --strict

# Docusaurus
npm run build

# VitePress
npm run docs:build
```

Fix any build errors before proceeding.

## Next Phase

Once quality checks pass, proceed to **Phase 7: Handoff** by reading `phases/07-handoff.md`.
