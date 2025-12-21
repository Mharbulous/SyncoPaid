"""
Configuration management for SyncoPaid.

Handles loading, saving, and accessing application settings from a JSON file.
Settings include polling intervals, thresholds, and file paths.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from .config_defaults import DEFAULT_CONFIG
from .config_dataclass import Config
from .config_paths import get_default_config_path, get_default_database_path


class ConfigManager:
    """
    Manages loading and saving configuration from JSON file.

    Config file location:
    - Windows: %LOCALAPPDATA%\\SyncoPaid\\config.json
    - Linux/Mac: ~/.config/SyncoPaid/config.json
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config manager.

        Args:
            config_path: Custom path to config file. If None, uses default location.
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = get_default_config_path()

        self.config = self.load()

        logging.info(f"Configuration loaded from: {self.config_path}")

    def load(self) -> Config:
        """
        Load configuration from JSON file.

        If file doesn't exist, creates it with default values.

        Returns:
            Config object with loaded settings
        """
        if not self.config_path.exists():
            logging.info("Config file not found, creating with defaults")
            config = Config(**DEFAULT_CONFIG)
            self.save(config)
            return config

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            config = Config.from_dict(data)

            # Set default database path if not specified
            if config.database_path is None:
                config.database_path = str(get_default_database_path())

            return config

        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file: {e}")
            logging.info("Using default configuration")
            return Config(**DEFAULT_CONFIG)

        except Exception as e:
            logging.error(f"Error loading config: {e}")
            logging.info("Using default configuration")
            return Config(**DEFAULT_CONFIG)

    def save(self, config: Optional[Config] = None):
        """
        Save configuration to JSON file.

        Args:
            config: Config object to save. If None, saves current config.
        """
        if config is None:
            config = self.config

        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)

            logging.info(f"Configuration saved to: {self.config_path}")

        except Exception as e:
            logging.error(f"Error saving config: {e}")
            raise

    def update(self, **kwargs):
        """
        Update specific configuration values and save.

        Example:
            config_manager.update(idle_threshold_seconds=300)
        """
        config_dict = self.config.to_dict()

        for key, value in kwargs.items():
            if key in config_dict:
                config_dict[key] = value
                logging.info(f"Updated config: {key} = {value}")
            else:
                logging.warning(f"Unknown config key ignored: {key}")

        self.config = Config.from_dict(config_dict)
        self.save()

    def reset_to_defaults(self):
        """Reset configuration to default values."""
        logging.warning("Resetting configuration to defaults")
        self.config = Config(**DEFAULT_CONFIG)

        # Set default database path
        self.config.database_path = str(get_default_database_path())

        self.save()

    def get_database_path(self) -> Path:
        """
        Get the database file path as a Path object.

        Returns:
            Path to the SQLite database file
        """
        if self.config.database_path:
            return Path(self.config.database_path)
        return get_default_database_path()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_config(config: Config):
    """Pretty print configuration settings."""
    print("\nCurrent Configuration:")
    print("=" * 50)
    print(f"  Poll interval: {config.poll_interval_seconds}s")
    print(f"  Idle threshold: {config.idle_threshold_seconds}s ({config.idle_threshold_seconds/60:.1f} minutes)")
    print(f"  Merge threshold: {config.merge_threshold_seconds}s")
    print(f"  Database path: {config.database_path}")
    print(f"  Start on boot: {config.start_on_boot}")
    print(f"  Start tracking on launch: {config.start_tracking_on_launch}")
    print(f"  Screenshot enabled: {config.screenshot_enabled}")
    print(f"  Screenshot interval: {config.screenshot_interval_seconds}s")
    print(f"  Screenshot quality: {config.screenshot_quality}")
    print(f"  Transition prompts: {config.transition_prompt_enabled}")
    print(f"  Transition sensitivity: {config.transition_sensitivity}")
    print("=" * 50)


# ============================================================================
# MAIN - FOR STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    import tempfile
    import os

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("Testing ConfigManager...\n")

    # Test with temporary config file
    with tempfile.TemporaryDirectory() as tmpdir:
        test_config_path = Path(tmpdir) / "test_config.json"

        # Create new config manager
        print("1. Creating new config with defaults...")
        manager = ConfigManager(config_path=test_config_path)
        print_config(manager.config)

        # Update some settings
        print("\n2. Updating idle threshold to 5 minutes...")
        manager.update(idle_threshold_seconds=300)
        print_config(manager.config)

        # Reload to verify persistence
        print("\n3. Reloading config from file...")
        manager2 = ConfigManager(config_path=test_config_path)
        print_config(manager2.config)

        # Test reset
        print("\n4. Resetting to defaults...")
        manager2.reset_to_defaults()
        print_config(manager2.config)

        # Show raw JSON
        print("\n5. Raw JSON content:")
        with open(test_config_path, 'r') as f:
            print(f.read())

    print("\n✓ Configuration tests complete")
