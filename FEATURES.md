# Focus Guard - Feature List

## Core Features

### 🍅 Pomodoro Timer

- **Adaptive Work Sessions**: AI-powered session duration that adjusts based on your focus performance (10-60 minutes)
- **Smart Break Calculation**: Break duration automatically calculated using sqrt(work_time) formula
- **Session Tracking**: Counts completed sessions and triggers long breaks after 4 sessions
- **Pause/Resume**: Full control over timer with pause and resume functionality
- **Quick Goals**: Set session goals to stay focused on specific tasks
- **Session Statistics**: Track total focus time, distractions, and completed sessions

### 👁️ Computer Vision Focus Detection

- **Real-time Face Tracking**: Uses MediaPipe Face Mesh (468 facial landmarks)
- **Head Pose Detection**: Detects when you're looking:
  - Left
  - Right
  - Down
  - Away from screen
- **Drowsiness Detection**: Eye aspect ratio (EAR) analysis to detect closed eyes
- **No Face Detection**: Alerts when you leave your desk
- **Visual Feedback**: Live webcam preview with focus status overlay
- **Distraction Counter**: Tracks unfocused moments during each session

### 🎵 Audio Alerts

- **Session End Sound**: Notification when work session or break completes
- **Focus Alert Sound**: Warning when distraction detected
- **Optional Audio**: Toggle sound on/off based on preference
- **Graceful Degradation**: Application continues if audio system unavailable

### 🧠 AI Adaptive Learning

- **Reinforcement Learning**: Adjusts optimal session length based on distraction patterns
- **Persistent Memory**: Saves learned optimal duration to disk
- **Dynamic Penalties**: Adds time penalties for excessive distractions
- **Performance Rewards**: Increases session length for focused work
- **Bounds Protection**: Keeps sessions between 10-60 minutes

## Accountability Features

### 🤝 Peer Accountability Collaboration

- **Session Code Sharing**: Create 6-character alphanumeric codes for study sessions
- **Multi-user Support**: Multiple students can join the same accountability session
- **Real-time Goal Sharing**: Share your session goals with accountability partners
- **Distraction Notifications**: Partners notified when you get distracted
- **Event Polling**: See partner updates in real-time (2-second polling interval)
- **File-based Sync**: Uses JSONL files for simple, reliable collaboration
- **Optional Toggle**: Enable/disable accountability feature as needed
- **Auto-ignore Own Events**: Clean separation of your events from partner events

### 📊 Teacher Reports (Academic Accountability)

- **Encrypted Report Generation**: RSA-2048 OAEP encryption for privacy
- **Digital Signatures**: RSA-PSS signatures prevent tampering
- **Report Metrics**:
  - Sessions completed
  - Total focus time (minutes)
  - Total distractions
  - Last session distractions
  - Timestamp
- **Teacher Key Management**: Load teacher's public key for encryption
- **Tamper-proof**: Students cannot edit reports without detection
- **Optional Toggle**: Enable/disable teacher reporting feature
- **Automatic Keypair**: App generates its own signing keypair automatically

### 🔐 Teacher Verification Tools

- **Keypair Generation**: Teachers can generate RSA-2048 keypairs
- **Report Decryption**: Decrypt student reports with private key
- **Signature Verification**: Validate report authenticity
- **Focus Quality Rating**: Automatic quality assessment (Excellent/Good/Fair/Needs Improvement)
- **Command-line Interface**: `verify_report.py` for easy verification
- **Batch Processing Support**: Can verify multiple reports

## User Interface

### 🎨 Modern Design

- **Dark Mode**: CustomTkinter dark theme
- **Two-panel Layout**:
  - Left: Timer, camera, and controls
  - Right: Accountability and reports
- **980x760 Resolution**: Wide layout for better visibility
- **Color-coded Status**:
  - Green: Connected/Active
  - Yellow: Warnings
  - Gray: Neutral/Inactive
- **Live Updates**: Real-time UI updates for timer, focus status, and partner activity

### 📱 Controls & Settings

- **Start/Stop Timer**: Main timer control
- **Pause/Resume**: Mid-session control
- **Reset Timer**: Return to initial state
- **Camera Toggle**: Enable/disable webcam
- **Accountability Controls**:
  - Create new session
  - Join existing session
  - Disconnect from session
  - View partner goals
- **Report Controls**:
  - Load teacher key
  - Generate encrypted report
  - Status indicators

## Production-Ready Features

### 🛡️ Security & Validation

- **Input Validation**: All user inputs validated
- **Session Code Validation**: Regex pattern matching, length limits
- **Path Traversal Protection**: Sanitized file paths
- **Payload Size Limits**:
  - Collaboration events: 100KB max
  - Reports: 10KB max
