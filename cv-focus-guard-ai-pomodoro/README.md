# Focus Guard: AI-Powered Pomodoro Timer

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)

An intelligent desktop Pomodoro timer that uses AI and your webcam to detect loss of focus and help you stay on track with intelligent session management.

---

## 🎯 About The Project

Focus Guard is a smart productivity tool that enhances the classic **Pomodoro Technique** by integrating real-time AI-powered focus detection. It's designed to combat distractions in the digital age by monitoring your engagement and providing intelligent feedback.

Using your webcam, Focus Guard continuously analyzes your head pose and eye state during work sessions. When it detects that you're looking away or showing signs of drowsiness, it provides gentle alerts to guide you back to your task.

## ✨ Key Features

### Smart Timer Controls

- **Custom Duration**: Set work sessions from 5-120 minutes
- **Auto-calculated Breaks**: Break duration automatically calculated as √(work_duration)
- **Total Focus Goals**: Set daily/session goals with automatic session calculation
- **Dynamic Session Counting**: Sessions adjust automatically as work duration changes

### AI-Powered Focus Detection (Work Sessions Only)

- **Head Pose Estimation**: Detects looking away (left/right) with real-time visual feedback
- **Drowsiness Detection**: Uses Eye Aspect Ratio (EAR) to identify fatigue vs. blinks
- **Gradual Algorithm Learning**: ML adapts work duration by max ±25% per session (prevents drastic changes)

### Tiered Alert System

- **Visual Warnings**: First indicator of lost focus (15 frames)
- **Audio Alerts**: Persistent sound after prolonged unfocus (45 frames)
- **Cooldown System**: 10-second penalty cooldown prevents alert spam

### Gamification & Motivation

- **Quick Goals/To-Do List**: Set and track session objectives
- **Session Completion Dialogs**: Congratulations screens after every completed session
- **Break Rewards**: Motivational messages after break completion
- **Progress Tracking**: Visual session counter with goal visualization

### User-Friendly Interface

- **Modern GUI**: Built with CustomTkinter (dark mode)
- **Live Webcam Feed**: Real-time video with face landmark overlay
- **Distraction Counter**: Track focus lapses per session
- **Responsive Controls**: Pause, resume, and reset functionality

---

## 🛠 Built With

