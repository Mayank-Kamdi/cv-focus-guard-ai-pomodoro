import customtkinter as ctk
import os
import threading
import time
import pygame
import cv2
import mediapipe as mp
from tkinter import filedialog
from PIL import Image
import math
from pathlib import Path
import queue

# Local Modular Imports
from focus_detector import FocusDetector
from brain import AdaptiveTimer
from collaboration import CollaborationSession
from storage import DatabaseManager
from teacher import TeacherKeyManager
from logger import logger as app_logger
from config import (
    DATABASE_PATH, 
    KEY_DIR,
    COLLAB_DIR,
    COLLAB_CODE_LENGTH,
    COLLAB_POLL_INTERVAL_MS,
    DATA_DIR,
)

import requests
import logging

# Ensure directories exist
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(KEY_DIR).mkdir(parents=True, exist_ok=True)

try:
    from report_manager import TeacherReportManager
    REPORTS_AVAILABLE = True
except Exception:
    TeacherReportManager = None
    REPORTS_AVAILABLE = False

WORK_MIN = 25
SHORT_BREAK_MIN = 5
LONG_BREAK_MIN = 20
SESSIONS_BEFORE_LONG_BREAK = 4

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_PATH = os.path.join(BASE_DIR, "focus_memory.txt")

SOUND_SESSION_END = "assets/session_end.mp3"
SOUND_FOCUS_ALERT = "assets/focus_alert.mp3"

COLOR_TEXT = "#FFFFFF"
COLOR_WARN = "#FFCC00"


