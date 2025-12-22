"""
Single-instance enforcement for SyncoPaid.

Uses Windows mutex to ensure only one instance of the application runs at a time.
Supports graceful takeover: new instance can signal old instance to shut down.
"""

import ctypes
import logging
import threading
import time

# Single-instance enforcement using Windows mutex and event
_MUTEX_NAME = "SyncoPaidTracker_SingleInstance_Mutex"
_EVENT_NAME = "SyncoPaidTracker_Shutdown_Event"
_mutex_handle = None
_event_handle = None
_shutdown_monitor_thread = None
_shutdown_callback = None


def acquire_single_instance(request_takeover: bool = True, takeover_timeout: float = 10.0):
    """
    Acquire a Windows mutex to ensure only one instance runs.

    If another instance is running and request_takeover is True, signals
    the old instance to shut down gracefully and waits for it to exit.

    Args:
        request_takeover: If True, request old instance to shut down
        takeover_timeout: Seconds to wait for old instance to exit

    Returns:
        True if this instance can proceed, False if takeover failed.
    """
    global _mutex_handle, _event_handle

    kernel32 = ctypes.windll.kernel32
    ERROR_ALREADY_EXISTS = 183
    WAIT_OBJECT_0 = 0
    WAIT_TIMEOUT = 258

    # Create named mutex
    _mutex_handle = kernel32.CreateMutexW(None, True, _MUTEX_NAME)

    # Check if mutex already existed (another instance is running)
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        if _mutex_handle:
            kernel32.CloseHandle(_mutex_handle)
            _mutex_handle = None

        if not request_takeover:
            return False

        # Signal the old instance to shut down via named event
        logging.info("Another instance detected - requesting graceful shutdown...")
        print("Another instance of SyncoPaid is running.")
        print("Requesting graceful shutdown of existing instance...")

        # Open or create the shutdown event and signal it
        EVENT_MODIFY_STATE = 0x0002
        event = kernel32.OpenEventW(EVENT_MODIFY_STATE, False, _EVENT_NAME)
        if event:
            kernel32.SetEvent(event)
            kernel32.CloseHandle(event)
        else:
            # Event doesn't exist yet - old instance may not support takeover
            logging.warning("Shutdown event not found - old instance may not support takeover")
            print("The existing instance doesn't support graceful takeover.")
            print("Please close it manually and try again.")
            return False

        # Wait for the old instance to release the mutex
        wait_start = time.time()
        while time.time() - wait_start < takeover_timeout:
            # Try to acquire the mutex again
            _mutex_handle = kernel32.CreateMutexW(None, True, _MUTEX_NAME)
            if kernel32.GetLastError() != ERROR_ALREADY_EXISTS:
                # Successfully acquired - old instance has exited
                logging.info("Previous instance shut down - takeover successful")
                print("Takeover successful. Starting new instance...")
                break
            else:
                kernel32.CloseHandle(_mutex_handle)
                _mutex_handle = None
                time.sleep(0.5)
        else:
            # Timeout - old instance didn't shut down in time
            logging.error(f"Takeover failed - old instance didn't shut down within {takeover_timeout}s")
            print(f"Takeover failed - existing instance didn't shut down within {takeover_timeout} seconds.")
            print("Please close it manually and try again.")
            return False

    # Create the shutdown event for future takeover requests
    # EVENT_ALL_ACCESS = 0x1F0003
    _event_handle = kernel32.CreateEventW(None, True, False, _EVENT_NAME)
    if not _event_handle:
        logging.warning("Could not create shutdown event")

    return True


def start_shutdown_monitor(shutdown_callback):
    """
    Start a background thread that monitors for shutdown requests from new instances.

    Args:
        shutdown_callback: Function to call when shutdown is requested (e.g., app.quit_app)
    """
    global _shutdown_monitor_thread, _shutdown_callback

    if not _event_handle:
        logging.warning("No shutdown event - monitor not started")
        return

    _shutdown_callback = shutdown_callback

    def monitor_loop():
        """Monitor the shutdown event and trigger callback when signaled."""
        kernel32 = ctypes.windll.kernel32
        WAIT_OBJECT_0 = 0
        INFINITE = 0xFFFFFFFF

        logging.info("Shutdown monitor started")

        # Wait for the event to be signaled (blocks until signaled)
        result = kernel32.WaitForSingleObject(_event_handle, INFINITE)

        if result == WAIT_OBJECT_0:
            logging.info("Shutdown signal received from new instance")
            print("\n" + "="*50)
            print("Shutdown requested by new instance...")
            print("Closing gracefully...")
            print("="*50 + "\n")

            if _shutdown_callback:
                # Call the shutdown callback (this should trigger graceful exit)
                _shutdown_callback()

    _shutdown_monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    _shutdown_monitor_thread.start()


def release_single_instance():
    """Release the Windows mutex and close the shutdown event."""
    global _mutex_handle, _event_handle

    kernel32 = ctypes.windll.kernel32

    if _event_handle:
        kernel32.CloseHandle(_event_handle)
        _event_handle = None

    if _mutex_handle:
        kernel32.ReleaseMutex(_mutex_handle)
        kernel32.CloseHandle(_mutex_handle)
        _mutex_handle = None
