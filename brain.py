import os
import math
from pathlib import Path
from collections import deque

class AdaptiveTimer:
    def __init__(self, current_optimal_mins=25.0, memory_path="focus_memory.txt"):
        # Validate inputs
        if not isinstance(current_optimal_mins, (int, float)):
            raise ValueError("current_optimal_mins must be a number")
        if current_optimal_mins < 1 or current_optimal_mins > 120:
            raise ValueError("current_optimal_mins must be between 1 and 120")

        self.memory_path = memory_path
        self.optimal_mins = self._load_or_default(float(current_optimal_mins))
        self.learning_rate = 0.2
        
        # Advanced Focus Engine State
        self.focus_data_window = deque(maxlen=300)  # ~30 seconds at 10fps
        self.score_history = []

    def calculate_next_session(self, distractions):
        """Calculate next session duration based on distractions."""
        if distractions < 0:
            distractions = 0

        # Calculate reward
        if distractions <= 1:
            reward = 1.0
        elif distractions <= 4:
            reward = 0.0
        else:
            reward = -0.5 * (distractions - 4)

        # Clamp reward
        reward = max(-3.0, min(1.0, reward))

        step_size = 5.0
        change = self.learning_rate * reward * step_size

        self.optimal_mins += change
        # Enforce bounds: 10-60 minutes
        self.optimal_mins = max(10.0, min(60.0, self.optimal_mins))

        self._save()
        return round(self.optimal_mins, 2)

    def calculate_focus_score(self, frame_is_focused: bool):
        """
        Calculates a real-time focus score based on frame history.
        Uses time-weighted scoring: penalizes continuous distraction more.
        """
        self.focus_data_window.append(1.0 if frame_is_focused else 0.0)
        
        if not self.focus_data_window:
            return 100.0

        # Penalize clusters of distraction
        window_list = list(self.focus_data_window)
        total_frames = len(window_list)
        distracted_frames = window_list.count(0.0)
        
        # Continuity penalty: longer streaks of distraction hit harder
        penalty_multiplier = 1.0
        consecutive_distractions = 0
        max_consecutive = 0
        for f in window_list:
            if f == 0.0:
                consecutive_distractions += 1
                max_consecutive = max(max_consecutive, consecutive_distractions)
            else:
                consecutive_distractions = 0
        
        # Extra penalty if max_consecutive is high (> 3 seconds at 10fps)
        if max_consecutive > 30:
            penalty_multiplier = 1.5
            
        base_score = (1.0 - (distracted_frames / total_frames)) * 100
        weighted_score = base_score / penalty_multiplier
        
        final_score = max(0.0, min(100.0, weighted_score))
        self.score_history.append(final_score)
        return round(final_score, 2)

    def get_session_focus_avg(self):
        """Returns the average focus score for the current session."""
        if not self.score_history:
            return 100.0
        return round(sum(self.score_history) / len(self.score_history), 2)

    def generate_report(self, session_data: dict):
        """
        Generates a session report summary.
        session_data should contain: duration_mins, distractions, goals
        """
        duration = session_data.get('duration_mins', 0)
        distractions = session_data.get('distractions', 0)
        avg_score = self.get_session_focus_avg()
        
        summary = f"Session Summary:\n"
        summary += f"- Duration: {duration} mins\n"
        summary += f"- Distractions Detected: {distractions}\n"
        summary += f"- Average Focus Score: {avg_score}/100\n"
        
        if avg_score > 85:
            performance = "Excellent"
            msg = "Keep it up, you are in the zone!"
        elif avg_score > 60:
            performance = "Good"
            msg = "Stable focus, try to reduce long gaze-aways."
        else:
            performance = "Needs Attention"
            msg = "High level of distraction detected. Take a longer break."
            
        summary += f"- Performance: {performance}\n"
        summary += f"- Insight: {msg}"
            
        # Reset history for next session
        self.score_history = []
        self.focus_data_window.clear()
            
        return {
            "avg_focus": avg_score,
            "total_distractions": distractions,
            "total_study_time": duration,
            "performance": performance,
            "summary": summary
        }

    def _load_or_default(self, default_value):
        """Load saved value with error handling."""
        try:
            memory_file = Path(self.memory_path)
            if not memory_file.exists():
                return float(default_value)

            with open(self.memory_path, "r", encoding="utf-8") as handle:
                content = handle.read().strip()
                if not content:
                    return float(default_value)
                return max(10.0, min(60.0, float(content)))
        except (OSError, ValueError):
            return float(default_value)

    def _save(self):
        """Save current value safely."""
        try:
            memory_file = Path(self.memory_path)
            memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(memory_file, "w", encoding="utf-8") as handle:
                handle.write(f"{self.optimal_mins:.2f}")
        except OSError:
            pass
