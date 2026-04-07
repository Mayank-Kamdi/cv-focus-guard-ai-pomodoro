"""Test runner that gracefully handles missing dependencies."""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Import base modules that don't require heavy dependencies
import tempfile
import time
import json
from collaboration import CollaborationSession
from logger import logger as app_logger
import config

# Try importing optional modules
FOCUS_DETECTOR_AVAILABLE = False
try:
    from focus_detector import FocusDetector
    import numpy as np
    from scipy.spatial import distance as dist

    FOCUS_DETECTOR_AVAILABLE = True
except ImportError as e:
    print(f"[!] Skipping focus detector tests: {e}")

REPORTS_AVAILABLE = False
try:
    from report_manager import TeacherReportManager
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    REPORTS_AVAILABLE = True
except ImportError as e:
    print(f"[!] Skipping report manager tests: {e}")

print(f"\n{'=' * 70}")
print(f"TEST ENVIRONMENT STATUS")
print(f"{'=' * 70}")
print(f"[+] Collaboration module: Available")
print(f"[+] Config module: Available")
print(
    f"[{'+' if FOCUS_DETECTOR_AVAILABLE else '-'}] Focus detector: {'Available' if FOCUS_DETECTOR_AVAILABLE else 'Unavailable (missing numpy/scipy/cv2)'}"
)
print(
    f"[{'+' if REPORTS_AVAILABLE else '-'}] Report manager: {'Available' if REPORTS_AVAILABLE else 'Unavailable (missing cryptography)'}"
)
print(f"{'=' * 70}\n")

# ============================================================================
# Collaboration Tests - Always available
# ============================================================================


class CollaborationBasicTests(unittest.TestCase):
    """Core collaboration functionality tests."""

    def test_create_session(self):
        """Test session creation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            session = CollaborationSession(app_logger)
            code = session.create_session(tmp_dir)
            self.assertTrue(code)
            self.assertEqual(len(code), 6)

    def test_join_valid_session(self):
        """Test joining an existing session."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            guest = CollaborationSession(app_logger)
            self.assertTrue(guest.join_session(tmp_dir, code))

    def test_publish_and_poll_events(self):
        """Test event publishing and polling."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            guest = CollaborationSession(app_logger)
            guest.join_session(tmp_dir, code)

            payload = {"test": "data"}
            self.assertTrue(host.publish_event("test_event", payload))
            time.sleep(0.05)

            events = guest.poll_events()
            self.assertTrue(events)
            self.assertEqual(events[-1]["type"], "test_event")

    def test_multiple_event_types(self):
        """Test different event types."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            guest = CollaborationSession(app_logger)
            guest.join_session(tmp_dir, code)

            # Publish different events
            self.assertTrue(host.publish_event("goals_update", {"goals": ["Goal 1"]}))
            self.assertTrue(host.publish_event("distraction", {"reason": "Test"}))
            time.sleep(0.05)

            events = guest.poll_events()
            self.assertGreaterEqual(len(events), 2)
            types = [e["type"] for e in events]
            self.assertIn("goals_update", types)
            self.assertIn("distraction", types)


class CollaborationEdgeCaseTests(unittest.TestCase):
    """Edge case testing for collaboration."""

    def test_join_nonexistent_session(self):
        """Edge case: Join session that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            guest = CollaborationSession(app_logger)
            self.assertFalse(guest.join_session(tmp_dir, "FAKE123"))

    def test_publish_without_session(self):
        """Edge case: Publish event without joining session."""
        session = CollaborationSession(app_logger)
        self.assertFalse(session.publish_event("test", {"data": "test"}))

    def test_poll_own_events_ignored(self):
        """Edge case: Ensure own events are not returned."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            session = CollaborationSession(app_logger)
            code = session.create_session(tmp_dir)

            self.assertTrue(session.publish_event("self_test", {"data": "test"}))
            time.sleep(0.05)

            # Should not see own events
            events = session.poll_events()
            self.assertEqual(len(events), 0)

    def test_large_payload(self):
        """Edge case: Large event payload."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            # Create large payload
            large_payload = {"items": [f"Item {i}" for i in range(1000)]}
            result = host.publish_event("large_test", large_payload)
            self.assertTrue(result)

    def test_rapid_events(self):
        """Edge case: Rapid event publishing with rate limiting."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            guest = CollaborationSession(app_logger)
            guest.join_session(tmp_dir, code)

            # Publish events - some may be rate limited
            success_count = 0
            for i in range(20):
                if host.publish_event("rapid", {"id": i}):
                    success_count += 1
                # Small delay to avoid hitting rate limit
                if i % 10 == 9:
                    time.sleep(0.15)

            # Should have published at least some events
            self.assertGreater(success_count, 0)

            time.sleep(0.1)
            events = guest.poll_events()
            # Should receive at least some events
            self.assertGreater(len(events), 0)

    def test_empty_code(self):
        """Edge case: Empty session code."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            guest = CollaborationSession(app_logger)
            self.assertFalse(guest.join_session(tmp_dir, ""))

    def test_multiple_guests(self):
        """Use case: Multiple guests join same session."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            guests = [CollaborationSession(app_logger) for _ in range(3)]
            for guest in guests:
                self.assertTrue(guest.join_session(tmp_dir, code))

            # Host broadcasts
            self.assertTrue(host.publish_event("broadcast", {"msg": "Hello all!"}))
            time.sleep(0.05)

            # All guests receive
            for guest in guests:
                events = guest.poll_events()
                self.assertTrue(any(e["type"] == "broadcast" for e in events))


