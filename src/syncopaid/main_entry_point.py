"""
SyncoPaid - Main entry point setup.

Handles application initialization:
- Logging configuration
- Single instance enforcement
- Error handling
"""

import sys
import logging

from syncopaid.main_single_instance import acquire_single_instance, release_single_instance
from syncopaid.main_app_class import SyncoPaidApp


def main():
    """Main entry point for the application."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            # Optionally add file handler
            # logging.FileHandler('lawtime.log')
        ]
    )

    # Enforce single instance
    if not acquire_single_instance():
        print("SyncoPaid is already running.")
        print("Check your system tray for the existing instance.")
        sys.exit(0)

    try:
        app = SyncoPaidApp()
        app.run()

    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        release_single_instance()
        sys.exit(0)

    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        release_single_instance()
        sys.exit(1)