- [Python 3.9+](https://www.python.org/) - Programming language
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern GUI framework
- [OpenCV](https://opencv.org/) - Computer vision library
- [MediaPipe](https://mediapipe.dev/) - ML face detection & pose estimation
- [Pygame](https://www.pygame.org/) - Audio playback
- [NumPy](https://numpy.org/) - Numerical computing
- [SciPy](https://scipy.org/) - Scientific computing

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **pip** (comes with Python)
- **Webcam** (for focus detection)
- **300 MB** free disk space
- **Windows, macOS, or Linux**

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/irgidev/cv-focus-guard-ai-pomodoro.git
cd cv-focus-guard-ai-pomodoro
```

#### 2. Create & Activate Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Set Up Audio Assets

Create an `assets/` folder in the project directory with these audio files:

```
assets/
├── session_end.mp3      # Plays when session completes
└── focus_alert.mp3      # Plays when focus is lost
```

You can:

- Download royalty-free sounds from [Freesound](https://freesound.org/) or [Pixabay](https://pixabay.com/sound-effects/)
- Convert audio files to MP3 format if needed
- Or use any `.mp3` or `.wav` files

#### 5. Run the Application

```bash
python main.py
```

---

## 📖 Usage Guide

### Starting Your First Session

1. **Set Focus Duration**: Select how long you want to work (5-120 minutes)
2. **Set Total Goal** (Optional): Set daily focus target (30-600 minutes)
3. **Add Quick Goals** (Optional): Type goals you want to achieve
4. **Start Timer**: Click "Start" to begin
5. **Focus**: Work while the app monitors your attention
6. **Alerts**: If you lose focus, you'll see warnings and hear alerts
7. **Complete**: After session, view your congratulations screen with completed goals
8. **Break**: Automatic break duration calculated and displayed

### Configuration

Customize settings in `config.py`:

```python
# Timer defaults (minutes)
WORK_MIN = 25
SHORT_BREAK_MIN = 5
LONG_BREAK_MIN = 20

# Alert thresholds (frames)
VISUAL_WARNING_THRESHOLD_FRAMES = 15
SOUND_ALERT_THRESHOLD_FRAMES = 45

# Algorithm constraints
AI_MAX_CHANGE_PERCENT = 0.25  # ±25% max change per session
```

### Features Explained

#### Auto-calculated Breaks

The break duration is calculated as the square root of the work session:

- 5-min session → ~2 min break
- 25-min session → 5 min break
- 100-min session → 10 min break

This provides proportional recovery time that scales naturally.

#### AI Adaptation

The adaptive algorithm learns your optimal focus duration:

- Adjusts based on distraction count per session
- Changes limited to ±25% to prevent drastic shifts
- Constrained changes ensure gradual, sustainable improvements
- You can override by manually setting duration anytime

#### Dynamic Sessions

Set a total focus goal and watch session count adjust:

- Goal: 120 mins, Duration: 5 mins → Need 24 sessions
- Duration changes to 6 mins → Recalculates to 20 sessions
- Flexible and responsive to your workflow

---

## 🎓 Understanding the Detection System

### Focus Detection Metrics

**Head Yaw (Looking Left/Right)**

- Tracked via nose tip and eye positions
- Threshold: 1.8x ratio between left/right eye distances
- Triggers warning if sustained > 15 frames

**Drowsiness (Eye Closure)**

- Uses Eye Aspect Ratio (EAR) for each eye
- EAR < 0.22 indicates closed/closing eyes
- Differentiates blinks (< 3 frames) from drowsiness

---

## 📊 Project Structure

```
cv-focus-guard-ai-pomodoro/
├── main.py                 # Main application entry point
├── focus_detector.py       # Focus detection logic
├── brain.py               # Adaptive algorithm (AI learning)
├── config.py              # Configuration constants
├── logger.py              # Logging utilities
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── LICENSE                # MIT License
├── DEVELOPMENT_LOG.md     # Complete change history
├── assets/                # Audio files
│   ├── session_end.mp3
│   └── focus_alert.mp3
├── data/                  # Application data
│   └── focus_memory.txt   # Algorithm memory/history
└── logs/                  # Application logs
    └── focus_guard.log
```

---

## 🔍 Troubleshooting

### "No module named 'customtkinter'"

```bash
pip install --upgrade customtkinter
```

### "Cannot play sound: No such file"

- Ensure `assets/` folder exists in project root
- Verify `session_end.mp3` and `focus_alert.mp3` are present
- Check file permissions

### Webcam Not Working

- Check Windows/macOS/Linux permissions for camera access
- Try testing with another app first (like Zoom)
- In code, change `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)` if using different camera

### Face Detection Errors

- Ensure good lighting
- Keep face clearly visible to webcam
- Adjust `MIN_DETECTION_CONFIDENCE` in `config.py` if detection is sensitive

### High Memory/CPU Usage

- Close other applications
- Reduce video resolution in `config.py`
- Disable webcam feed during break periods

---

## 📝 Development Log

See [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) for complete change history, commit messages, and architectural decisions.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [MediaPipe](https://mediapipe.dev/) - Face detection & tracking
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [OpenCV](https://opencv.org/) - Computer vision processing
- Pomodoro Technique by Francesco Cirillo

---

## 📞 Support

For issues, questions, or suggestions:

- Check the [Troubleshooting](#-troubleshooting) section
- Review [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)
- Open an issue on GitHub

---

**Version:** 1.0.0 | **Status:** Production Ready ✅ | **Last Updated:** February 19, 2026
