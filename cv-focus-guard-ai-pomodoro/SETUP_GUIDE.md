# Focus Guard - Complete Setup Guide

## Quick Start (5 Minutes)

### Windows

```bash
# 1. Clone the repository
git clone https://github.com/irgidev/cv-focus-guard-ai-pomodoro.git
cd cv-focus-guard-ai-pomodoro

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download audio files (or create placeholder MP3 files)
# Create assets folder and add:
# - assets/session_end.mp3
# - assets/focus_alert.mp3

# 5. Run the app
python main.py
```

### macOS

```bash
# 1. Clone the repository
git clone https://github.com/irgidev/cv-focus-guard-ai-pomodoro.git
cd cv-focus-guard-ai-pomodoro

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download audio files
# Create assets folder and add:
# - assets/session_end.mp3
# - assets/focus_alert.mp3

# 5. Run the app
python main.py
```

### Linux

```bash
# 1. Install Python and requirements
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv libpython3-dev

# 2. Clone the repository
git clone https://github.com/irgidev/cv-focus-guard-ai-pomodoro.git
cd cv-focus-guard-ai-pomodoro

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Download audio files
# Create assets folder and add MP3 files

# 6. Run the app
python main.py
```

---

## Detailed Setup Instructions

### Step 1: System Requirements

**Minimum:**

- Python 3.9 or newer
- 300 MB free disk space
- Webcam (with USB/integrated)
- 2 GB RAM
- Multi-core processor recommended

**Recommended:**

- Python 3.10+
- 500 MB free disk space
- HD Webcam (720p+)
- 4+ GB RAM
- Modern processor (2018+)

### Step 2: Python Installation

Check if Python is installed:

```bash
python --version  # Windows/macOS
python3 --version  # Linux
```

If not installed:

