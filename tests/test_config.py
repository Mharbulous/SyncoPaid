"""Tests for configuration management."""

import tempfile
from pathlib import Path
from syncopaid.config import ConfigManager


def test_ui_automation_config_defaults():
    """Test that UI automation config defaults are set correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.json"
        manager = ConfigManager(config_path=config_path)

        assert manager.config.ui_automation_enabled == True
        assert manager.config.ui_automation_outlook_enabled == True
        assert manager.config.ui_automation_explorer_enabled == True


def test_transition_config_defaults():
    """Test that transition detection config defaults are set correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.json"
        manager = ConfigManager(config_path=config_path)

        assert manager.config.transition_prompt_enabled == True
        assert manager.config.transition_sensitivity == "moderate"
        assert manager.config.transition_never_prompt_apps == ["WINWORD.EXE", "EXCEL.EXE", "Teams.exe", "Zoom.exe"]


def test_archive_config_defaults():
    """Test config includes archive settings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.json"
        manager = ConfigManager(config_path=config_path)

        assert manager.config.archive_enabled == True
        assert manager.config.archive_check_interval_hours == 24


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


def test_default_config_has_url_extraction_enabled():
    """Default config should enable URL extraction."""
    from syncopaid.config import DEFAULT_CONFIG
    assert "url_extraction_enabled" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["url_extraction_enabled"] is True