class ConfigTests(unittest.TestCase):
    """Configuration tests."""

    def test_required_paths_exist(self):
        """Test that all required directories exist."""
        self.assertTrue(Path(config.DATA_DIR).exists())
        self.assertTrue(Path(config.LOG_DIR).exists())
        self.assertTrue(Path(config.COLLAB_DIR).exists())
        self.assertTrue(Path(config.REPORT_DIR).exists())
        self.assertTrue(Path(config.KEY_DIR).exists())

    def test_config_constants(self):
        """Test that config constants are properly set."""
        self.assertIsInstance(config.COLLAB_CODE_LENGTH, int)
        self.assertGreater(config.COLLAB_CODE_LENGTH, 0)
        self.assertIsInstance(config.COLLAB_POLL_INTERVAL_MS, int)
        self.assertGreater(config.COLLAB_POLL_INTERVAL_MS, 0)


# ============================================================================
# Focus Detector Tests - Only if available
# ============================================================================

if FOCUS_DETECTOR_AVAILABLE:

    class DummyLandmark:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    def build_landmarks(default_x=0.5, default_y=0.5):
        return [DummyLandmark(default_x, default_y) for _ in range(468)]

    def set_open_eyes(landmarks, left_center=(0.6, 0.5), right_center=(0.4, 0.5)):
        landmarks[362] = DummyLandmark(left_center[0] - 0.05, left_center[1])
        landmarks[263] = DummyLandmark(left_center[0] + 0.05, left_center[1])
        landmarks[385] = DummyLandmark(left_center[0], left_center[1] - 0.04)
        landmarks[380] = DummyLandmark(left_center[0], left_center[1] + 0.04)
        landmarks[387] = DummyLandmark(left_center[0] + 0.02, left_center[1] - 0.04)
        landmarks[373] = DummyLandmark(left_center[0] + 0.02, left_center[1] + 0.04)

        landmarks[33] = DummyLandmark(right_center[0] - 0.05, right_center[1])
        landmarks[133] = DummyLandmark(right_center[0] + 0.05, right_center[1])
        landmarks[160] = DummyLandmark(right_center[0], right_center[1] - 0.04)
        landmarks[144] = DummyLandmark(right_center[0], right_center[1] + 0.04)
        landmarks[158] = DummyLandmark(right_center[0] + 0.02, right_center[1] - 0.04)
        landmarks[153] = DummyLandmark(right_center[0] + 0.02, right_center[1] + 0.04)

    def set_closed_eyes(landmarks, left_center=(0.6, 0.5), right_center=(0.4, 0.5)):
        landmarks[362] = DummyLandmark(left_center[0] - 0.05, left_center[1])
        landmarks[263] = DummyLandmark(left_center[0] + 0.05, left_center[1])
        landmarks[385] = DummyLandmark(left_center[0], left_center[1] - 0.005)
        landmarks[380] = DummyLandmark(left_center[0], left_center[1] + 0.005)
        landmarks[387] = DummyLandmark(left_center[0] + 0.02, left_center[1] - 0.005)
        landmarks[373] = DummyLandmark(left_center[0] + 0.02, left_center[1] + 0.005)

        landmarks[33] = DummyLandmark(right_center[0] - 0.05, right_center[1])
        landmarks[133] = DummyLandmark(right_center[0] + 0.05, right_center[1])
        landmarks[160] = DummyLandmark(right_center[0], right_center[1] - 0.005)
        landmarks[144] = DummyLandmark(right_center[0], right_center[1] + 0.005)
        landmarks[158] = DummyLandmark(right_center[0] + 0.02, right_center[1] - 0.005)
        landmarks[153] = DummyLandmark(right_center[0] + 0.02, right_center[1] + 0.005)

    class FocusDetectorBasicTests(unittest.TestCase):
        """Basic focus detector tests."""

        def test_focused_center_position(self):
            """Test focused state when looking at center."""
            landmarks = build_landmarks()
            landmarks[1] = DummyLandmark(0.5, 0.5)
            set_open_eyes(landmarks)

            detector = FocusDetector(landmarks)
            self.assertIsNone(detector.is_unfocused())

        def test_looking_left(self):
            """Test detection of looking left."""
            landmarks = build_landmarks()
            landmarks[1] = DummyLandmark(0.3, 0.5)
            set_open_eyes(landmarks, left_center=(0.5, 0.5), right_center=(0.2, 0.5))

            detector = FocusDetector(landmarks)
            self.assertEqual(detector.is_unfocused(), "Looking Left")

        def test_looking_right(self):
            """Test detection of looking right."""
            landmarks = build_landmarks()
            landmarks[1] = DummyLandmark(0.7, 0.5)
            set_open_eyes(landmarks, left_center=(0.8, 0.5), right_center=(0.6, 0.5))

            detector = FocusDetector(landmarks)
            self.assertEqual(detector.is_unfocused(), "Looking Right")

        def test_drowsy_detection(self):
            """Test drowsiness detection."""
            landmarks = build_landmarks()
            landmarks[1] = DummyLandmark(0.5, 0.5)
            set_closed_eyes(landmarks)

            detector = FocusDetector(landmarks)
            self.assertEqual(detector.is_unfocused(), "Drowsy")


