"""Adaptive timer with reinforcement learning.

Production features:
- Input validation for all parameters
- Safe file operations with error handling
- Bounds checking for calculated values
"""

import os
from pathlib import Path


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

    def calculate_next_session(self, distractions):
        """Calculate next session duration based on distractions."""
        # Validate input
        if not isinstance(distractions, (int, float)):
            raise ValueError("distractions must be a number")
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

        return int(self.optimal_mins)

    def _load_or_default(self, default_value):
        """Load saved value with error handling."""
        if not self.memory_path:
            return float(default_value)

        try:
            memory_file = Path(self.memory_path)
            if not memory_file.exists():
                return float(default_value)

            # Check file size (prevent loading huge files)
            if memory_file.stat().st_size > 1000:
                return float(default_value)

            with open(self.memory_path, "r", encoding="utf-8") as handle:
                content = handle.read().strip()
                if not content:
                    return float(default_value)
                value = float(content)
        except (OSError, ValueError) as exc:
            # Log error but continue with default
            print(f"Warning: Could not load memory from {self.memory_path}: {exc}")
            return float(default_value)

        # Validate loaded value
        return max(10.0, min(60.0, value))

    def _save(self):
        """Save current value with error handling."""
        if not self.memory_path:
            return

        try:
            # Create parent directory if needed
            memory_file = Path(self.memory_path)
            memory_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to temp file first, then rename (atomic operation)
            temp_path = memory_file.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as handle:
                handle.write(f"{self.optimal_mins:.2f}\n")

            # Atomic rename
            temp_path.replace(memory_file)
        except OSError as exc:
            # Log error but don't crash
            print(f"Warning: Could not save memory to {self.memory_path}: {exc}")
