# 📁 Google Drive Collaboration Setup

## ✨ Super Simple Cloud Collaboration (No Complex Setup!)

This guide shows you how to enable **zero-configuration cloud collaboration** using Google Drive. Your friend can be anywhere in the world!

---

## 🎯 How It Works

1. **You create a shared Google Drive folder** (one-time, 2 minutes)
2. **Users add it to their Drive** (one-click, 30 seconds)
3. **Google Drive syncs in the background** (automatic)
4. **App auto-detects the folder** (no configuration needed!)

---

## 📝 Setup Instructions

### For the App Creator (You - Do This Once):

#### Step 1: Create the Shared Folder (1 minute)

1. Go to [Google Drive](https://drive.google.com)
2. Click **"New"** → **"Folder"**
3. Name it: **`FocusGuardCollab`** (exact name!)
4. Click **"Create"**

#### Step 2: Share the Folder (1 minute)

1. Right-click the folder → **"Share"**
2. Click **"Change"** under "General access"
3. Select **"Anyone with the link"**
4. Change permission to: **"Editor"** (important!)
5. Click **"Copy link"**
6. Click **"Done"**

#### Step 3: Update the App Code (30 seconds)

1. Open: `cv-focus-guard-ai-pomodoro/gdrive_helper.py`
2. Find line 95 (starts with `SHARED_FOLDER_LINK =`)
3. Replace `YOUR_FOLDER_ID_HERE` with the link you copied
4. Save the file

**Example:**

```python
# Before:
SHARED_FOLDER_LINK = "https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE"

# After (use YOUR actual link):
SHARED_FOLDER_LINK = "https://drive.google.com/drive/folders/1AbC2DeF3GhI4JkL5MnO6PqR7StU8VwX9YzA"
```

#### Step 4: Share the Link with Users

Give your users:

1. The Google Drive folder link
2. The app installer

That's it! You're done!

---

### For Users (Anyone Using the App):

#### One-Time Setup (30 seconds):

1. **Install Google Drive Desktop** (if you don't have it):
   - Download: https://www.google.com/drive/download/
   - Install and sign in with your Google account
   - Let it sync (you'll see a Drive icon in your taskbar)

2. **Add the shared folder**:
   - Click the folder link (get this from whoever created the app)
   - Click **"Add shortcut to Drive"** or **"Add to My Drive"**
   - Wait a few seconds for Google Drive to sync

3. **Run Focus Guard**:
   - The app will automatically detect the Google Drive folder
   - You'll see: **"✓ Using Google Drive (works anywhere!)"**

#### Using Collaboration:

**To Start a Session:**

1. Enable "Accountability" checkbox
2. Click **"Create"**
3. Share the 6-letter code with your friend

**To Join a Session:**

1. Enable "Accountability" checkbox
2. Enter your friend's code
3. Click **"Join"**

**Both of you will now:**

- See each other's focus status in real-time
- See each other's goals
- Get notified when partner loses focus
- Stay accountable together!

---

## 🔍 Troubleshooting

### "Using local folder" message appears

**Problem:** App can't find Google Drive  
**Solutions:**

1. Make sure Google Drive Desktop is installed and running
2. Check that the folder icon appears in your taskbar (Windows) or menu bar (Mac)
3. Open Google Drive folder in File Explorer - make sure you see the `FocusGuardCollab` folder
4. Try restarting the app

### Can't connect to friend's session

**Problem:** Session code doesn't work  
**Solutions:**

1. Make sure BOTH people have the Google Drive folder set up
2. Verify the code is exactly 6 UPPERCASE letters/numbers (case-sensitive)
3. Make sure Google Drive is syncing (check the Drive icon - shouldn't show sync errors)
4. Try creating a new session code

### Google Drive folder not syncing

**Problem:** Changes not appearing  
**Solutions:**

1. Right-click Google Drive icon → Check for sync status
2. Make sure you have internet connection
3. Check Google Drive storage (free tier gives 15GB)
4. Pause and resume sync from Drive settings

---

## 💡 How to Find Your Google Drive Folder

**Windows:**

- Usually at: `C:\Users\YourName\Google Drive\`
- Or check Drive icon → Settings → Folder location

**Mac:**

- Usually at: `/Users/YourName/Google Drive/`
- Or check Drive icon → Preferences → Folder location

**Linux:**

- Usually at: `~/Google Drive/`
- Or wherever you configured it during installation

---

## ✅ Advantages of This Method

**vs Firebase/Cloud Services:**

- ✅ No API keys or credentials needed
- ✅ No server setup required
- ✅ Visual confirmation (see files syncing)
- ✅ Works offline (syncs when back online)
- ✅ 15GB free storage

**vs Manual Shared Folders:**

- ✅ Auto-detection (no path configuration)
- ✅ Works across different computers easily
- ✅ One link setup for all users
- ✅ Always synced in background

---

## 🔒 Privacy & Security

- Session codes are random 6-character codes
- Only people with the code can join your session
- Data is stored in Google Drive (subject to Google's security)
- No data is sent to external servers
- You can delete session files anytime from the Drive folder

---

## 📊 What Data is Shared?

When you collaborate, the following is shared in real-time:

- Focus status (focused/not focused)
- Goals you've set
- Session events (started, paused, etc.)
- Study time and focus time

**NOT shared:**

- Webcam video or images
- Keystrokes or screen content
- Personal files or data
- Location information

---

## 🆘 Still Having Issues?

1. Check that `FocusGuardCollab` folder exists in your Google Drive
2. Make sure Google Drive is actively syncing
3. Try accessing Google Drive in your browser - does the folder appear there?
4. Check the app logs: `cv-focus-guard-ai-pomodoro/logs/focus_guard.log`

---

## 🎓 For Schools/Universities

If you're deploying this for multiple students:

1. Create ONE shared folder as described above
2. Share the folder link via email/LMS/Discord
3. Students just click the link and add to their Drive
4. No IT configuration needed!

**Network Restrictions:**

- Only requires Google Drive access (usually allowed)
- No special ports or firewall rules needed
- Works on school WiFi

---

## 🚀 Advanced: Auto-Add Folder to App Distribution

If you're distributing the app to many users, you can:

1. Update `SHARED_FOLDER_LINK` in `gdrive_helper.py` before distribution
2. Include instructions in your README
3. Users just need to click the link and install Drive Desktop
4. App handles everything else automatically!

---

## 📝 Summary

**You (Creator):**

1. Create `FocusGuardCollab` folder in Google Drive
2. Share with "Anyone with link" as "Editor"
3. Update `SHARED_FOLDER_LINK` in code
4. Distribute app + folder link

**Users:**

1. Install Google Drive Desktop
2. Click folder link → Add to My Drive
3. Run app → It just works!

**No configuration files, no API keys, no complex setup!** 🎉