- **Rate Limiting**: Max 10 events/second for collaboration
- **Key Size Validation**: Minimum 2048-bit RSA keys
- **File Size Checks**: Prevent loading malicious large files

### ⚡ Error Handling & Resilience

- **Graceful Degradation**: Features fail independently without crashing app
- **Try-except Protection**: All major operations wrapped in error handling
- **Resource Cleanup**: Proper camera, audio, and file cleanup on exit
- **Atomic File Operations**: Write-to-temp-then-rename for data safety
- **Fallback Values**: Safe defaults when calculations fail
- **Production Readiness Check**: Validates environment on startup

### 📝 Logging & Monitoring

- **Comprehensive Logging**: All events logged to `logs/focus_guard.log`
- **Error Tracking**: Detailed error messages with stack traces
- **Info Messages**: Session creation, joins, reports
- **Warning Messages**: Rate limits, validation failures, resource issues
- **Rotating Logs**: Automatic log management

### 🧪 Testing & Quality

- **Automated Test Suite**: 21 comprehensive tests
- **Use Case Testing**: Real-world scenario validation
- **Edge Case Testing**: Boundary conditions and error scenarios
- **Integration Testing**: End-to-end workflow validation
- **CI/CD Ready**: Exit codes for automated testing
- **Test Categories**:
  - Collaboration (8 tests)
  - Config (2 tests)
  - Report Manager (4 tests)
  - Integration (1 test)
  - Edge Cases (6 tests)

## Technical Specifications

### 🔧 Dependencies

- **CustomTkinter 5.2.2**: Modern UI framework
- **OpenCV (cv2)**: Webcam capture and image processing
- **MediaPipe**: Face mesh detection
- **NumPy**: Numerical operations
- **SciPy**: Distance calculations
- **Pygame**: Audio playback
- **Cryptography**: RSA encryption and signatures

### 📁 File Structure

```
cv-focus-guard-ai-pomodoro/
├── main.py                     # Main application
├── brain.py                    # Adaptive timer AI
├── focus_detector.py           # CV focus detection
├── collaboration.py            # Peer accountability
├── report_manager.py           # Encrypted reports
├── verify_report.py            # Teacher verification tool
├── config.py                   # Configuration
├── logger.py                   # Logging setup
├── data/
│   ├── focus_memory.txt        # AI learning data
│   ├── collaboration/          # Session files
│   ├── reports/                # Generated reports
│   └── keys/                   # Encryption keys
├── logs/                       # Application logs
├── assets/                     # Sound files
└── tests/
    ├── auto_smoke_test.py      # Legacy tests
    └── run_tests.py            # Production test suite
```

### 🔐 Cryptography Details

- **Encryption Algorithm**: RSA-OAEP with SHA-256
- **Signature Algorithm**: RSA-PSS with SHA-256
- **Key Size**: 2048-bit (minimum)
- **Key Format**: PEM encoding
- **Report Format**: JSON envelope with base64-encoded encrypted data

## Platform Support

### 💻 Operating Systems

- ✅ Windows (Primary development platform)
- ✅ macOS (Compatible)
- ✅ Linux (Compatible)

### 🎥 Hardware Requirements

- **Webcam**: Required for focus detection
- **Speakers/Headphones**: Optional for audio alerts
- **Display**: Minimum 1024x768 resolution recommended
- **RAM**: 500MB+ available
- **Storage**: 100MB for application and data

## Configuration Options

### ⚙️ Customizable Settings

- **Work Duration**: 25 minutes default (AI-adjusted)
- **Short Break**: 5 minutes
- **Long Break**: 20 minutes
- **Sessions to Long Break**: 4
- **Collaboration Code Length**: 6 characters
- **Polling Interval**: 2000ms (2 seconds)
- **Sound Files**: Customizable paths
- **Data Directories**: Configurable locations

## Future Enhancements

### 🚀 Potential Features

- Data visualization and analytics dashboard
- Cloud synchronization for multi-device support
- Mobile companion app
- Scheduled work sessions
- Pomodoro technique variants (52/17, 90-minute deep work)
- Integration with calendar apps
- Export statistics to CSV/Excel
- Custom focus detection sensitivity
- Multiple simultaneous accountability sessions
- Group leaderboards and achievements

---

**Version**: 1.0.0  
**Last Updated**: February 21, 2026  
**License**: See LICENSE file  
**Documentation**: See README.md, SETUP_GUIDE.md, TEACHER_VERIFICATION_GUIDE.md
