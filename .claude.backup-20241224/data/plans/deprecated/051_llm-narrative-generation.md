# 051: LLM & AI Integration - Narrative Generation

## Task
Implement billing narrative generation from activity sequences using LLM.

## Context
Multiple activities for the same matter should be combined into a coherent billing narrative. The LLM summarizes related activities into professional billing descriptions.

## Scope
- Add generate_billing_narrative() to billing.py
- Use LLMClient to generate narrative from activities
- Combine related activities into single entry

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/billing.py` | Add narrative generation |
| `tests/test_billing.py` | Add tests |

## Implementation

```python
# src/syncopaid/billing.py (add)
from typing import Optional
from .llm import LLMClient


def generate_billing_narrative(
    activities: List[Dict],
    llm_client: Optional[LLMClient] = None
) -> str:
    """
    Generate a billing narrative from multiple activities.

    Combines related activities into a professional billing description
    suitable for client invoices.

    Args:
        activities: List of activity dicts with 'app' and 'title' keys
        llm_client: Optional LLM client for AI-powered generation

    Returns:
        Professional billing narrative string

    Example:
        activities = [
            {'app': 'Chrome', 'title': 'Estate Tax Research'},
            {'app': 'Word', 'title': 'Trust Amendment Draft.docx'}
        ]
        -> "Researched estate tax implications; drafted trust amendment"
    """
    if not activities:
        return ""

    # Combine activity descriptions
    combined = "; ".join([
        f"{a.get('app', 'Unknown')}: {a.get('title', 'No title')}"
        for a in activities
    ])

    if llm_client:
        # Use LLM to generate professional narrative
        try:
            result = llm_client.generate_narrative(combined)
            return result
        except Exception as e:
            logging.warning(f"LLM narrative generation failed: {e}")
            # Fall through to basic generation

    # Basic narrative without LLM
    return _generate_basic_narrative(activities)


def _generate_basic_narrative(activities: List[Dict]) -> str:
    """
    Generate a basic narrative without LLM.

    Extracts key terms from activities and formats them professionally.
    """
    terms = set()

    for activity in activities:
        title = activity.get('title', '')
        app = activity.get('app', '').lower()

        # Extract meaningful terms from title
        if title:
            # Remove file extensions and common suffixes
            clean_title = title.split(' - ')[0]  # Remove app name suffix
            clean_title = clean_title.replace('.docx', '').replace('.pdf', '')
            if clean_title:
                terms.add(clean_title)

        # Add app-specific context
        if 'word' in app or 'winword' in app:
            terms.add('document drafting')
        elif 'outlook' in app:
            terms.add('correspondence')
        elif 'chrome' in app or 'edge' in app or 'firefox' in app:
            terms.add('research')
        elif 'excel' in app:
            terms.add('data analysis')

    if terms:
        return "; ".join(sorted(terms)[:5])  # Limit to 5 terms

    return "General work activities"
```

Add to LLMClient:

```python
# src/syncopaid/llm.py (add to LLMClient class)
def generate_narrative(self, activity_summary: str) -> str:
    """
    Generate professional billing narrative from activity summary.

    Args:
        activity_summary: Combined description of activities

    Returns:
        Professional billing narrative string
    """
    prompt = f"""Convert these work activities into a professional billing narrative:

Activities: {activity_summary}

Respond with only the narrative text, no JSON. Keep it concise (1-2 sentences)."""

    return self._call_api(prompt).strip()
```

### Tests

```python
# tests/test_billing.py (add)
def test_generate_narrative():
    from syncopaid.billing import generate_billing_narrative

    activities = [
        {'app': 'Chrome', 'title': 'Estate Tax Research'},
        {'app': 'Word', 'title': 'Trust Amendment Draft.docx'}
    ]
    narrative = generate_billing_narrative(activities)

    assert narrative != ""
    assert len(narrative) > 0


def test_generate_narrative_empty():
    from syncopaid.billing import generate_billing_narrative
    assert generate_billing_narrative([]) == ""


def test_generate_basic_narrative():
    from syncopaid.billing import _generate_basic_narrative

    activities = [
        {'app': 'WINWORD.EXE', 'title': 'Contract Review.docx'}
    ]
    narrative = _generate_basic_narrative(activities)

    assert 'document drafting' in narrative or 'Contract Review' in narrative
```

## Verification

```bash
pytest tests/test_billing.py -v
```

## Dependencies
- Task 050 (billing rounding)
- Task 049 (LLM client) for AI-powered generation

## Next Task
After this: `052_llm-review-ui.md`