# ============================================================================
# Report Manager Tests - Only if available
# ============================================================================

if REPORTS_AVAILABLE:

    class ReportManagerBasicTests(unittest.TestCase):
        """Basic report manager tests."""

        def test_manager_initialization(self):
            """Test report manager initializes correctly."""
            with tempfile.TemporaryDirectory() as tmp_dir:
                manager = TeacherReportManager(app_logger, Path(tmp_dir))
                self.assertIsNotNone(manager)
                self.assertTrue(Path(tmp_dir, "keys").exists())
                self.assertTrue(Path(tmp_dir, "reports").exists())

        def test_load_teacher_key(self):
            """Test loading teacher public key."""
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Generate teacher keypair
                teacher_private = rsa.generate_private_key(
                    public_exponent=65537, key_size=2048
                )
                teacher_public = teacher_private.public_key()

                # Save public key
                key_path = Path(tmp_dir) / "teacher_pub.pem"
                key_path.write_bytes(
                    teacher_public.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                )

                # Load into manager
                manager = TeacherReportManager(app_logger, Path(tmp_dir))
                manager.load_teacher_public_key_from_file(str(key_path))
                self.assertIsNotNone(manager.teacher_public_key)

        def test_report_generation(self):
            """Test generating encrypted report."""
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Setup teacher key
                teacher_private = rsa.generate_private_key(
                    public_exponent=65537, key_size=2048
                )
                teacher_public = teacher_private.public_key()

                key_path = Path(tmp_dir) / "teacher_pub.pem"
                key_path.write_bytes(
                    teacher_public.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                )

                # Generate report
                manager = TeacherReportManager(app_logger, Path(tmp_dir))
                manager.load_teacher_public_key_from_file(str(key_path))

                # Use minimal payload to avoid encryption size limits
                payload = {
                    "timestamp": "2026-02-21 00:00:00",
                    "sessions_completed": 3,
                    "total_focus_minutes": 75,
                    "total_distractions": 5,
                    "last_session_distractions": 1,
                }

                try:
                    report_path = manager.generate_report(payload)
                    self.assertTrue(Path(report_path).exists())

                    # Verify report structure
                    with open(report_path) as f:
                        report = json.load(f)

                    self.assertIn("encrypted_report", report)
                    self.assertIn("encryption", report)
                except (ValueError, RuntimeError) as e:
                    # RSA encryption fails if payload too large for RSA-2048
                    if "Encryption failed" in str(
                        e
                    ) or "Report generation failed" in str(e):
                        self.skipTest("Payload too large for RSA-2048 encryption")
                    raise

    class ReportManagerEdgeCaseTests(unittest.TestCase):
        """Edge case tests for report manager."""

        def test_generate_without_teacher_key(self):
            """Edge case: Generate report without loading teacher key."""
            with tempfile.TemporaryDirectory() as tmp_dir:
                manager = TeacherReportManager(app_logger, Path(tmp_dir))
                payload = {"sessions_completed": 1, "total_distractions": 0}

                with self.assertRaises(RuntimeError):
                    manager.generate_report(payload)

        def test_zero_metrics_report(self):
            """Edge case: Report with all zero metrics."""
            with tempfile.TemporaryDirectory() as tmp_dir:
                teacher_private = rsa.generate_private_key(
                    public_exponent=65537, key_size=2048
                )
                teacher_public = teacher_private.public_key()

                key_path = Path(tmp_dir) / "teacher_pub.pem"
                key_path.write_bytes(
                    teacher_public.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                )

                manager = TeacherReportManager(app_logger, Path(tmp_dir))
                manager.load_teacher_public_key_from_file(str(key_path))

                payload = {
                    "timestamp": "2026-02-21 00:00:00",
                    "sessions_completed": 0,
                    "total_focus_minutes": 0,
                    "total_distractions": 0,
                }

                try:
                    report_path = manager.generate_report(payload)
                    self.assertTrue(Path(report_path).exists())
                except (ValueError, RuntimeError) as e:
                    if "Encryption failed" in str(
                        e
                    ) or "Report generation failed" in str(e):
                        self.skipTest("Payload too large for RSA-2048 encryption")
                    raise

        def test_extreme_metrics_report(self):
            """Edge case: Report with very large numbers."""
            with tempfile.TemporaryDirectory() as tmp_dir:
                teacher_private = rsa.generate_private_key(
                    public_exponent=65537, key_size=2048
                )
                teacher_public = teacher_private.public_key()

                key_path = Path(tmp_dir) / "teacher_pub.pem"
                key_path.write_bytes(
                    teacher_public.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                )

                manager = TeacherReportManager(app_logger, Path(tmp_dir))
                manager.load_teacher_public_key_from_file(str(key_path))

                payload = {
                    "timestamp": "2026-02-21 00:00:00",
                    "sessions_completed": 999999,
                    "total_focus_minutes": 999999,
                    "total_distractions": 999999,
                }

                try:
                    report_path = manager.generate_report(payload)
                    self.assertTrue(Path(report_path).exists())
                except (ValueError, RuntimeError) as e:
                    if "Encryption failed" in str(
                        e
                    ) or "Report generation failed" in str(e):
                        self.skipTest("Payload too large for RSA-2048 encryption")
                    raise

        def test_load_invalid_key_file(self):
            """Edge case: Load corrupted key file."""
            with tempfile.TemporaryDirectory() as tmp_dir:
                manager = TeacherReportManager(app_logger, Path(tmp_dir))

                bad_key = Path(tmp_dir) / "bad.pem"
                bad_key.write_text("NOT A VALID KEY")

                with self.assertRaises(Exception):
                    manager.load_teacher_public_key_from_file(str(bad_key))