class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Focus Guard")
        self.root.geometry("1100x850")
        self.root.resizable(False, False)

        main_container = ctk.CTkFrame(root, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        left_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=10)

        separator = ctk.CTkFrame(main_container, width=2, fg_color="#444444")
        # Create right frame for status and reports (now scrollable)
        right_frame = ctk.CTkScrollableFrame(main_container, width=420)
        right_frame.pack(side="right", padx=(5, 20), pady=10, fill="both", expand=False)

        self.sessions = 0
        self.is_running = False
        self.is_paused = False
        self.current_session_type = "Work"
        self.timer_thread = None
        self.current_session_distractions = 0
        self.last_session_distractions = 0
        self.last_penalty_time = 0.0
        self.total_focus_seconds = 0
        self.total_distractions = 0
        self.completed_sessions = 0
        self.ai_brain = AdaptiveTimer(
            current_optimal_mins=WORK_MIN, memory_path=MEMORY_PATH
        )
        self.db_manager = DatabaseManager(DATABASE_PATH)
        self.key_manager = TeacherKeyManager(KEY_DIR)
        self.work_duration = int(self.ai_brain.optimal_mins) * 60
        self.current_time = self.work_duration
        self.break_duration = (
            int(math.sqrt(WORK_MIN)) * 60
        )  # Default break = sqrt(work)
        self.total_focus_time_goal = (
            WORK_MIN * 4 * 60
        )  # Default: 4 sessions worth (100 mins)
        self.total_sessions_needed = 4  # Default sessions to reach goal

        self.sound_enabled = True
        try:
            pygame.mixer.init()
        except Exception as exc:
            self.sound_enabled = False
            app_logger.warning("Audio init failed: %s", exc)
        self.cap = None
        self.camera_active = False
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = None
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(
            thickness=1, circle_radius=1, color=(0, 255, 0)
        )
        try:
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        except Exception as exc:
            app_logger.warning("Face mesh init failed: %s", exc)

        self.unfocused_counter = 0
        self.VISUAL_WARNING_THRESHOLD_FRAMES = 15
        self.SOUND_ALERT_THRESHOLD_FRAMES = 45

        # Collaboration and Threading
        self.collab_polling_active = False
        self._frame_queue = queue.Queue(maxsize=1)
        self._stop_camera_worker = False
        self._camera_thread = None
        self._camera_initializing = False

        self.session_label = ctk.CTkLabel(
            left_frame, text="", font=("Helvetica", 24, "bold")
        )
        self.session_label.pack(pady=10)

        self.timer_label = ctk.CTkLabel(
            left_frame, text="", font=("Helvetica", 80, "bold")
        )
        self.timer_label.pack(pady=10)

        stats_frame = ctk.CTkFrame(left_frame)
        stats_frame.pack(pady=5, fill="x", padx=20)

        self.next_focus_label = ctk.CTkLabel(
            stats_frame, text="", font=("Helvetica", 14)
        )
        self.next_focus_label.pack(pady=(8, 2))

        self.current_distractions_label = ctk.CTkLabel(
            stats_frame, text="", font=("Helvetica", 14)
        )
        self.current_distractions_label.pack(pady=2)

        self.last_distractions_label = ctk.CTkLabel(
            stats_frame, text="", font=("Helvetica", 14)
        )
        self.last_distractions_label.pack(pady=(2, 8))

        self.unfocused_reason_label = ctk.CTkLabel(
            left_frame, text="", font=("Helvetica", 16), text_color=COLOR_WARN
        )
        self.unfocused_reason_label.pack(pady=5)

        # Focus Duration Setting
        duration_frame = ctk.CTkFrame(left_frame)
        duration_frame.pack(pady=8, fill="x", padx=20)

        duration_label = ctk.CTkLabel(
            duration_frame,
            text="Focus Duration (mins):",
            font=("Helvetica", 12, "bold"),
        )
        duration_label.pack(side="left", padx=(0, 10))

        duration_options = [str(i) for i in range(5, 121, 5)]
        self.duration_combobox = ctk.CTkComboBox(
            duration_frame,
            values=duration_options,
            state="readonly",
            width=80,
            command=self.update_work_duration,
        )
        self.duration_combobox.set(str(WORK_MIN))
        self.duration_combobox.pack(side="left")

        # Total Focus Time Goal Setting
        total_frame = ctk.CTkFrame(left_frame)
        total_frame.pack(pady=8, fill="x", padx=20)

        total_label = ctk.CTkLabel(
            total_frame,
            text="Total Focus Goal (mins):",
            font=("Helvetica", 12, "bold"),
        )
        total_label.pack(side="left", padx=(0, 10))

        total_options = [str(i) for i in range(30, 601, 30)]
        self.total_time_combobox = ctk.CTkComboBox(
            total_frame,
            values=total_options,
            state="readonly",
            width=80,
            command=self.update_total_focus_time,
        )
        self.total_time_combobox.set(str(int(self.total_focus_time_goal / 60)))
        self.total_time_combobox.pack(side="left")

        sessions_label = ctk.CTkLabel(
            total_frame,
            text=f"({self.total_sessions_needed} sessions)",
            font=("Helvetica", 11),
            text_color="#FFD700",
        )
        sessions_label.pack(side="left", padx=(10, 0))
        self.sessions_indicator = sessions_label

        # Break Duration Display
        break_duration_frame = ctk.CTkFrame(left_frame)
        break_duration_frame.pack(pady=5, fill="x", padx=20)

        break_label = ctk.CTkLabel(
            break_duration_frame,
            text="Break Duration (auto-calculated):",
            font=("Helvetica", 12, "bold"),
        )
        break_label.pack(side="left", padx=(0, 10))

        self.break_duration_display = ctk.CTkLabel(
            break_duration_frame,
            text=f"{int(self.break_duration / 60)} mins",
            font=("Helvetica", 12),
            text_color="#00FF00",
        )
        self.break_duration_display.pack(side="left")

        # Quick Goals / To-Do Section
        goals_frame = ctk.CTkFrame(left_frame)
        goals_frame.pack(pady=8, fill="x", padx=20)

        goals_label = ctk.CTkLabel(
            goals_frame, text="Quick Goals", font=("Helvetica", 12, "bold")
        )
        goals_label.pack(anchor="w", pady=(0, 5))

        goals_input_frame = ctk.CTkFrame(goals_frame, fg_color="transparent")
        goals_input_frame.pack(fill="x", pady=(0, 5))

        self.goal_entry = ctk.CTkEntry(
            goals_input_frame, placeholder_text="Add a quick goal...", height=28
        )
        self.goal_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.goal_entry.bind("<Return>", lambda e: self.add_goal())

        self.add_goal_button = ctk.CTkButton(
            goals_input_frame, text="+", command=self.add_goal, width=30
        )
        self.add_goal_button.pack(side="left")

        self.goals_list_frame = ctk.CTkFrame(goals_frame)
        self.goals_list_frame.pack(fill="both", expand=True)

        self.goals = []
        self.session_goals = []  # Track goals for current session

        self.collab_session = CollaborationSession(
            app_logger,
            code_length=COLLAB_CODE_LENGTH,
        )
        self.collab_polling_active = False
        self.accountability_enabled = ctk.BooleanVar(value=False)

        self.report_manager = None
        self.reports_enabled = ctk.BooleanVar(value=False)
        if not REPORTS_AVAILABLE:
            app_logger.warning("Teacher reports unavailable: cryptography not loaded")

        accountability_frame = ctk.CTkFrame(right_frame)
        accountability_frame.pack(pady=8, fill="x", padx=10)

        accountability_label = ctk.CTkLabel(
            accountability_frame,
            text="Accountability",
            font=("Helvetica", 12, "bold"),
        )
        accountability_label.pack(anchor="w", pady=(0, 5))

        accountability_toggle = ctk.CTkCheckBox(
            accountability_frame,
            text="Enable accountability",
            variable=self.accountability_enabled,
            command=self.on_accountability_toggle,
        )
        accountability_toggle.pack(anchor="w", pady=(0, 5))

        code_frame = ctk.CTkFrame(accountability_frame, fg_color="transparent")
        code_frame.pack(fill="x", pady=(0, 5))

        code_label = ctk.CTkLabel(
            code_frame,
            text="Session Code:",
            font=("Helvetica", 11),
        )
        code_label.pack(side="left", padx=(0, 6))

        self.code_entry = ctk.CTkEntry(
            code_frame,
            placeholder_text="Enter code",
            height=28,
            width=120,
        )
        self.code_entry.pack(side="left", padx=(0, 6))

        create_button = ctk.CTkButton(
            code_frame,
            text="Create",
            command=self.create_collab_session,
            width=70,
        )
        create_button.pack(side="left", padx=(0, 6))

        join_button = ctk.CTkButton(
            code_frame,
            text="Join",
            command=self.join_collab_session,
            width=70,
        )
        join_button.pack(side="left")

        self.collab_status_label = ctk.CTkLabel(
            accountability_frame,
            text="Accountability: Not connected",
            font=("Helvetica", 12),
            text_color="#CCCCCC",
        )
        self.collab_status_label.pack(anchor="w", pady=(2, 0))

        self.collab_event_label = ctk.CTkLabel(
            accountability_frame,
            text="",
            font=("Helvetica", 11),
            text_color=COLOR_WARN,
        )
        self.collab_event_label.pack(anchor="w")

        partner_goals_label = ctk.CTkLabel(
            accountability_frame,
            text="Partner Goals",
            font=("Helvetica", 11, "bold"),
        )
        partner_goals_label.pack(anchor="w", pady=(6, 2))

        self.partner_goals_display = ctk.CTkTextbox(
            accountability_frame,
            height=120,
            width=260,
        )
        self.partner_goals_display.pack(fill="x")
        self.partner_goals_display.configure(state="disabled")

        self.collab_controls = [
            self.code_entry,
            create_button,
            join_button,
        ]
        self.set_accountability_enabled(self.accountability_enabled.get())

        reports_frame = ctk.CTkFrame(right_frame)
        reports_frame.pack(pady=8, fill="x", padx=10)

        reports_label = ctk.CTkLabel(
            reports_frame,
            text="Teacher Reports",
            font=("Helvetica", 12, "bold"),
        )
        reports_label.pack(anchor="w", pady=(0, 5))

        reports_toggle = ctk.CTkCheckBox(
            reports_frame,
            text="Enable teacher reports",
            variable=self.reports_enabled,
            command=self.on_reports_toggle,
        )
        reports_toggle.pack(anchor="w", pady=(0, 5))

        # Teacher Reporting Fields
        student_name_frame = ctk.CTkFrame(reports_frame, fg_color="transparent")
        student_name_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(student_name_frame, text="Student Name:", font=("Helvetica", 11)).pack(side="left", padx=(0, 5))
        self.student_name_entry = ctk.CTkEntry(student_name_frame, height=28, placeholder_text="Your Name")
        self.student_name_entry.pack(side="left", fill="x", expand=True)

        teacher_key_frame = ctk.CTkFrame(reports_frame, fg_color="transparent")
        teacher_key_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(teacher_key_frame, text="Teacher Key:", font=("Helvetica", 11)).pack(side="left", padx=(0, 5))
        self.teacher_key_entry = ctk.CTkEntry(teacher_key_frame, height=28, placeholder_text="Enter 8-char Key")
        self.teacher_key_entry.pack(side="left", fill="x", expand=True)

        key_actions_frame = ctk.CTkFrame(reports_frame, fg_color="transparent")
        key_actions_frame.pack(fill="x", pady=5)
        
        generate_key_button = ctk.CTkButton(
            key_actions_frame,
            text="Generate New Key",
            command=self.generate_new_teacher_key,
            width=120,
            fg_color="#3498db"
        )
        generate_key_button.pack(side="left", padx=(0, 5))

        load_key_button = ctk.CTkButton(
            key_actions_frame,
            text="Use Key",
            command=self.confirm_teacher_key,
            width=100
        )
        load_key_button.pack(side="left")

        generate_report_button = ctk.CTkButton(
            reports_frame,
            text="Generate report",
            command=self.generate_teacher_report,
        )
        generate_report_button.pack(fill="x", pady=(0, 5))

        self.report_status_label = ctk.CTkLabel(
            reports_frame,
            text="Teacher reports: Disabled",
            font=("Helvetica", 11),
            text_color="#CCCCCC",
        )
        self.report_status_label.pack(anchor="w")

        self.report_controls = [
            generate_report_button,
        ]
        self.set_reports_enabled(self.reports_enabled.get())

        control_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        control_frame.pack(pady=10)

        self.start_button = ctk.CTkButton(
            control_frame, text="Start", command=self.start_timer, width=100
        )
        self.start_button.pack(side="left", padx=5)

        self.pause_button = ctk.CTkButton(
            control_frame,
            text="Pause",
            command=self.pause_timer,
            width=100,
            state="disabled",
        )
        self.pause_button.pack(side="left", padx=5)

        self.reset_button = ctk.CTkButton(
            control_frame, text="Reset", command=self.reset_timer, width=100
        )
        self.reset_button.pack(side="left", padx=5)

        # --- Webcam Preview at TOP of Right Sidebar ---
        self.webcam_label = ctk.CTkLabel(right_frame, text="")
        self.webcam_label.pack(pady=(0, 20), side="top", before=accountability_frame)

        self.update_display()
        self.update_webcam()

    def update_display(self):
        mins, secs = divmod(self.current_time, 60)
        self.timer_label.configure(text=f"{mins:02d}:{secs:02d}")
        self.session_label.configure(
            text=f"{self.current_session_type} Session ({self.sessions}/{self.total_sessions_needed})"
        )
        self.next_focus_label.configure(
            text=f"Next Focus: {int(self.work_duration / 60)} min"
        )
        self.current_distractions_label.configure(
            text=f"Session Distractions: {self.current_session_distractions}"
        )
        self.last_distractions_label.configure(
            text=f"Last Session Distractions: {self.last_session_distractions}"
        )
        # Update break duration display
        self.break_duration_display.configure(
            text=f"{int(self.break_duration / 60)} mins"
        )

    def add_goal(self):
        goal_text = self.goal_entry.get().strip()
        if goal_text:
            self.goals.append(goal_text)
            self.goal_entry.delete(0, "end")
            self.update_goals_display()
            if self.is_accountability_enabled():
                self.collab_session.publish_event(
                    "goals_update",
                    {"goals": self.goals},
                )

    def update_work_duration(self, value=None):
        try:
            new_duration = int(self.duration_combobox.get())
            self.work_duration = new_duration * 60
            # Recalculate break duration as sqrt(work_duration)
            self.break_duration = int(math.sqrt(new_duration)) * 60
            self.recalculate_sessions_needed()
            if not self.is_running:
                self.current_time = self.work_duration
                self.update_display()
        except ValueError:
            pass

    def update_total_focus_time(self, value=None):
        try:
            new_total = int(self.total_time_combobox.get())
            self.total_focus_time_goal = new_total * 60
            self.recalculate_sessions_needed()
            if not self.is_running:
                self.update_display()
        except ValueError:
            pass

    def recalculate_sessions_needed(self):
        work_mins = int(self.work_duration / 60)
        total_mins = int(self.total_focus_time_goal / 60)
        self.total_sessions_needed = max(1, total_mins // work_mins)
        self.sessions_indicator.configure(
            text=f"({self.total_sessions_needed} sessions)"
        )

    def remove_goal(self, index):
        if 0 <= index < len(self.goals):
            self.goals.pop(index)
            self.update_goals_display()
            if self.is_accountability_enabled():
                self.collab_session.publish_event(
                    "goals_update",
                    {"goals": self.goals},
                )

    def show_session_completion_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Session Complete!")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.grab_set()

        # Center the dialog on the root window
        dialog.transient(self.root)
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = (
            self.root.winfo_y()
            + (self.root.winfo_height() - dialog.winfo_height()) // 2
        )
        dialog.geometry(f"+{x}+{y}")

        # Congratulations heading
        congrats_label = ctk.CTkLabel(
            dialog,
            text="🎉 Congratulations! 🎉",
            font=("Helvetica", 20, "bold"),
            text_color="#00FF00",
        )
        congrats_label.pack(pady=15)

        message_label = ctk.CTkLabel(
            dialog,
            text="You've completed a focused work session!",
            font=("Helvetica", 14),
        )
        message_label.pack(pady=10)

        # Goals completed section
        if self.session_goals:
            goals_heading = ctk.CTkLabel(
                dialog, text="Goals Completed:", font=("Helvetica", 12, "bold")
            )
            goals_heading.pack(pady=(10, 5))

            goals_text_frame = ctk.CTkFrame(dialog)
            goals_text_frame.pack(pady=5, padx=20, fill="both", expand=True)

            goals_display = ctk.CTkTextbox(goals_text_frame, height=120, width=350)
            goals_display.pack(fill="both", expand=True)
            goals_display.configure(state="normal")

            for goal in self.session_goals:
                goals_display.insert("end", f"✓ {goal}\n")

            goals_display.configure(state="disabled")
        else:
            no_goals_label = ctk.CTkLabel(
                dialog,
                text="No goals set for this session.",
                font=("Helvetica", 12),
                text_color="#CCCCCC",
            )
            no_goals_label.pack(pady=20)

        # Close button
        close_button = ctk.CTkButton(
            dialog, text="Continue", command=dialog.destroy, font=("Helvetica", 12)
        )
        close_button.pack(pady=15)

    def show_break_completion_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Break Complete!")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.grab_set()

        # Center the dialog on the root window
        dialog.transient(self.root)
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = (
            self.root.winfo_y()
            + (self.root.winfo_height() - dialog.winfo_height()) // 2
        )
        dialog.geometry(f"+{x}+{y}")

        # Reward heading
        reward_label = ctk.CTkLabel(
            dialog,
            text="✨ Great Job! ✨",
            font=("Helvetica", 20, "bold"),
            text_color="#FFD700",
        )
        reward_label.pack(pady=15)

        message_label = ctk.CTkLabel(
            dialog,
            text="You've earned your well-deserved break!",
            font=("Helvetica", 14),
        )
        message_label.pack(pady=10)

        rest_message = ctk.CTkLabel(
            dialog,
            text="Get refreshed and ready for the next session!",
            font=("Helvetica", 12),
            text_color="#00FF00",
        )
        rest_message.pack(pady=10)

        # Close button
        close_button = ctk.CTkButton(
            dialog, text="Continue", command=dialog.destroy, font=("Helvetica", 12)
        )
        close_button.pack(pady=15)

    def update_goals_display(self):
        for widget in self.goals_list_frame.winfo_children():
            widget.destroy()

        for i, goal in enumerate(self.goals):
            goal_item_frame = ctk.CTkFrame(
                self.goals_list_frame, fg_color="transparent"
            )
            goal_item_frame.pack(fill="x", pady=2)

            goal_label = ctk.CTkLabel(
                goal_item_frame,
                text=f"• {goal}",
                font=("Helvetica", 11),
                justify="left",
            )
            goal_label.pack(side="left", fill="x", expand=True, anchor="w")

            delete_btn = ctk.CTkButton(
                goal_item_frame,
                text="✓",
                command=lambda idx=i: self.remove_goal(idx),
                width=25,
                height=20,
                font=("Helvetica", 10),
            )
            delete_btn.pack(side="right", padx=(5, 0))

    def on_accountability_toggle(self):
        self.set_accountability_enabled(self.accountability_enabled.get())

    def set_accountability_enabled(self, enabled: bool):
        if not enabled:
            self.stop_collaboration()
            self.collab_event_label.configure(text="")
            self.update_partner_goals([])
            self.update_collab_status("Accountability: Disabled")
        else:
            self.update_collab_status("Accountability: Not connected")

        for control in self.collab_controls:
            control.configure(state="normal" if enabled else "disabled")

    def is_accountability_enabled(self):
        return bool(self.accountability_enabled.get())

    def update_partner_goals(self, goals):
        self.partner_goals_display.configure(state="normal")
        self.partner_goals_display.delete("1.0", "end")
        if goals:
            for goal in goals:
                self.partner_goals_display.insert("end", f"• {goal}\n")
        else:
            self.partner_goals_display.insert("end", "No goals shared yet.")
        self.partner_goals_display.configure(state="disabled")

    def on_reports_toggle(self):
        self.set_reports_enabled(self.reports_enabled.get())

    def set_reports_enabled(self, enabled: bool):
        if not REPORTS_AVAILABLE:
            self.reports_enabled.set(False)
            enabled = False
            self.update_report_status("Teacher reports: Unavailable", state="error")
        elif enabled:
            if self.report_manager is None:
                self.report_manager = TeacherReportManager(app_logger, DATA_DIR)
            self.update_report_status("Teacher reports: Enabled")
        else:
            self.update_report_status("Teacher reports: Disabled")

        for control in self.report_controls:
            control.configure(state="normal" if enabled else "disabled")

    def update_report_status(self, text, state="neutral"):
        if state == "error":
            color = COLOR_WARN
        elif state == "connected":
            color = "#00FF00"
        else:
            color = "#CCCCCC"
        self.report_status_label.configure(text=text, text_color=color)

    def load_teacher_key(self):
        if not self.reports_enabled.get():
            return
        if self.report_manager is None:
            self.update_report_status("Teacher reports: Unavailable", state="error")
            return

        key_path = filedialog.askopenfilename(
            title="Select Teacher Public Key",
            filetypes=[("PEM files", "*.pem"), ("All files", "*.*")],
        )
        if not key_path:
            return
        try:
            self.report_manager.load_teacher_public_key_from_file(key_path)
            self.update_report_status("Teacher key loaded", state="connected")
        except Exception as exc:
            app_logger.warning("Failed to load teacher key: %s", exc)
            self.update_report_status("Teacher key load failed", state="error")

    def build_report_payload(self):
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sessions_completed": self.completed_sessions,
            "total_focus_minutes": int(self.total_focus_seconds / 60),
            "total_distractions": self.total_distractions,
            "last_session_distractions": self.last_session_distractions,
        }

    def generate_teacher_report(self):
        if not self.reports_enabled.get():
            return
        
        # This manual button now shows the result of the LAST completed session or current progress
        avg_score = self.ai_brain.get_session_focus_avg()
        duration = int((self.work_duration - self.current_time) / 60) if self.is_running else int(self.work_duration / 60)
        
        report = {
            "avg_focus": avg_score,
            "total_distractions": self.current_session_distractions,
            "total_study_time": duration,
            "summary": f"Current session status:\n- Focus: {avg_score}%\n- Distractions: {self.current_session_distractions}\n- Time: {duration} mins"
        }
        self._show_report_dialog_automated(report)

    def _show_report_dialog_automated(self, report):
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Teacher Report")
        dialog.geometry("450x400")
        
        ctk.CTkLabel(dialog, text="Session Report", font=("Helvetica", 18, "bold")).pack(pady=10)
        report_text = f"Avg Focus Score: {report['avg_focus']}/100\n"
        report_text += f"Total Distractions: {report['total_distractions']}\n"
        report_text += f"Study Time: {report['total_study_time']} mins\n\n"
        report_text += report['summary']
        
        textbox = ctk.CTkTextbox(dialog, height=180, width=400)
        textbox.pack(pady=10)
        textbox.insert("0.0", report_text)
        textbox.configure(state="disabled")
        
        dashboard_url = "http://localhost:5000/dashboard"
        ctk.CTkLabel(dialog, text=f"Teachers can view this at:\n{dashboard_url}", 
                     font=("Helvetica", 10), text_color="#3498db").pack(pady=5)
        
        # Sync with backend if key is set
        student_name = self.student_name_entry.get().strip()
        teacher_key = self.teacher_key_entry.get().strip()
        if student_name and teacher_key:
            self.send_to_backend(
                student_name, 
                teacher_key, 
                report['total_study_time'], 
                report['total_distractions'], 
                report['avg_focus'], 
                self.session_goals
            )
            self.update_report_status(f"Report synced for {student_name}", state="connected")

        ctk.CTkButton(dialog, text="Close", command=dialog.destroy).pack(pady=10)

    def generate_new_teacher_key(self):
        new_key = self.key_manager.generate_key()
        self.teacher_key_entry.delete(0, "end")
        self.teacher_key_entry.insert(0, new_key)
        self.update_report_status(f"Generated Key: {new_key}", state="connected")

    def confirm_teacher_key(self):
        key = self.teacher_key_entry.get().strip()
        if self.key_manager.validate_key(key):
            self.update_report_status(f"Using Key: {key}", state="connected")
        else:
            self.update_report_status("Invalid key format (need 8 chars)", state="error")

    def send_to_backend(self, student_name, teacher_key, duration_mins, distractions, focus_score, goals):
        """Asynchronously sync session data to the Flask dashboard."""
        def _bg_post():
            try:
                url = "http://localhost:5000/submit-data"
                payload = {
                    "student_name": student_name,
                    "teacher_key": teacher_key,
                    "duration_mins": duration_mins,
                    "distractions": distractions,
                    "focus_score": focus_score,
                    "goals": goals 
                }
                requests.post(url, json=payload, timeout=5)
                app_logger.info(f"Successfully synced session for {student_name}")
            except Exception as exc:
                app_logger.debug(f"Dashboard sync failed (likely offline): {exc}")

        threading.Thread(target=_bg_post, daemon=True).start()

    def update_collab_status(self, text, state="neutral"):
        if state == "connected":
            color = "#00FF00"
        elif state == "error":
            color = COLOR_WARN
        else:
            color = "#CCCCCC"
        self.collab_status_label.configure(text=text, text_color=color)

    def create_collab_session(self):
        if not self.is_accountability_enabled():
            return
        code = self.collab_session.create_session(str(COLLAB_DIR))
        self.code_entry.delete(0, "end")
        self.code_entry.insert(0, code)
        self.update_collab_status("Accountability: Connected (host)", state="connected")
        self.collab_event_label.configure(text="Share this code with your partner.")
        self.start_collab_polling()

    def join_collab_session(self):
        if not self.is_accountability_enabled():
            return
        code = self.code_entry.get().strip().upper()
        if not code:
            self.update_collab_status("Accountability: Missing code", state="error")
            return

        joined = self.collab_session.join_session(str(COLLAB_DIR), code)
        if not joined:
            self.update_collab_status(
                "Accountability: Session not found", state="error"
            )
            return

        self.update_collab_status(
            "Accountability: Connected (joined)", state="connected"
        )
        self.collab_event_label.configure(text="Waiting for partner updates...")
        self.start_collab_polling()

    def start_collab_polling(self):
        if self.collab_polling_active or not self.is_accountability_enabled():
            return
        self.collab_polling_active = True
        self.root.after(COLLAB_POLL_INTERVAL_MS, self.poll_collab_events)

    def poll_collab_events(self):
        if not self.collab_polling_active or not self.is_accountability_enabled():
            return

        try:
            events = self.collab_session.poll_events()
            for event in events:
                self.handle_collab_event(event)
        except Exception as exc:
            app_logger.warning("Collaboration polling failed: %s", exc)

        self.root.after(COLLAB_POLL_INTERVAL_MS, self.poll_collab_events)

    def handle_collab_event(self, event):
        event_type = event.get("type")
        payload = event.get("payload", {})

        if event_type == "distraction":
            reason = payload.get("reason", "Unfocused")
            count = payload.get("count")
            message = f"Partner distracted: {reason}"
            if count is not None:
                message += f" (total {count})"
            self.collab_event_label.configure(text=message)
            app_logger.info("Collaboration update: %s", message)
            return

        if event_type == "work_started":
            self.collab_event_label.configure(text="Partner started a work session.")
            return

        if event_type == "work_completed":
            distractions = payload.get("distractions")
            message = "Partner completed a work session"
            if distractions is not None:
                message += f" with {distractions} distractions"
            self.collab_event_label.configure(text=message)
            return

        if event_type == "session_joined":
            self.collab_event_label.configure(text="Partner joined the session.")
            return

        if event_type == "session_left":
            self.collab_event_label.configure(text="Partner left the session.")
            return

        if event_type == "goals_update":
            goals = payload.get("goals", [])
            self.update_partner_goals(goals)
        if event_type == "session_goals":
            goals = payload.get("goals", [])
            self.update_partner_goals(goals)
            return

    def stop_collaboration(self):
        self.collab_polling_active = False
        self.collab_session.disconnect()
        if self.is_accountability_enabled():
            self.update_collab_status("Accountability: Not connected")

    def countdown(self):
        try:
            while self.is_running and self.current_time > 0:
                if not self.is_paused:
                    self.current_time -= 1
                    self.root.after(0, self.update_display)
                    time.sleep(1)

            if self.is_running and self.current_time == 0:
                self.play_sound(SOUND_SESSION_END)
                self.root.after(0, self.on_timer_complete)
        except Exception as exc:
            app_logger.warning("Timer thread failed: %s", exc)

    def start_timer(self):
        if not self.is_running:
            try:
                self.is_running = True
                self.start_button.configure(state="disabled")
                self.pause_button.configure(state="normal")
                self.duration_combobox.configure(state="disabled")
                if self.current_session_type == "Work":
                    self.session_goals = self.goals.copy()
                    self.start_camera()
                    if self.is_accountability_enabled():
                        self.collab_session.publish_event(
                            "work_started",
                            {"session_type": self.current_session_type},
                        )
                        self.collab_session.publish_event(
                            "session_goals",
                            {"goals": self.session_goals},
                        )
                self.timer_thread = threading.Thread(target=self.countdown, daemon=True)
                self.timer_thread.start()
            except Exception as exc:
                app_logger.warning("Start timer failed: %s", exc)
                self.is_running = False
                self.start_button.configure(state="normal")
                self.pause_button.configure(state="disabled", text="Pause")
                self.duration_combobox.configure(state="readonly")

    def pause_timer(self):
        self.is_paused = not self.is_paused
        self.pause_button.configure(text="Resume" if self.is_paused else "Pause")

    def reset_timer(self):
        self.is_running = False
        self.is_paused = False
        self.sessions = 0
        self.current_session_type = "Work"
        self.work_duration = int(self.duration_combobox.get()) * 60
        self.break_duration = int(math.sqrt(int(self.duration_combobox.get()))) * 60
        self.total_focus_time_goal = int(self.total_time_combobox.get()) * 60
        self.recalculate_sessions_needed()
        self.current_time = self.work_duration
        self.current_session_distractions = 0
        self.last_session_distractions = 0
        self.last_penalty_time = 0.0
        self.goals = []
        self.session_goals = []
        self.stop_camera()
        self.update_display()
        self.update_goals_display()
        self.start_button.configure(state="normal")
        self.pause_button.configure(state="disabled", text="Pause")
        self.duration_combobox.configure(state="readonly")
        self.unfocused_reason_label.configure(text="")

    def on_timer_complete(self):
        try:
            if self.current_session_type == "Work":
                self.stop_camera()
                self.last_session_distractions = self.current_session_distractions
                self.completed_sessions += 1
                self.total_focus_seconds += self.work_duration
                
                # Calculate reports and scores
                current_work_mins = int(self.work_duration / 60)
                session_data = {
                    "duration_mins": current_work_mins,
                    "distractions": self.current_session_distractions,
                    "goals": self.session_goals
                }
                report = self.ai_brain.generate_report(session_data)
                focus_score = report["avg_focus"]
                
                next_focus_time = self.ai_brain.calculate_next_session(
                    self.current_session_distractions
                )
                
                if self.is_accountability_enabled():
                    self.collab_session.publish_event(
                        "work_completed",
                        {"distractions": self.current_session_distractions, "score": focus_score},
                    )

                # Constrain algorithm changes to max ±25% per session
                max_increase = current_work_mins * 1.25
                min_decrease = current_work_mins * 0.75
                next_focus_time = max(min(next_focus_time, max_increase), min_decrease)

                self.work_duration = int(next_focus_time * 60)
                self.break_duration = int(math.sqrt(next_focus_time)) * 60

                # Persistent Storage Hook
                student_name = self.student_name_entry.get().strip() or "Guest"
                teacher_key = self.teacher_key_entry.get().strip() or "DEFAULT"
                
                # Save to Local SQLite
                try:
                    self.db_manager.save_session(
                        student_name, 
                        teacher_key, 
                        current_work_mins, 
                        self.last_session_distractions, 
                        focus_score, 
                        self.session_goals
                    )
                except Exception as db_exc:
                    app_logger.error(f"Database save failed: {db_exc}")
                
                # Send to Backend if key is set
                if teacher_key != "DEFAULT":
                    self.send_to_backend(student_name, teacher_key, current_work_mins, self.last_session_distractions, focus_score, self.session_goals)

                # Show completion dialog with goals
                self._show_report_dialog_automated(report)
            elif self.current_session_type in ["Short Break", "Long Break"]:
                self.show_break_completion_dialog()

            self.next_session()
        except Exception as exc:
            app_logger.warning("Timer completion failed: %s", exc)

    def play_sound(self, sound_path):
        """Play a sound file in a separate thread to prevent UI micro-stutters."""
        if not self.sound_enabled:
            return
        
        def _play():
            try:
                if os.path.exists(sound_path):
                    sound = pygame.mixer.Sound(sound_path)
                    sound.play()
            except Exception as e:
                app_logger.debug(f"Sound playback error: {e}")

        threading.Thread(target=_play, daemon=True).start()

    def next_session(self):
        if self.current_session_type == "Work":
            self.sessions += 1
            if self.sessions % SESSIONS_BEFORE_LONG_BREAK == 0:
                self.current_session_type = "Long Break"
                self.current_time = LONG_BREAK_MIN * 60
            else:
                self.current_session_type = "Short Break"
                self.current_time = self.break_duration  # Use calculated break duration
        else:
            self.current_session_type = "Work"
            self.current_time = self.work_duration
            self.current_session_distractions = 0
            self.last_penalty_time = 0.0
            if self.is_running:
                self.start_camera()

        self.is_paused = False
        self.update_display()

        self.timer_thread = threading.Thread(target=self.countdown, daemon=True)
        self.timer_thread.start()

    def update_webcam(self):
        """Purely UI updates - pulls processed frames from the background thread queue."""
        # Auto-trigger camera if it should be active but isn't
        if not self.camera_active and not self._camera_initializing:
            self.start_camera()
            self.webcam_label.configure(image=None, text="Initializing Camera...")
            self.root.after(1000, self.update_webcam)
            return

        if not self.camera_active:
            self.webcam_label.configure(image=None, text="Camera Starting...")
            self.root.after(200, self.update_webcam)
            return

        try:
            # Non-blocking check for new processed frames
            if not self._frame_queue.empty():
                frame_to_display, focused, reason = self._frame_queue.get_nowait()

                # Convert to RGB and then to PIL for CTK
                img = Image.fromarray(frame_to_display)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(360, 270))
                
                # IMPORTANT: Must keep a reference to prevent garbage collection
                self.webcam_label.configure(image=ctk_img, text="")
                self.webcam_label._image_ref = ctk_img

                # Handle Focus Scoring and Alerts
                current_score = self.ai_brain.calculate_focus_score(focused)
                
                if not focused:
                    self.unfocused_counter += 1
                    self.unfocused_reason_label.configure(text=reason, text_color="red")
                    
                    # Logic: If unfocused for 15 frames (~1s), count as 1 distraction
                    if self.unfocused_counter == 15:
                        self.current_session_distractions += 1
                        self.total_distractions += 1
                        self.current_distractions_label.configure(
                            text=f"Session Distractions: {self.current_session_distractions}"
                        )
                        self.play_sound(SOUND_FOCUS_ALERT)
                    
                    # Periodic alert if distraction continues
                    if self.unfocused_counter > 60: 
                        self.play_sound(SOUND_FOCUS_ALERT)
                        self.unfocused_counter = 30 # Reset to midway to avoid immediate re-alerting
                else:
                    self.unfocused_counter = 0
                    self.unfocused_reason_label.configure(text=f"Focus: {int(current_score)}%")
            
        except Exception as exc:
            app_logger.debug(f"UI Camera update skipped: {exc}")
        finally:
            self.root.after(30, self.update_webcam)

    def _camera_worker(self):
        """Background thread for heavy image processing and AI logic."""
        app_logger.info("Camera worker thread started")
        
        # Local Mediapipe instance to avoid thread-safety issues
        with mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as face_mesh:
            
            while not self._stop_camera_worker:
                if not self.camera_active or self.cap is None or not self.cap.isOpened():
                    time.sleep(0.1)
                    continue

                try:
                    ret, frame = self.cap.read()
                    if not ret:
                        time.sleep(0.01)
                        continue

                    # Mirror and resize for processing
                    frame = cv2.flip(frame, 1)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # AI LANDMARK PROCESSING (The CPU-intensive part)
                    results = face_mesh.process(frame_rgb)
                    
                    focused = True
                    reason = ""
                    
                    if results.multi_face_landmarks:
                        for face_landmarks in results.multi_face_landmarks:
                            detector = FocusDetector(face_landmarks.landmark)
                            reason = detector.is_unfocused()
                            focused = reason is None
                            break
                    else:
                        focused = False
                        reason = "Face not detected"

                    # Only put in queue if UI is ready for it (prevents backlog)
                    if self._frame_queue.empty():
                        self._frame_queue.put((frame_rgb, focused, reason))
                        
                except Exception as e:
                    app_logger.warning(f"Worker iteration failed: {e}")
                    time.sleep(0.1)

    def start_camera(self):
        """Initialization logic that launches the worker thread with multiple backend fallbacks."""
        if self.camera_active or self._camera_initializing:
            return

        self._camera_initializing = True
        
        def _launch_bg():
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY] if os.name == 'nt' else [cv2.CAP_ANY]
            cap = None
            
            try:
                for backend in backends:
                    app_logger.info(f"Attempting camera with backend {backend}")
                    cap = cv2.VideoCapture(0, backend)
                    if cap.isOpened():
                        break
                    cap.release()
                    cap = None

                if cap and cap.isOpened():
                    self.cap = cap
                    self.camera_active = True
                    self._stop_camera_worker = False
                    
                    # Start the worker thread if not running
                    if self._camera_thread is None or not self._camera_thread.is_alive():
                        self._camera_thread = threading.Thread(target=self._camera_worker, daemon=True)
                        self._camera_thread.start()
                    
                    app_logger.info("Camera and worker thread active")
                else:
                    app_logger.error("All camera backends failed")
                    self.camera_active = False
            except Exception as e:
                app_logger.error(f"Failed to start camera thread: {e}")
                self.camera_active = False
            finally:
                self._camera_initializing = False

        threading.Thread(target=_launch_bg, daemon=True).start()

    def stop_camera(self):
        if not self.camera_active:
            return

        self.camera_active = False
        self._stop_camera_worker = True
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as exc:
                app_logger.warning("Camera release failed: %s", exc)
        self.cap = None

    def on_closing(self):
        """Cleanup resources on application exit."""
        print("Closing app...")
        self.is_running = False

        # Stop camera with error handling
        try:
            self.stop_camera()
        except Exception as exc:
            app_logger.warning("Error stopping camera: %s", exc)

        # Stop collaboration with error handling
        try:
            self.stop_collaboration()
        except Exception as exc:
            app_logger.warning("Error stopping collaboration: %s", exc)

        # Cleanup pygame mixer
        if self.sound_enabled:
            try:
                pygame.mixer.quit()
            except Exception as exc:
                app_logger.warning("Error stopping audio: %s", exc)

        # Destroy window
        try:
            self.root.destroy()
        except Exception as exc:
            app_logger.error("Error destroying window: %s", exc)


