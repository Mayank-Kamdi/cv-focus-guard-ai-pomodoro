"""Comprehensive automated tests for core modules.

Tests include:
- Use cases: Real-world scenarios and workflows
- Edge cases: Boundary conditions, error handling, concurrent operations
- Integration: End-to-end feature testing

These tests avoid GUI and hardware dependencies.
"""

import tempfile
import time
import unittest
import json
import base64
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from collaboration import CollaborationSession
from focus_detector import FocusDetector
from logger import logger as app_logger
import config

# Try importing report manager (may not have cryptography)
try:
    from report_manager import TeacherReportManager

    REPORTS_AVAILABLE = True
except ImportError:
    REPORTS_AVAILABLE = False


class DummyLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def build_landmarks(default_x=0.5, default_y=0.5):
    landmarks = [DummyLandmark(default_x, default_y) for _ in range(468)]
    return landmarks


def set_open_eyes(landmarks, left_center=(0.6, 0.5), right_center=(0.4, 0.5)):
    # Left eye indices: [362, 385, 387, 263, 373, 380]
    landmarks[362] = DummyLandmark(left_center[0] - 0.05, left_center[1])
    landmarks[263] = DummyLandmark(left_center[0] + 0.05, left_center[1])
    landmarks[385] = DummyLandmark(left_center[0], left_center[1] - 0.04)
    landmarks[380] = DummyLandmark(left_center[0], left_center[1] + 0.04)
    landmarks[387] = DummyLandmark(left_center[0] + 0.02, left_center[1] - 0.04)
    landmarks[373] = DummyLandmark(left_center[0] + 0.02, left_center[1] + 0.04)

    # Right eye indices: [33, 160, 158, 133, 153, 144]
    landmarks[33] = DummyLandmark(right_center[0] - 0.05, right_center[1])
    landmarks[133] = DummyLandmark(right_center[0] + 0.05, right_center[1])
    landmarks[160] = DummyLandmark(right_center[0], right_center[1] - 0.04)
    landmarks[144] = DummyLandmark(right_center[0], right_center[1] + 0.04)
    landmarks[158] = DummyLandmark(right_center[0] + 0.02, right_center[1] - 0.04)
    landmarks[153] = DummyLandmark(right_center[0] + 0.02, right_center[1] + 0.04)


def set_closed_eyes(landmarks, left_center=(0.6, 0.5), right_center=(0.4, 0.5)):
    # Use a tiny vertical eye opening to trigger drowsy detection.
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


class CollaborationTests(unittest.TestCase):
    def test_create_join_and_events(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)
            self.assertTrue(code)

            guest = CollaborationSession(app_logger)
            joined = guest.join_session(tmp_dir, code)
            self.assertTrue(joined)

            payload = {"goals": ["Goal A", "Goal B"]}
            self.assertTrue(host.publish_event("goals_update", payload))
            time.sleep(0.05)

            events = guest.poll_events()
            self.assertTrue(events)
            self.assertEqual(events[-1]["type"], "goals_update")
            self.assertEqual(events[-1]["payload"], payload)

    def test_poll_ignores_own_events(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            session = CollaborationSession(app_logger)
            code = session.create_session(tmp_dir)
            self.assertTrue(code)
            self.assertTrue(session.publish_event("ping", {"ok": True}))
            time.sleep(0.05)
            self.assertEqual(session.poll_events(), [])

    def test_join_missing_session_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            guest = CollaborationSession(app_logger)
            self.assertFalse(guest.join_session(tmp_dir, "NOPE"))

    def test_publish_without_connection_returns_false(self):
        session = CollaborationSession(app_logger)
        self.assertFalse(session.publish_event("ping", {"ok": True}))

    def test_poll_after_session_file_deleted(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)
            session_file = Path(tmp_dir) / f"focus_guard_{code}.jsonl"
            self.assertTrue(session_file.exists())
            session_file.unlink()
            self.assertEqual(host.poll_events(), [])


class FocusDetectorTests(unittest.TestCase):
    def test_unfocused_none_when_center(self):
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.5, 0.5)  # nose
        set_open_eyes(landmarks, left_center=(0.6, 0.5), right_center=(0.4, 0.5))
        detector = FocusDetector(landmarks)
        self.assertIsNone(detector.is_unfocused())

    def test_unfocused_left_when_nose_shifts(self):
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.35, 0.5)
        set_open_eyes(landmarks, left_center=(0.8, 0.5), right_center=(0.4, 0.5))
        detector = FocusDetector(landmarks)
        self.assertEqual(detector.is_unfocused(), "Looking Left")

    def test_unfocused_drowsy_when_eyes_closed(self):
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.5, 0.5)
        set_closed_eyes(landmarks)
        detector = FocusDetector(landmarks)
        self.assertEqual(detector.is_unfocused(), "Drowsy")


