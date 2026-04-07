"""
Google Drive Helper - Auto-detect Google Drive folder location

This module helps find the Google Drive folder on different systems
to enable easy collaboration without manual configuration.
"""

import os
from pathlib import Path
from typing import Optional
import platform


def find_google_drive_folder() -> Optional[Path]:
    """
    Auto-detect Google Drive Desktop folder location.

    Returns:
        Path to Google Drive folder if found, None otherwise
    """
    system = platform.system()

    if system == "Windows":
        # Common Windows locations for Google Drive
        possible_paths = [
            Path("G:") / "My Drive",  # Google Drive Desktop (G: drive)
            Path.home() / "Google Drive",
            Path.home() / "GoogleDrive",
            Path("G:"),  # Sometimes mapped as G: drive
            Path("C:") / "Users" / os.environ.get("USERNAME", "") / "Google Drive",
        ]
    elif system == "Darwin":  # macOS
        possible_paths = [
            Path.home() / "Google Drive",
            Path.home() / "GoogleDrive",
        ]
    else:  # Linux
        possible_paths = [
            Path.home() / "Google Drive",
            Path.home() / "GoogleDrive",
            Path.home() / "google-drive",
        ]

    # Check each possible path
    for path in possible_paths:
        if path.exists() and path.is_dir():
            return path.resolve()

    return None


def get_shared_collab_folder(folder_name: str = "Tomato") -> Optional[Path]:
    """
    Get the shared collaboration folder inside Google Drive.

    Args:
        folder_name: Name of the shared collaboration folder

    Returns:
        Path to the collaboration folder if found, None otherwise
    """
    gdrive_folder = find_google_drive_folder()

    if gdrive_folder is None:
        return None

    collab_folder = gdrive_folder / folder_name

    # Check if folder exists
    if collab_folder.exists() and collab_folder.is_dir():
        return collab_folder.resolve()

    return None


def setup_shared_folder(folder_name: str = "Tomato") -> tuple[bool, str]:
    """
    Try to set up the shared collaboration folder.

    Args:
        folder_name: Name of the shared collaboration folder

    Returns:
        Tuple of (success: bool, message: str)
    """
    gdrive_folder = find_google_drive_folder()

    if gdrive_folder is None:
        return (
            False,
            "Google Drive not found. Please install Google Drive Desktop and sync it.",
        )

    collab_folder = gdrive_folder / folder_name

    try:
        collab_folder.mkdir(parents=True, exist_ok=True)
        return (True, f"Collaboration folder created at: {collab_folder}")
    except Exception as e:
        return (False, f"Failed to create collaboration folder: {e}")


def get_collaboration_folder() -> Path:
    """
    Get the collaboration folder, falling back to local if Google Drive not available.

    Returns:
        Path to use for collaboration (Google Drive or local fallback)
    """
    # Try to get Google Drive folder first
    shared_folder = get_shared_collab_folder()

    if shared_folder is not None:
        return shared_folder

    # Fallback to local folder
    local_folder = Path(__file__).parent / "data" / "collaboration"
    local_folder.mkdir(parents=True, exist_ok=True)

    return local_folder


# Shared folder link for users to add to their Drive
# You should create this folder and share it publicly with edit access
SHARED_FOLDER_LINK = "https://drive.google.com/drive/folders/1v5hrC6zKTBC81EvYDr6FejSeWiYFbBBf?usp=sharing"

# Instructions for users who don't have the folder yet
SETUP_INSTRUCTIONS = """
📁 Google Drive Collaboration Setup

To collaborate with friends, follow these simple steps:

1. Install Google Drive Desktop (if not already installed):
   https://www.google.com/drive/download/

2. Add the shared collaboration folder:
   - Click this link: {link}
   - Click "Add to My Drive" 
   - Wait for Google Drive to sync (usually takes a few seconds)

3. Restart Focus Guard - it will automatically find the folder!

That's it! You can now create or join collaboration sessions.
""".format(link=SHARED_FOLDER_LINK)
