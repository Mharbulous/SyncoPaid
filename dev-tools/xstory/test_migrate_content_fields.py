"""Tests for migration script parsing logic."""

from migrate_content_fields import parse_description


def test_parse_description_with_full_content():
    description = """**As a** developer
**I want** to split fields
**So that** content is semantic

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

Additional context here."""

    story, criteria, remaining = parse_description(description)
    assert "As a developer" in story, f"Story check failed: {story}"
    assert "- [ ] Criterion 1" in criteria, f"Criteria check failed: {criteria}"
    assert "Additional context" in remaining, f"Remaining check failed: {remaining}"
    print("✓ All assertions passed")


if __name__ == "__main__":
    test_parse_description_with_full_content()
