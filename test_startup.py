#!/usr/bin/env python3
"""Test that the application starts without hanging."""

import sys
import threading
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def test_startup():
    """Test app startup in a separate thread with timeout."""
    startup_success = []

    def run_app():
        try:
            import customtkinter as ctk
            from cv_focus_guard_ai_pomodoro.main import PomodoroTimer

            print("✓ Imports successful")
            startup_success.append(True)

            root = ctk.CTk()
            print("✓ CTk root created")

            app = PomodoroTimer(root)
            print("✓ PomodoroTimer instantiated")

            # Schedule a window close after 1 second
            root.after(1000, root.quit)
            print("✓ Close scheduled")

            # Run mainloop
            root.mainloop()
            print("✓ Mainloop completed successfully")

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback

            traceback.print_exc()

    # Run in thread with timeout
    app_thread = threading.Thread(target=run_app, daemon=True)
    app_thread.start()
    app_thread.join(timeout=5.0)

    if app_thread.is_alive():
        print("✗ App startup timed out (unresponsive)")
        return False

    if startup_success:
        print("\n✓ Startup test PASSED - app is responsive!")
        return True
    else:
        print("\n✗ Startup test FAILED - see errors above")
        return False


if __name__ == "__main__":
    success = test_startup()
    sys.exit(0 if success else 1)
