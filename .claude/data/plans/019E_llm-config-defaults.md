# 019E: LLM & AI Integration - Config Defaults

**Story ID:** 8.5

## Task
Add LLM configuration settings to the config module.

## Context
Final step for LLM integration. Adds configuration options for LLM provider, API key path, and billing increment.

## Scope
- Add llm_provider to DEFAULT_CONFIG and Config
- Add llm_api_key to DEFAULT_CONFIG and Config
- Add billing_increment to DEFAULT_CONFIG and Config

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/config.py` | Add LLM config settings |
| `tests/test_config.py` | Add tests |

## Implementation

### Config Updates

```python
# src/syncopaid/config.py - add to DEFAULT_CONFIG
# LLM settings
'llm_provider': 'openai',  # 'openai' or 'anthropic'
'llm_api_key': '',         # API key (or env var name)
'billing_increment': 6,     # Minutes per billing increment (default: 6 = 0.1 hour)
```

```python
# src/syncopaid/config.py - add to Config dataclass
# LLM settings
llm_provider: str = 'openai'
llm_api_key: str = ''
billing_increment: int = 6
```

### Tests

```python
# tests/test_config.py (add)
def test_llm_config_defaults():
    from syncopaid.config import DEFAULT_CONFIG, ConfigManager
    import tempfile
    from pathlib import Path

    assert 'llm_provider' in DEFAULT_CONFIG
    assert DEFAULT_CONFIG['llm_provider'] == 'openai'
    assert 'billing_increment' in DEFAULT_CONFIG
    assert DEFAULT_CONFIG['billing_increment'] == 6

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.json"
        manager = ConfigManager(config_path=config_path)

        assert manager.config.llm_provider == 'openai'
        assert manager.config.billing_increment == 6
```

## Verification

```bash
pytest tests/test_config.py::test_llm_config_defaults -v
python -m syncopaid.config
```

## Final Verification

After all LLM sub-plans complete:

```bash
python -m pytest tests/test_llm.py -v
python -m pytest tests/test_billing.py -v
python -m pytest tests/test_review_ui.py -v
python -m pytest tests/ -v  # All tests
```

## Dependencies
- Task 019D (review UI)

## Notes
This completes the LLM & AI Integration feature (original story 8).

All acceptance criteria should now be met:
- LLM API integration for activity classification
- 6-minute billing increment rounding
- Billing narrative generation from activities
- Review UI for approving/editing entries
- Configurable LLM provider and billing settings
