import sqlite3
import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

# Optional: MongoDB Support for Production (Vercel)
try:
    from pymongo import MongoClient
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.mongo_uri = os.environ.get("MONGO_URI")
        self.use_mongo = HAS_PYMONGO and self.mongo_uri is not None
        
        if self.use_mongo:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client.get_database("focus_guard")
            self.students_col = self.db.students
            self.sessions_col = self.db.sessions
            # Create indexes for MongoDB
            self.students_col.create_index([("name", 1), ("teacher_key", 1)], unique=True)
            self.sessions_col.create_index([("student_id", 1)])
            self.sessions_col.create_index([("timestamp", -1)])
        else:
            self._init_sqlite()

    def _get_sqlite_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self):
        with self._get_sqlite_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    teacher_key TEXT NOT NULL,
                    UNIQUE(name, teacher_key)
                )
            ''')
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
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_teacher_key ON students(teacher_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_student_id ON sessions(student_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON sessions(timestamp)')
            conn.commit()

    def register_student(self, name: str, teacher_key: str):
        if self.use_mongo:
            student = self.students_col.find_one_and_update(
                {"name": name, "teacher_key": teacher_key},
                {"$set": {"name": name, "teacher_key": teacher_key}},
                upsert=True,
                return_document=True
            )
            return str(student["_id"])
        else:
            with self._get_sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR IGNORE INTO students (name, teacher_key) VALUES (?, ?)', (name, teacher_key))
                conn.commit()
                cursor.execute('SELECT id FROM students WHERE name = ? AND teacher_key = ?', (name, teacher_key))
                result = cursor.fetchone()
                return result[0] if result else None

    def save_session(self, student_name: str, teacher_key: str, duration_mins: int, distractions: int, focus_score: float, goals: list):
        student_id = self.register_student(student_name, teacher_key)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if self.use_mongo:
            self.sessions_col.insert_one({
                "student_id": student_id,
                "student_name": student_name,
                "teacher_key": teacher_key,
                "timestamp": timestamp,
                "duration_mins": duration_mins,
                "distractions": distractions,
                "focus_score": focus_score,
                "goals": goals
            })
            return True
        else:
            goals_json = json.dumps(goals)
            with self._get_sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sessions (student_id, timestamp, duration_mins, distractions, focus_score, goals)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (student_id, timestamp, duration_mins, distractions, focus_score, goals_json))
                conn.commit()
            return True

    def get_teacher_students(self, teacher_key: str):
        if self.use_mongo:
            return list(self.students_col.find({"teacher_key": teacher_key}))
        else:
            with self._get_sqlite_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM students WHERE teacher_key = ?', (teacher_key,))
                return [dict(row) for row in cursor.fetchall()]

    def get_student_sessions(self, teacher_key: str):
        if self.use_mongo:
            sessions = list(self.sessions_col.find({"teacher_key": teacher_key}).sort("timestamp", -1))
            for s in sessions:
                s['id'] = str(s.pop('_id'))
            return sessions
        else:
            with self._get_sqlite_connection() as conn:
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
        if self.use_mongo:
            pipeline = [
                {"$match": {"teacher_key": teacher_key}},
                {"$group": {
                    "_id": "$student_id",
                    "name": {"$first": "$student_name"},
                    "total_sessions": {"$sum": 1},
                    "total_time": {"$sum": "$duration_mins"},
                    "avg_focus": {"$avg": "$focus_score"},
                    "total_distractions": {"$sum": "$distractions"}
                }}
            ]
            results = list(self.sessions_col.aggregate(pipeline))
            return [(r['name'], r['total_sessions'], r['total_time'], r['avg_focus'], r['total_distractions']) for r in results]
        else:
            with self._get_sqlite_connection() as conn:
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
        if self.use_mongo:
            # Simplified for now
            pipeline = [
                {"$match": {"teacher_key": teacher_key}},
                {"$project": {
                    "day": {"$substr": ["$timestamp", 0, 10]},
                    "focus_score": 1,
                    "distractions": 1,
                    "duration_mins": 1
                }},
                {"$group": {
                    "_id": "$day",
                    "avg_focus": {"$avg": "$focus_score"},
                    "total_distractions": {"$sum": "$distractions"},
                    "total_duration": {"$sum": "$duration_mins"}
                }},
                {"$sort": {"_id": 1}}
            ]
            results = list(self.sessions_col.aggregate(pipeline))
            return [(r['_id'], r['avg_focus'], r['total_distractions'], r['total_duration']) for r in results]
        else:
            date_format = '%Y-%m-%d'
            with self._get_sqlite_connection() as conn:
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
