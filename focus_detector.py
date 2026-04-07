"""Focus detection using facial landmarks.

Production features:
- Input validation for landmarks
- Bounds checking for calculations
- Error handling for edge cases
"""

import numpy as np
from scipy.spatial import distance as dist


class FocusDetector:
    def __init__(self, landmarks):
        # Validate landmarks
        if not landmarks:
            raise ValueError("Landmarks list cannot be empty")
        if len(landmarks) < 468:
            raise ValueError(f"Expected at least 468 landmarks, got {len(landmarks)}")
        self.landmarks = landmarks

    def _get_landmark_point(self, index):
        """Get landmark point with validation."""
        try:
            if index < 0 or index >= len(self.landmarks):
                raise IndexError(f"Landmark index {index} out of range")
            lm = self.landmarks[index]
            if not hasattr(lm, "x") or not hasattr(lm, "y"):
                raise AttributeError("Landmark missing x or y attribute")
            return (lm.x, lm.y)
        except Exception as exc:
            # Return center point as fallback
            return (0.5, 0.5)

    def get_head_yaw(self):
        """Detect head yaw direction with error handling."""
        try:
            nose_tip = self._get_landmark_point(1)
            left_eye_corner = self._get_landmark_point(263)
            right_eye_corner = self._get_landmark_point(33)

            dist_nose_to_left = abs(nose_tip[0] - left_eye_corner[0])
            dist_nose_to_right = abs(nose_tip[0] - right_eye_corner[0])

            ratio_threshold = 1.8

            if dist_nose_to_left > dist_nose_to_right * ratio_threshold:
                return "Left"
            elif dist_nose_to_right > dist_nose_to_left * ratio_threshold:
                return "Right"
            else:
                return "Center"
        except Exception:
            # Default to center if error
            return "Center"

    def is_looking_down(self, pitch_threshold=0.65):
        face_left = self._get_landmark_point(234)
        face_right = self._get_landmark_point(454)
        nose_tip = self._get_landmark_point(1)
        chin = self._get_landmark_point(152)

        face_width = dist.euclidean(face_left, face_right)
        nose_to_chin_dist = dist.euclidean(nose_tip, chin)

        if face_width == 0:
            return False

        ratio = nose_to_chin_dist / face_width
        return ratio < pitch_threshold

    def is_drowsy(self, ear_threshold=0.22):
        LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
        RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]

        left_ear = self.get_eye_aspect_ratio(LEFT_EYE_INDICES)
        right_ear = self.get_eye_aspect_ratio(RIGHT_EYE_INDICES)

        avg_ear = (left_ear + right_ear) / 2.0

        return avg_ear < ear_threshold

    def get_eye_aspect_ratio(self, eye_indices):
        eye_points = np.array(
            [self._get_landmark_point(i) for i in eye_indices], dtype="float32"
        )
        A = dist.euclidean(eye_points[1], eye_points[5])
        B = dist.euclidean(eye_points[2], eye_points[4])
        C = dist.euclidean(eye_points[0], eye_points[3])

        if C == 0:
            return 0.3

        ear = (A + B) / (2.0 * C)
        return ear

    def is_unfocused(self):
        head_yaw = self.get_head_yaw()
        if head_yaw != "Center":
            return f"Looking {head_yaw}"

        if self.is_drowsy():
            return "Drowsy"

        return None
