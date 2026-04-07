import sqlite3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table for students (Normalized)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    teacher_key TEXT NOT NULL,
                    UNIQUE(name, teacher_key)
                )
            ''')
            # Table for sessions (Normalized)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    duration_mins INTEGER NOT NULL,
                    distractions INTEGER NOT NULL,
                    focus_score REAL NOT NULL,
                    goals TEXT,
                    FOREIGN KEY (student_id) REFERENCES students (id)
                )
            ''')
            
            # Indexing for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_teacher_key ON students(teacher_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_student_id ON sessions(student_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON sessions(timestamp)')
            
            conn.commit()

    def register_student(self, name: str, teacher_key: str):
        """Registers a student or returns existing student's ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO students (name, teacher_key)
                VALUES (?, ?)
            ''', (name, teacher_key))
            conn.commit()
            
            cursor.execute('SELECT id FROM students WHERE name = ? AND teacher_key = ?', (name, teacher_key))
            result = cursor.fetchone()
            return result[0] if result else None

    def save_session(self, student_name: str, teacher_key: str, duration_mins: int, distractions: int, focus_score: float, goals: list):
        """Saves a session by student name and teacher key."""
        student_id = self.register_student(student_name, teacher_key)
        if student_id is None:
            return False
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        goals_json = json.dumps(goals)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (student_id, timestamp, duration_mins, distractions, focus_score, goals)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_id, timestamp, duration_mins, distractions, focus_score, goals_json))
            conn.commit()
        return True

    def get_teacher_students(self, teacher_key: str):
        """Gets all students linked to a teacher key."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE teacher_key = ?', (teacher_key,))
            return [dict(row) for row in cursor.fetchall()]

    def get_student_sessions(self, teacher_key: str):
        """Gets all sessions for all students under a teacher key."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, st.name as student_name 
                FROM sessions s
                JOIN students st ON s.student_id = st.id
                WHERE st.teacher_key = ? 
                ORDER BY s.timestamp DESC
            ''', (teacher_key,))
            return [dict(row) for row in cursor.fetchall()]

    def get_summary_stats(self, teacher_key: str):
        """Aggregated stats per student."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    st.name,
                    COUNT(s.id) as total_sessions,
                    SUM(s.duration_mins) as total_time,
                    AVG(s.focus_score) as avg_focus,
                    SUM(s.distractions) as total_distractions
                FROM students st
                LEFT JOIN sessions s ON st.id = s.student_id
                WHERE st.teacher_key = ?
                GROUP BY st.id
            ''', (teacher_key,))
            return cursor.fetchall()

    def get_periodic_aggregation(self, teacher_key: str, period='daily'):
        """Daily or Weekly aggregation of focus scores and distractions."""
        if period == 'weekly':
            date_format = '%Y-W%W'  # Year-WeekNumber
        else:
            date_format = '%Y-%m-%d'
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT 
                    strftime('{date_format}', timestamp) as period,
                    AVG(focus_score) as avg_focus,
                    SUM(distractions) as total_distractions,
                    SUM(duration_mins) as total_duration
                FROM sessions s
                JOIN students st ON s.student_id = st.id
                WHERE st.teacher_key = ?
                GROUP BY period
                ORDER BY period ASC
            ''', (teacher_key,))
            return cursor.fetchall()
