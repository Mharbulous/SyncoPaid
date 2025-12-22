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