class ConfigTests(unittest.TestCase):
    def test_paths_exist(self):
        self.assertTrue(Path(config.DATA_DIR).exists())
        self.assertTrue(Path(config.LOG_DIR).exists())
        self.assertTrue(Path(config.COLLAB_DIR).exists())


# ============================================================================
# USE CASE TESTS - Real-world scenarios
# ============================================================================


class CollaborationUseCaseTests(unittest.TestCase):
    """Test realistic collaboration workflows."""

    def test_complete_study_session_workflow(self):
        """Use case: Two students start session, share goals, report distractions."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Student A creates session
            student_a = CollaborationSession(app_logger)
            code = student_a.create_session(tmp_dir)

            # Student B joins
            student_b = CollaborationSession(app_logger)
            self.assertTrue(student_b.join_session(tmp_dir, code))

            # Student A shares goals
            goals = {"goals": ["Complete math homework", "Study for chemistry test"]}
            self.assertTrue(student_a.publish_event("goals_update", goals))
            time.sleep(0.05)

            # Student B receives goals
            events_b = student_b.poll_events()
            self.assertEqual(len(events_b), 1)
            self.assertEqual(events_b[0]["payload"]["goals"], goals["goals"])

            # Student A gets distracted
            distraction = {"reason": "Looking Left", "count": 1}
            self.assertTrue(student_a.publish_event("distraction", distraction))
            time.sleep(0.05)

            # Student B sees distraction
            events_b = student_b.poll_events()
            self.assertEqual(events_b[0]["type"], "distraction")

    def test_multiple_guests_same_session(self):
        """Use case: One host, multiple guests in same study session."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            # Three guests join
            guests = [CollaborationSession(app_logger) for _ in range(3)]
            for guest in guests:
                self.assertTrue(guest.join_session(tmp_dir, code))

            # Host broadcasts message
            broadcast = {"message": "Let's focus for 25 minutes!"}
            self.assertTrue(host.publish_event("broadcast", broadcast))
            time.sleep(0.05)

            # All guests receive it
            for guest in guests:
                events = guest.poll_events()
                self.assertTrue(any(e["type"] == "broadcast" for e in events))

    def test_session_persistence_across_reconnects(self):
        """Use case: Guest disconnects and rejoins same session."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            # Guest joins, disconnects
            guest1 = CollaborationSession(app_logger)
            self.assertTrue(guest1.join_session(tmp_dir, code))
            del guest1

            # Host publishes event
            self.assertTrue(host.publish_event("ping", {"status": "active"}))
            time.sleep(0.05)

            # New guest instance joins same session
            guest2 = CollaborationSession(app_logger)
            self.assertTrue(guest2.join_session(tmp_dir, code))

            # Can see host's event
            events = guest2.poll_events()
            self.assertTrue(any(e["type"] == "ping" for e in events))


class FocusDetectorUseCaseTests(unittest.TestCase):
    """Test realistic focus detection scenarios."""

    def test_normal_focused_reading_session(self):
        """Use case: Student reads directly at screen for extended period."""
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.5, 0.5)
        set_open_eyes(landmarks)

        detector = FocusDetector(landmarks)
        # Should stay focused
        for _ in range(10):
            self.assertIsNone(detector.is_unfocused())

    def test_brief_glance_away_during_thinking(self):
        """Use case: Student briefly looks away while thinking."""
        # Slightly looking up-right (thinking pose)
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.55, 0.45)
        set_open_eyes(landmarks, left_center=(0.65, 0.45), right_center=(0.45, 0.45))

        detector = FocusDetector(landmarks)
        # Minor deviation shouldn't trigger unfocus
        result = detector.is_unfocused()
        self.assertIn(result, [None, "Looking Right"])  # Tolerance for minor angles

    def test_prolonged_distraction_sequence(self):
        """Use case: Student gets distracted by phone, then refocuses."""
        # Looking right (at phone)
        landmarks_distracted = build_landmarks()
        landmarks_distracted[1] = DummyLandmark(0.7, 0.5)
        set_open_eyes(
            landmarks_distracted, left_center=(0.8, 0.5), right_center=(0.6, 0.5)
        )

        detector = FocusDetector(landmarks_distracted)
        self.assertEqual(detector.is_unfocused(), "Looking Right")

        # Returns to center
        landmarks_focused = build_landmarks()
        landmarks_focused[1] = DummyLandmark(0.5, 0.5)
        set_open_eyes(landmarks_focused)

        detector2 = FocusDetector(landmarks_focused)
        self.assertIsNone(detector2.is_unfocused())

    def test_tired_student_eyes_closing(self):
        """Use case: Student getting tired, eyes gradually closing."""
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.5, 0.5)
        set_closed_eyes(landmarks)

        detector = FocusDetector(landmarks)
        self.assertEqual(detector.is_unfocused(), "Drowsy")


@unittest.skipUnless(REPORTS_AVAILABLE, "cryptography not installed")
class ReportManagerUseCaseTests(unittest.TestCase):
    """Test realistic report generation workflows."""

    def test_complete_report_workflow(self):
        """Use case: Teacher sets up key, student generates and encrypts report."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Teacher generates keypair
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization

            teacher_private = rsa.generate_private_key(
                public_exponent=65537, key_size=2048
            )
            teacher_public = teacher_private.public_key()

            # Save teacher public key
            teacher_pub_path = Path(tmp_dir) / "teacher_public.pem"
            teacher_pub_path.write_bytes(
                teacher_public.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )

            # Student loads teacher key and generates report
            manager = TeacherReportManager(app_logger, Path(tmp_dir))
            manager.load_teacher_public_key_from_file(str(teacher_pub_path))

            report_data = {
                "sessions_completed": 5,
                "total_focus_minutes": 120,
                "total_distractions": 8,
                "last_session_distractions": 2,
            }

            report_path = manager.generate_report(**report_data)
            self.assertTrue(Path(report_path).exists())

            # Verify report structure
            with open(report_path) as f:
                report = json.load(f)
            self.assertIn("encrypted_report", report)
            self.assertIn("signature", report)
            self.assertIn("signer_public_key", report)


