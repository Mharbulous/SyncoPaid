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
