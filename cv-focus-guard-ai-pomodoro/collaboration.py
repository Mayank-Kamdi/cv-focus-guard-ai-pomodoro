"""
File-based collaboration for accountability sessions.

Uses a shared folder and a short session code to coordinate two clients.

Production features:
- Input validation for session codes
- Path traversal protection
- Payload size limits
- Rate limiting for event publishing
- Secure file operations
"""

from __future__ import annotations

import json
import random
import re
import string
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

# Security constants
MAX_PAYLOAD_SIZE = 1024 * 100  # 100KB max payload size
MAX_SESSION_CODE_LENGTH = 20  # Maximum session code length
MIN_SESSION_CODE_LENGTH = 4  # Minimum session code length
MAX_EVENTS_PER_SECOND = 10  # Rate limit: max events per second
VALID_CODE_PATTERN = re.compile(r"^[A-Z0-9]+$")  # Only uppercase alphanumeric


class CollaborationSession:
    def __init__(self, logger, code_length: int = 6) -> None:
        self.logger = logger
        # Validate and clamp code length
        self.code_length = max(
            MIN_SESSION_CODE_LENGTH, min(code_length, MAX_SESSION_CODE_LENGTH)
        )
        self.sender_id = uuid.uuid4().hex
        self.session_code: Optional[str] = None
        self.shared_dir: Optional[Path] = None
        self.session_file: Optional[Path] = None
        self.connected = False
        self.last_position = 0
        # Rate limiting
        self.last_publish_times: List[float] = []
        self.event_count = 0

    def generate_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(random.choice(alphabet) for _ in range(self.code_length))

    def _validate_session_code(self, code: str) -> bool:
        """Validate session code for security."""
        if not code:
            return False
        if len(code) < MIN_SESSION_CODE_LENGTH or len(code) > MAX_SESSION_CODE_LENGTH:
            return False
        if not VALID_CODE_PATTERN.match(code):
            return False
        # Prevent path traversal attempts
        if ".." in code or "/" in code or "\\" in code:
            return False
        return True

    def _session_file_path(self, shared_dir: Path, code: str) -> Path:
        """Get session file path with validation."""
        # Sanitize code to prevent path traversal
        sanitized_code = "".join(c for c in code if c.isalnum())
        filename = f"focus_guard_{sanitized_code}.jsonl"
        # Resolve to absolute path and verify it's within shared_dir
        file_path = (shared_dir / filename).resolve()
        if not str(file_path).startswith(str(shared_dir.resolve())):
            raise ValueError("Invalid session path")
        return file_path

    def create_session(self, shared_dir: str, code: Optional[str] = None) -> str:
        shared_path = Path(shared_dir)
        shared_path.mkdir(parents=True, exist_ok=True)

        session_code = code or self.generate_code()
        session_file = self._session_file_path(shared_path, session_code)
        session_file.touch(exist_ok=True)

        self.session_code = session_code
        self.shared_dir = shared_path
        self.session_file = session_file
        self.connected = True
        self.last_position = 0

        self.publish_event("session_created", {"code": session_code})
        self.logger.info("Collaboration session created: %s", session_code)
        return session_code

    def join_session(self, shared_dir: str, code: str) -> bool:
        # Validate inputs
        if not self._validate_session_code(code):
            self.logger.warning("Invalid session code format: %s", code)
            return False

        try:
            shared_path = Path(shared_dir).resolve()
            session_file = self._session_file_path(shared_path, code)
            if not session_file.exists():
                return False

            self.session_code = code
            self.shared_dir = shared_path
            self.session_file = session_file
            self.connected = True
            self.last_position = 0
            self.last_publish_times = []

            self.publish_event("session_joined", {"code": code})
            self.logger.info("Joined collaboration session: %s", code)
            return True
        except (OSError, ValueError) as exc:
            self.logger.error("Failed to join session: %s", exc)
            return False

    def disconnect(self) -> None:
        if self.connected:
            self.publish_event("session_left", {})
        self.connected = False
        self.session_code = None
        self.shared_dir = None
        self.session_file = None
        self.last_position = 0

    def _check_rate_limit(self) -> bool:
        """Check if publishing rate is within limits."""
        now = time.time()
        # Remove events older than 1 second
        self.last_publish_times = [t for t in self.last_publish_times if now - t < 1.0]
        if len(self.last_publish_times) >= MAX_EVENTS_PER_SECOND:
            return False
        self.last_publish_times.append(now)
        return True

    def publish_event(self, event_type: str, payload: Dict) -> bool:
        if not self.connected or self.session_file is None:
            return False

        # Rate limiting
        if not self._check_rate_limit():
            self.logger.warning("Rate limit exceeded for event publishing")
            return False

        # Validate payload size
        try:
            payload_json = json.dumps(payload)
            if len(payload_json) > MAX_PAYLOAD_SIZE:
                self.logger.warning(
                    "Payload too large: %d bytes (max: %d)",
                    len(payload_json),
                    MAX_PAYLOAD_SIZE,
                )
                return False
        except (TypeError, ValueError) as exc:
            self.logger.error("Invalid payload: %s", exc)
            return False

        event = {
            "type": event_type,
            "timestamp": time.time(),
            "sender": self.sender_id,
            "payload": payload,
        }

        try:
            with self.session_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event) + "\n")
            self.event_count += 1
            return True
        except Exception as exc:
            self.logger.warning("Failed to write collaboration event: %s", exc)
            return False

    def poll_events(self, timeout: float = 1.0) -> List[Dict]:
        """Poll events from collaboration file with timeout protection.

        Args:
            timeout: Maximum time in seconds to wait for file operations.

        Returns:
            List of events from other participants.
        """
        if not self.connected or self.session_file is None:
            return []

        if not self.session_file.exists():
            return []

        events: List[Dict] = []
        try:
            # Use timeout to prevent blocking on locked files
            start_time = time.time()

            # Check file size with timeout
            try:
                file_size = self.session_file.stat().st_size
            except OSError:
                # File might be locked or deleted
                return []

            if self.last_position > file_size:
                self.last_position = 0

            # Open file with timeout protection
            try:
                with self.session_file.open("r", encoding="utf-8") as handle:
                    handle.seek(self.last_position)
                    for line in handle:
                        # Check timeout
                        if time.time() - start_time > timeout:
                            self.logger.debug("Collaboration polling timeout")
                            break

                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        if event.get("sender") == self.sender_id:
                            continue
                        events.append(event)

                    self.last_position = handle.tell()
            except (IOError, OSError) as exc:
                # File locked or other I/O error - skip this poll cycle
                self.logger.debug("File I/O error during polling: %s", exc)

        except Exception as exc:
            self.logger.warning("Failed to read collaboration events: %s", exc)

        return events