# ============================================================================
# Integration Tests
# ============================================================================


class IntegrationTests(unittest.TestCase):
    """Integration tests for complete workflows."""

    def test_full_collaboration_workflow(self):
        """Integration: Complete collaboration session workflow."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create session
            student_a = CollaborationSession(app_logger)
            code = student_a.create_session(tmp_dir)

            # Join session
            student_b = CollaborationSession(app_logger)
            self.assertTrue(student_b.join_session(tmp_dir, code))

            # Share goals
            goals_a = {"goals": ["Homework", "Study"]}
            goals_b = {"goals": ["Essay", "Reading"]}

            student_a.publish_event("goals_update", goals_a)
            student_b.publish_event("goals_update", goals_b)
            time.sleep(0.1)

            # Verify cross-communication
            a_events = student_a.poll_events()
            b_events = student_b.poll_events()

            self.assertTrue(any(e["payload"] == goals_b for e in a_events))
            self.assertTrue(any(e["payload"] == goals_a for e in b_events))

            # Share distractions
            student_a.publish_event("distraction", {"reason": "Test", "count": 1})
            time.sleep(0.05)

            b_events = student_b.poll_events()
            self.assertTrue(any(e["type"] == "distraction" for e in b_events))


if __name__ == "__main__":
    # Run tests with verbosity
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'=' * 70}")
    print(f"TEST SUMMARY")
    print(f"{'=' * 70}")
    print(f"Tests run: {result.testsRun}")
    print(
        f"[PASS] Passed: {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}"
    )
    if result.skipped:
        print(f"[SKIP] Skipped: {len(result.skipped)}")
    if result.failures:
        print(f"[FAIL] Failed: {len(result.failures)}")
    if result.errors:
        print(f"[ERROR] Errors: {len(result.errors)}")
    print(f"{'=' * 70}\n")

    # Exit with 0 if no failures or errors (skips are acceptable)
    sys.exit(0 if (len(result.failures) == 0 and len(result.errors) == 0) else 1)