def validate_production_readiness():
    """Validate that the application is ready for production use."""
    issues = []

    # Check critical directories exist
    if not DATA_DIR.exists():
        issues.append(f"Data directory missing: {DATA_DIR}")
    if not COLLAB_DIR.exists():
        issues.append(f"Collaboration directory missing: {COLLAB_DIR}")

    # Check asset files exist (optional, warn only)
    if not Path(SOUND_SESSION_END).exists():
        app_logger.warning("Sound file missing: %s", SOUND_SESSION_END)
    if not Path(SOUND_FOCUS_ALERT).exists():
        app_logger.warning("Sound file missing: %s", SOUND_FOCUS_ALERT)

    # Check write permissions
    try:
        test_file = DATA_DIR / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
    except Exception as exc:
        issues.append(f"Data directory not writable: {exc}")

    if issues:
        app_logger.error("Production readiness check failed:")
        for issue in issues:
            app_logger.error("  - %s", issue)
        print("\nWARNING: Production readiness check failed!")
        for issue in issues:
            print(f"  - {issue}")
        print("\nContinuing anyway...\n")
    else:
        app_logger.info("Production readiness check passed")


if __name__ == "__main__":
    # Validate production readiness
    validate_production_readiness()

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    app = PomodoroTimer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        app_logger.info("Application interrupted by user")
        app.on_closing()
    except Exception as exc:
        app_logger.error("Unexpected error in main loop: %s", exc)
        app.on_closing()
        raise
