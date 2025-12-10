"""
Configuration management for LawTime Tracker.

Handles loading, saving, and accessing application settings from a JSON file.
Settings include polling intervals, thresholds, and file paths.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


# Default configuration values
DEFAULT_CONFIG = {
    "poll_interval_seconds": 1.0,
    "idle_threshold_seconds": 180,
    "merge_threshold_seconds": 2.0,
    "database_path": None,  # Will be set to default location if None
    "start_on_boot": False,
    "start_tracking_on_launch": True,
    # Screenshot settings (periodic)
    "screenshot_enabled": True,
    "screenshot_interval_seconds": 10,
    "screenshot_threshold_identical": 0.92,
    "screenshot_threshold_significant": 0.70,
    "screenshot_threshold_identical_same_window": 0.90,
    "screenshot_threshold_identical_different_window": 0.99,
    "screenshot_quality": 65,
    "screenshot_max_dimension": 1920,
    # Action screenshot settings
    "action_screenshot_enabled": True,
    "action_screenshot_throttle_seconds": 0.5,
    "action_screenshot_quality": 65,
    "action_screenshot_max_dimension": 1920
}


@dataclass
class Config:
    """
    Application configuration settings.

    Attributes:
        poll_interval_seconds: How often to check the active window (default: 1.0)
        idle_threshold_seconds: Seconds before marking as idle (default: 180)
        merge_threshold_seconds: Max gap to merge identical windows (default: 2.0)
        database_path: Path to SQLite database file (default: auto-detected)
        start_on_boot: Launch automatically on Windows startup (default: False)
        start_tracking_on_launch: Begin tracking when app starts (default: True)
        screenshot_enabled: Enable periodic screenshot capture (default: True)
        screenshot_interval_seconds: Seconds between screenshot attempts (default: 10)
        screenshot_threshold_identical: Similarity threshold to overwrite (≥0.92)
        screenshot_threshold_significant: Similarity threshold for new save (<0.70)
        screenshot_threshold_identical_same_window: Threshold when active window unchanged (default: 0.90)
        screenshot_threshold_identical_different_window: Threshold when active window changed (default: 0.99)
        screenshot_quality: JPEG quality 1-100 (default: 65)
        screenshot_max_dimension: Max width/height in pixels (default: 1920)
        action_screenshot_enabled: Enable action-based screenshot capture (default: True)
        action_screenshot_throttle_seconds: Minimum seconds between action screenshots (default: 0.5)
        action_screenshot_quality: JPEG quality for action screenshots (default: 65)
        action_screenshot_max_dimension: Max dimension for action screenshots (default: 1920)
    """
    poll_interval_seconds: float = 1.0
    idle_threshold_seconds: float = 180.0
    merge_threshold_seconds: float = 2.0
    database_path: Optional[str] = None
    start_on_boot: bool = False
    start_tracking_on_launch: bool = True
    # Screenshot settings (periodic)
    screenshot_enabled: bool = True
    screenshot_interval_seconds: float = 10.0
    screenshot_threshold_identical: float = 0.92
    screenshot_threshold_significant: float = 0.70
    screenshot_threshold_identical_same_window: float = 0.90
    screenshot_threshold_identical_different_window: float = 0.99
    screenshot_quality: int = 65
    screenshot_max_dimension: int = 1920
    # Action screenshot settings
    action_screenshot_enabled: bool = True
    action_screenshot_throttle_seconds: float = 0.5
    action_screenshot_quality: int = 65
    action_screenshot_max_dimension: int = 1920
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from dictionary."""
        # Filter only known fields
        valid_fields = {
            k: v for k, v in data.items() 
            if k in cls.__dataclass_fields__
        }
        return cls(**valid_fields)


class ConfigManager:
    """
    Manages loading and saving configuration from JSON file.
    
    Config file location:
    - Windows: %LOCALAPPDATA%\\TimeLawg\\config.json
    - Linux/Mac: ~/.config/timelawg/config.json
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
            self.config_path = self._get_default_config_path()
        
        self.config = self.load()
        
        logging.info(f"Configuration loaded from: {self.config_path}")
    
    @staticmethod
    def _get_default_config_path() -> Path:
        """
        Get the default configuration file path for the current platform.
        
        Returns:
            Path object pointing to config.json location
        """
        import sys
        import os
        
        if sys.platform == 'win32':
            # Windows: %LOCALAPPDATA%\TimeLawg\config.json
            appdata = os.environ.get('LOCALAPPDATA')
            if not appdata:
                # Fallback if LOCALAPPDATA not set
                appdata = Path.home() / 'AppData' / 'Local'
            else:
                appdata = Path(appdata)
            config_dir = appdata / 'TimeLawg'
        else:
            # Linux/Mac: ~/.config/timelawg/config.json
            config_dir = Path.home() / '.config' / 'timelawg'
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'config.json'
    
    @staticmethod
    def _get_default_database_path() -> Path:
        """
        Get the default database file path for the current platform.
        
        Returns:
            Path object pointing to lawtime.db location
        """
        import sys
        import os
        
        if sys.platform == 'win32':
            appdata = os.environ.get('LOCALAPPDATA')
            if not appdata:
                appdata = Path.home() / 'AppData' / 'Local'
            else:
                appdata = Path(appdata)
            db_dir = appdata / 'TimeLawg'
        else:
            db_dir = Path.home() / '.local' / 'share' / 'timelawg'
        
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / 'lawtime.db'
    
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
                config.database_path = str(self._get_default_database_path())
            
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
        self.config.database_path = str(self._get_default_database_path())
        
        self.save()
    
    def get_database_path(self) -> Path:
        """
        Get the database file path as a Path object.
        
        Returns:
            Path to the SQLite database file
        """
        if self.config.database_path:
            return Path(self.config.database_path)
        return self._get_default_database_path()


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
