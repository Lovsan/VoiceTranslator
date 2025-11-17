# Quick Start: Run Tests Before Work! 🚀

This guide helps you quickly verify the VoiceTranslator application is working before you leave for work.

## One-Line Test Command

From the repository root:
```bash
cd server && ./run_tests.sh
```

**Expected output:**
```
✅ All tests passed! You're good to go to work! 🎉
```

## What Gets Tested?

The test suite validates:
- ✅ Language code normalization (English, Norwegian, Polish)
- ✅ Audio processing utilities
- ✅ Voice selection for different languages
- ✅ Translation model configuration
- ✅ Core module structure

## First Time Setup

If you haven't installed dependencies yet:
```bash
cd server
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Running the Application

After tests pass, start the server:
```bash
cd server
python server_webrtc.py
```

The server will be available at: `http://localhost:8765`

## Troubleshooting

**Tests fail?**
- Ensure all dependencies are installed: `pip install -r requirements.txt requirements-dev.txt`
- Check Python version: `python --version` (requires 3.8+)

**Server won't start?**
- Check if port 8765 is available: `lsof -i :8765`
- Install FFmpeg if not present: `sudo apt-get install ffmpeg`

## Client Setup (Optional)

To use the mobile client:
```bash
cd client-expo-webrtc
npm install
npm start
```

Update the server URL in `App.tsx` to match your server's IP address.

## Need More Info?

- Full testing guide: [TESTING.md](TESTING.md)
- Server setup: [README.md](../README.md)
- Server API docs: [README.md](README.md)

---

**Pro Tip:** Add this to your morning routine:
```bash
cd /path/to/VoiceTranslator/server && ./run_tests.sh && echo "Ready for work!" || echo "Fix needed!"
```