- **Windows**: Download from [python.org](https://www.python.org/downloads/)
  - ✅ Check "Add Python to PATH" during installation
- **macOS**: `brew install python3`
- **Linux**: `sudo apt-get install python3`

### Step 3: Repository Setup

```bash
# Clone the repository
git clone https://github.com/irgidev/cv-focus-guard-ai-pomodoro.git

# Navigate to directory
cd cv-focus-guard-ai-pomodoro

# Verify structure
# You should see: main.py, focus_detector.py, brain.py, requirements.txt, etc.
```

### Step 4: Virtual Environment

Create an isolated Python environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

You'll see `(venv)` prefix in your terminal when activated.

To deactivate later: `deactivate`

### Step 5: Install Dependencies

```bash
# Upgrade pip first (recommended)
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

This installs:

- customtkinter - GUI framework
- opencv-python - Computer vision
- mediapipe - Face detection
- pygame - Audio playback
- scipy - Scientific computing
- And other dependencies

**Installation time:** 5-10 minutes (depends on internet speed)

### Step 6: Audio Files Setup

The app requires two MP3 audio files for alerts and session completion.

#### Option A: Use Existing Audio Files

1. Find two MP3 files on your computer
2. Create `assets/` folder in project root
3. Copy files with these names:
   - `session_end.mp3` (plays when session completes)
   - `focus_alert.mp3` (plays during distraction alerts)

#### Option B: Download Free Sounds

1. Visit [Freesound.org](https://freesound.org/) or [Pixabay](https://pixabay.com/sound-effects/)
2. Search for:
   - "notification sound" or "bell sound" → session_end.mp3
   - "alert sound" or "warning sound" → focus_alert.mp3
3. Download as MP3 format
4. Create `assets/` folder and place files

#### Option C: Create Silent Audio (Testing Only)

If you don't have audio files, the app will show warnings but won't crash.
To suppress warnings, either:

- Create dummy MP3 files (1 second silence)
- Or comment out sound playback in `main.py` (line ~278)

### Step 7: Verify Installation

Run the test script:

```bash
python main.py
```

**Expected outcome:**

- GUI window opens (400x760 pixels)
- Webcam initializes and shows feed
- All controls are interactive
- No error messages

If you see errors, refer to the [Troubleshooting](#troubleshooting) section below.

---

## Configuration

### Basic Settings (`config.py`)

```python
# Timer defaults
WORK_MIN = 25  # Work session duration (minutes)
SHORT_BREAK_MIN = 5  # Short break (minutes)
LONG_BREAK_MIN = 20  # Long break (minutes)

# Alert thresholds
VISUAL_WARNING_THRESHOLD_FRAMES = 15  # Frames before showing warning
SOUND_ALERT_THRESHOLD_FRAMES = 45  # Frames before playing sound
```

### Advanced Settings

Edit `config.py` to customize:

```python
# Focus detection sensitivity
MIN_DETECTION_CONFIDENCE = 0.5  # 0.0-1.0 (higher = stricter)
MIN_TRACKING_CONFIDENCE = 0.5  # 0.0-1.0

# Algorithm learning
AI_MAX_CHANGE_PERCENT = 0.25  # ±25% change limit per session

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

---

## Troubleshooting

### "Python is not recognized"

**Windows:**

- Reinstall Python and ✅ check "Add Python to PATH"
- Or use: `C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\python.exe`

**macOS/Linux:**

- Use `python3` instead of `python`

### "ModuleNotFoundError: No module named 'customtkinter'"

```bash
# Activate virtual environment first
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Then install
pip install customtkinter
```

### "No module named 'cv2' (OpenCV)"

```bash
pip install opencv-python opencv-contrib-python
```

### "Cannot play sound: No such file"

**Check:**

1. `assets/` folder exists in project root
2. `session_end.mp3` file exists
3. `focus_alert.mp3` file exists
4. Files are valid MP3 format

**Fix:**

```bash
# Create empty assets folder
mkdir assets  # macOS/Linux
md assets     # Windows

# Download audio files from Freesound or Pixabay
# Place them in the assets folder
```

### Webcam Not Detected

**Check:**

1. Webcam is plugged in (USB webcam) or built-in
2. No other app is using the webcam
3. Camera permissions granted (Windows/macOS)

**Try:**

```bash
# Test with different camera index
# Edit main.py line ~524:
self.cap = cv2.VideoCapture(0)  # Try 0, 1, 2, etc.
```

### "Permission denied" on Linux

```bash
# Grant camera permissions
sudo usermod -a -G video $USER
# Log out and log back in
```

### High CPU/Memory Usage

**Solutions:**

1. Close other applications
2. Reduce webcam resolution in `config.py`:
   ```python
   WEBCAM_FRAME_SIZE = (360, 270)  # Change to (240, 180)
   ```
3. Increase frame update interval:
   ```python
   WEBCAM_UPDATE_INTERVAL = 10  # Change to 30 (ms)
   ```
4. Disable MediaPipe refinements:
   ```python
   REFINE_LANDMARKS = False
   ```

### Face Detection Not Working

**Check lighting:**

1. Ensure good room lighting
2. Face should be clearly visible
3. Adjust distance from camera (30-60 cm ideal)

**Adjust sensitivity:**

```python
MIN_DETECTION_CONFIDENCE = 0.3  # More lenient (0.3-0.5)
MIN_DETECTION_CONFIDENCE = 0.7  # More strict (0.7-0.9)
```

### Application Crashes on Startup

**Check logs:**

```bash
# View recent errors
cat logs/focus_guard.log  # macOS/Linux
type logs\focus_guard.log  # Windows
```

**Common causes:**

- Virtual environment not activated
- Python version too old (need 3.9+)
- Missing audio files
- Corrupted requirements installation

**Solution:**

```bash
# Clean reinstall
deactivate
rm -rf venv  # Or: rmdir /s venv on Windows
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

---

## Running from Source vs. Distribution

### From Source (Current)

```bash
python main.py
```

✅ Pros: Easy to modify, debug, customize
❌ Cons: Requires Python installation, slower startup

### Distribution (Future)

```bash
focus-guard.exe  # Windows
# or standalone app
```

---

## Performance Tips

1. **Faster Startup:**
   - Close unused applications
   - Pre-warm GPU (if available)
   - Use SSD for project storage

2. **Better Detection:**
   - Good lighting
   - Clear face visibility
   - Steady camera mount
   - Clean camera lens

3. **Lower CPU Usage:**
   - Increase `WEBCAM_UPDATE_INTERVAL`
   - Reduce `WEBCAM_FRAME_SIZE`
   - Set `REFINE_LANDMARKS = False`

4. **Smoother Experience:**
   - Close browser tabs/apps
   - Disable antivirus scanning folder
   - Use wired network (if not network dependent)

---

## Uninstall

To completely remove:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows

# Delete project folder
rm -rf cv-focus-guard-ai-pomodoro  # macOS/Linux
rmdir /s cv-focus-guard-ai-pomodoro  # Windows
```

---

## Getting Help

1. **Check Documentation:**
   - [README.md](README.md) - Feature overview
   - [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) - Change history

2. **Review Logs:**
   - `logs/focus_guard.log` - Application errors and info

3. **Consult Code:**
   - Comments in `main.py`, `focus_detector.py`, `brain.py`
   - Docstrings in functions

---

## Next Steps

1. ✅ Complete setup
2. ✅ Run `python main.py`
3. ✅ Set your focus duration
4. ✅ Add quick goals
5. ✅ Start your first session
6. ✅ Experience the focus detection
7. 📖 Read [README.md](README.md) for feature guide

---

**Setup Version:** 1.0.0  
**Last Updated:** February 19, 2026  
**Status:** Production Ready ✅
