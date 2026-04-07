# Focus Guard AI: Production Upgrade Walkthrough

The project has been transformed into a student monitoring system with a focus on accountability and analytics.

## 🚀 Key Improvements

### 1. Advanced AI Focus Engine (`brain.py`)
- **Time-Weighted Scoring**: Focus scores now prioritize recent attention patterns while maintaining a rolling history.
- **Session History**: All focus events are tracked in a list for granular analysis rather than being overwritten.
- **Intelligent Feedback**: Automated reports now provide specific, data-driven advice based on distraction peaks.

### 2. Scalable Data Persistence (`storage.py`)
- **Normalized Schema**: Separate `students` and `sessions` tables to ensure data integrity across thousands of entries.
- **High Performance**: Added indexes on `teacher_key` and `timestamp` for near-instant reporting.
- **Dict-Like Interface**: Implemented `sqlite3.Row` for robust field access across the application.

### 3. Teacher Analytics Dashboard (`api.py`)
- **Real-Time Monitoring**: A browser-based dashboard (`http://localhost:5000/dashboard`) with 10s auto-refresh.
- **Visual Trends**: Integrated **Chart.js** to visualize focus scores and distraction distribution.
- **Global Reporting**: One-click CSV export of all student data for administrative records.
- **Status Indicators**: Live color-coded indicators showing which students are currently in productive sessions.

### 4. Secure Accountability (`teacher.py`)
- **Cryptographic Keys**: Upgraded to `secrets`-based 8-character keys for classroom-level security.
- **Collision Prevention**: Automated key verification to ensure uniqueness across the system.

### 5. Seamless UI Integration (`main.py`)
- **Automated Sync**: Session data is automatically pushed to the backend upon completion.
- **Accountability UI**: Enhanced student name and teacher key registration fields within the main app.
- **Fail-Safe Processing**: Background threading for API calls ensures the timer never lags due to network issues.

## 🛠️ How to Run

1. **Start the Backend (Dashboard)**:
   ```pwsh
   python api.py
   ```
   Open `http://localhost:5000/dashboard` in your browser.

2. **Run the Main Application**:
   ```pwsh
   python main.py
   ```
   Enter your **Student Name** and **Teacher Key** (use 'Generate New Key' if you don't have one).

3. **Monitor Live**: 
   Watch the dashboard update as you complete Pomodoro sessions!

## ✅ Goals & Fixes Implemented
- [x] **Fixed Accountabilty**: Focus scores are no longer overwritten; they are appended to a history list.
- [x] **Correct Calculation**: Session time and distraction counts persist accurately.
- [x] **Real-Time Sync**: Students are automatically visible on the teacher dashboard.
- [x] **Visual Analytics**: Focus trends are now visualized rather than just listed.
