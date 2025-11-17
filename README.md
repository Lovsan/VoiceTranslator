# VoiceTranslator
Translates spoken languages in real time to speakers with chosen language with minimal delay.

## Features
- Real-time voice translation using WebRTC
- Supports English, Norwegian (Bokmål/Nynorsk), and Polish
- Automatic language detection with Whisper
- Text-to-speech output in target language
- React Native mobile client with Expo

## Quick Start

### Server Setup
```bash
cd server
pip install -r requirements.txt
python server_webrtc.py
```

The server will start on `http://0.0.0.0:8765`

### Client Setup (React Native/Expo)
```bash
cd client-expo-webrtc
npm install
npm start
```

Update the server URL in `App.tsx` to point to your server's IP address.

## Testing

Run tests before deployment:
```bash
cd server
./run_tests.sh
```

For more details, see [server/TESTING.md](server/TESTING.md)

## Requirements
- Python 3.8+
- FFmpeg (for audio processing)
- Node.js (for mobile client)

## Architecture
- **Server**: FastAPI + WebRTC for real-time audio streaming
- **Client**: React Native with react-native-webrtc
- **ML Models**: Whisper (speech recognition), MarianMT (translation), Edge-TTS (speech synthesis)