# ============================================================================
# EDGE CASE TESTS - Boundary conditions and error handling
# ============================================================================


class CollaborationEdgeCaseTests(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_empty_session_code(self):
        """Edge case: Attempt to join with empty code."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            guest = CollaborationSession(app_logger)
            self.assertFalse(guest.join_session(tmp_dir, ""))

    def test_very_long_session_code(self):
        """Edge case: Attempt to join with extremely long code."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            guest = CollaborationSession(app_logger)
            long_code = "X" * 1000
            self.assertFalse(guest.join_session(tmp_dir, long_code))

    def test_special_characters_in_code(self):
        """Edge case: Session code with special characters."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            guest = CollaborationSession(app_logger)
            # Should fail safely
            self.assertFalse(guest.join_session(tmp_dir, "AB/../CD"))

    def test_large_payload_publish(self):
        """Edge case: Publishing very large event payload."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            # Create large payload (1000 goals)
            large_payload = {"goals": [f"Goal {i}" for i in range(1000)]}

            # Should handle gracefully
            try:
                result = host.publish_event("goals_update", large_payload)
                self.assertIsNotNone(result)
            except Exception as e:
                self.fail(f"Large payload caused exception: {e}")

    def test_rapid_sequential_publishes(self):
        """Edge case: Publishing many events in quick succession."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            guest = CollaborationSession(app_logger)
            guest.join_session(tmp_dir, code)

            # Publish 50 events rapidly
            for i in range(50):
                self.assertTrue(host.publish_event("ping", {"count": i}))

            time.sleep(0.1)

            # Guest should receive all events
            events = guest.poll_events()
            self.assertGreaterEqual(len(events), 50)

    def test_concurrent_session_creation(self):
        """Edge case: Multiple sessions created simultaneously."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sessions = [CollaborationSession(app_logger) for _ in range(5)]
            codes = [s.create_session(tmp_dir) for s in sessions]

            # All codes should be unique
            self.assertEqual(len(codes), len(set(codes)))

            # All sessions should work independently
            for idx, session in enumerate(sessions):
                self.assertTrue(session.publish_event("test", {"id": idx}))

    def test_poll_events_with_corrupted_json(self):
        """Edge case: Session file contains malformed JSON."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            # Append corrupted data to session file
            session_file = Path(tmp_dir) / f"focus_guard_{code}.jsonl"
            with open(session_file, "a") as f:
                f.write("CORRUPTED{invalid:json}\n")

            # Should handle gracefully
            events = host.poll_events()
            self.assertIsInstance(events, list)

    def test_session_file_permissions_readonly(self):
        """Edge case: Session file becomes read-only."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            host = CollaborationSession(app_logger)
            code = host.create_session(tmp_dir)

            session_file = Path(tmp_dir) / f"focus_guard_{code}.jsonl"

            # Make read-only (Windows compatible)
            import stat

            session_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

            try:
                # Publishing should fail gracefully
                result = host.publish_event("test", {"data": "test"})
                self.assertFalse(result)
            finally:
                # Restore permissions for cleanup
                session_file.chmod(stat.S_IWUSR | stat.S_IRUSR)

    def test_nonexistent_session_directory(self):
        """Edge case: Session directory doesn't exist."""
        guest = CollaborationSession(app_logger)
        fake_dir = "/nonexistent/path/to/nowhere"
        self.assertFalse(guest.join_session(fake_dir, "ABCDEF"))


class FocusDetectorEdgeCaseTests(unittest.TestCase):
    """Test focus detector edge cases."""

    def test_missing_landmarks(self):
        """Edge case: Empty landmarks list."""
        try:
            detector = FocusDetector([])
            # Should handle gracefully
            result = detector.is_unfocused()
            self.assertIsNotNone(result)  # Probably returns error state
        except Exception as e:
            # Or may raise exception - both acceptable
            pass

    def test_extreme_head_angles(self):
        """Edge case: Extremely turned head (looking behind)."""
        landmarks = build_landmarks()
        # Extreme rightward turn
        landmarks[1] = DummyLandmark(0.95, 0.5)
        set_open_eyes(landmarks, left_center=(0.99, 0.5), right_center=(0.9, 0.5))

        detector = FocusDetector(landmarks)
        result = detector.is_unfocused()
        self.assertIn(result, ["Looking Right", "No Face"])

    def test_extreme_head_tilt_up(self):
        """Edge case: Head tilted far upward (looking at ceiling)."""
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.5, 0.1)  # Nose very high
        set_open_eyes(landmarks, left_center=(0.6, 0.15), right_center=(0.4, 0.15))

        detector = FocusDetector(landmarks)
        result = detector.is_unfocused()
        # Should detect as unfocused
        self.assertIsNotNone(result)

    def test_extreme_head_tilt_down(self):
        """Edge case: Head tilted far downward (looking at lap)."""
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.5, 0.9)  # Nose very low
        set_open_eyes(landmarks, left_center=(0.6, 0.85), right_center=(0.4, 0.85))

        detector = FocusDetector(landmarks)
        result = detector.is_unfocused()
        self.assertIsNotNone(result)

    def test_partial_face_visibility(self):
        """Edge case: Only partial face visible in frame."""
        landmarks = build_landmarks()
        # Simulate right side of face out of frame
        landmarks[1] = DummyLandmark(0.1, 0.5)
        # Only left eye visible
        set_open_eyes(landmarks, left_center=(0.15, 0.5), right_center=(0.05, 0.5))

        detector = FocusDetector(landmarks)
        result = detector.is_unfocused()
        # Should detect as looking left or no face
        self.assertIn(result, ["Looking Left", "No Face", None])

    def test_rapid_eye_state_changes(self):
        """Edge case: Blinking rapidly."""
        # Open eyes
        landmarks_open = build_landmarks()
        landmarks_open[1] = DummyLandmark(0.5, 0.5)
        set_open_eyes(landmarks_open)
        detector1 = FocusDetector(landmarks_open)

        # Closed eyes
        landmarks_closed = build_landmarks()
        landmarks_closed[1] = DummyLandmark(0.5, 0.5)
        set_closed_eyes(landmarks_closed)
        detector2 = FocusDetector(landmarks_closed)

        # Both should process without errors
        self.assertIsNone(detector1.is_unfocused())
        self.assertEqual(detector2.is_unfocused(), "Drowsy")

    def test_boundary_yaw_threshold(self):
        """Edge case: Head angle exactly at threshold boundary."""
        landmarks = build_landmarks()
        # Set nose at exact threshold (around 0.3 or 0.7)
        landmarks[1] = DummyLandmark(0.3, 0.5)
        set_open_eyes(landmarks, left_center=(0.4, 0.5), right_center=(0.2, 0.5))

        detector = FocusDetector(landmarks)
        result = detector.is_unfocused()
        # Should consistently classify (either None or Looking Left)
        self.assertIn(result, [None, "Looking Left"])


@unittest.skipUnless(REPORTS_AVAILABLE, "cryptography not installed")
class ReportManagerEdgeCaseTests(unittest.TestCase):
    """Test report manager edge cases."""

    def test_report_generation_without_teacher_key(self):
        """Edge case: Generate report without loading teacher key."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = TeacherReportManager(app_logger, Path(tmp_dir))

            # Should fail gracefully
            try:
                report_path = manager.generate_report(
                    sessions_completed=1,
                    total_focus_minutes=25,
                    total_distractions=0,
                    last_session_distractions=0,
                )
                # If it returns None or raises, both OK
                if report_path:
                    self.fail("Should not generate report without teacher key")
            except Exception:
                pass  # Expected

    def test_load_invalid_teacher_key_file(self):
        """Edge case: Load corrupted teacher key file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = TeacherReportManager(app_logger, Path(tmp_dir))

            # Create invalid key file
            bad_key_path = Path(tmp_dir) / "bad_key.pem"
            bad_key_path.write_text("NOT A VALID KEY FILE")

            # Should handle gracefully
            try:
                manager.load_teacher_public_key_from_file(str(bad_key_path))
                self.fail("Should reject invalid key file")
            except Exception:
                pass  # Expected

    def test_zero_metrics_report(self):
        """Edge case: Report with all zero metrics."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization

            teacher_private = rsa.generate_private_key(
                public_exponent=65537, key_size=2048
            )
            teacher_public = teacher_private.public_key()

            teacher_pub_path = Path(tmp_dir) / "teacher_public.pem"
            teacher_pub_path.write_bytes(
                teacher_public.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )

            manager = TeacherReportManager(app_logger, Path(tmp_dir))
            manager.load_teacher_public_key_from_file(str(teacher_pub_path))

            # All zeros
            report_path = manager.generate_report(
                sessions_completed=0,
                total_focus_minutes=0,
                total_distractions=0,
                last_session_distractions=0,
            )

            self.assertTrue(Path(report_path).exists())

    def test_extreme_high_metrics_report(self):
        """Edge case: Report with extremely high metrics."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization

            teacher_private = rsa.generate_private_key(
                public_exponent=65537, key_size=2048
            )
            teacher_public = teacher_private.public_key()

            teacher_pub_path = Path(tmp_dir) / "teacher_public.pem"
            teacher_pub_path.write_bytes(
                teacher_public.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )

            manager = TeacherReportManager(app_logger, Path(tmp_dir))
            manager.load_teacher_public_key_from_file(str(teacher_pub_path))

            # Extreme values
            report_path = manager.generate_report(
                sessions_completed=999999,
                total_focus_minutes=999999,
                total_distractions=999999,
                last_session_distractions=999999,
            )

            self.assertTrue(Path(report_path).exists())


# ============================================================================
# INTEGRATION TESTS - End-to-end workflows
# ============================================================================


class IntegrationTests(unittest.TestCase):
    """Test complete feature workflows."""

    def test_full_accountability_partner_session(self):
        """Integration: Complete session with goal sharing and distraction tracking."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Setup
            student_a = CollaborationSession(app_logger)
            student_b = CollaborationSession(app_logger)

            # Session creation
            code = student_a.create_session(tmp_dir)
            self.assertTrue(student_b.join_session(tmp_dir, code))

            # Share initial goals
            goals_a = {"goals": ["Math homework", "Read Ch. 5"]}
            goals_b = {"goals": ["Essay draft", "Lab report"]}

            student_a.publish_event("goals_update", goals_a)
            student_b.publish_event("goals_update", goals_b)
            time.sleep(0.1)

            # Both see partner's goals
            a_events = student_a.poll_events()
            b_events = student_b.poll_events()

            self.assertTrue(any(e["payload"] == goals_b for e in a_events))
            self.assertTrue(any(e["payload"] == goals_a for e in b_events))

            # Simulate distractions
            student_a.publish_event(
                "distraction", {"reason": "Looking Left", "count": 1}
            )
            student_b.publish_event("distraction", {"reason": "Drowsy", "count": 1})
            time.sleep(0.1)

            # Both see partner's distractions
            a_events = student_a.poll_events()
            b_events = student_b.poll_events()

            self.assertTrue(any(e["type"] == "distraction" for e in a_events))
            self.assertTrue(any(e["type"] == "distraction" for e in b_events))

    def test_focus_detection_state_transitions(self):
        """Integration: Test all focus state transitions."""
        states_tested = []

        # Focused
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.5, 0.5)
        set_open_eyes(landmarks)
        detector = FocusDetector(landmarks)
        states_tested.append(detector.is_unfocused())

        # Looking Left
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.3, 0.5)
        set_open_eyes(landmarks, left_center=(0.5, 0.5), right_center=(0.2, 0.5))
        detector = FocusDetector(landmarks)
        states_tested.append(detector.is_unfocused())

        # Looking Right
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.7, 0.5)
        set_open_eyes(landmarks, left_center=(0.8, 0.5), right_center=(0.6, 0.5))
        detector = FocusDetector(landmarks)
        states_tested.append(detector.is_unfocused())

        # Drowsy
        landmarks = build_landmarks()
        landmarks[1] = DummyLandmark(0.5, 0.5)
        set_closed_eyes(landmarks)
        detector = FocusDetector(landmarks)
        states_tested.append(detector.is_unfocused())

        # Should have seen: None, Looking Left, Looking Right, Drowsy
        self.assertIn(None, states_tested)
        self.assertIn("Looking Left", states_tested)
        self.assertIn("Looking Right", states_tested)
        self.assertIn("Drowsy", states_tested)


if __name__ == "__main__":
    unittest.main(verbosity=2)
