import asyncio, json, os, io
from datetime import datetime
from typing import Dict, Optional
import numpy as np
from scipy.signal import resample_poly
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from aiortc import RTCPeerConnection, MediaStreamTrack, RTCDataChannel
from aiortc.mediastreams import AudioFrame
import webrtcvad
from faster_whisper import WhisperModel
from transformers import MarianMTModel, MarianTokenizer
import edge_tts
from pydub import AudioSegment

app = FastAPI(title="Realtime Interpreter Server (WebRTC)")

WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL", "small")
whisper = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")

MODEL_NAMES = {
    ("no", "en"): "Helsinki-NLP/opus-mt-no-en",
    ("nb", "en"): "Helsinki-NLP/opus-mt-no-en",
    ("nn", "en"): "Helsinki-NLP/opus-mt-no-en",
    ("pl", "en"): "Helsinki-NLP/opus-mt-pl-en",
    ("en", "pl"): "Helsinki-NLP/opus-mt-en-pl",
    ("en", "no"): "Helsinki-NLP/opus-mt-en-no",
    ("en", "nb"): "Helsinki-NLP/opus-mt-en-no",
    ("en", "nn"): "Helsinki-NLP/opus-mt-en-no",
}
_cache: Dict[str, tuple] = {}

def norm_lang(code: Optional[str]) -> str:
    if not code:
        return "en"
    c = code.lower()
    if c in ("nb","nn","no","nb-no","nn-no"): return "no"
    if c.startswith("en"): return "en"
    if c.startswith("pl"): return "pl"
    return c[:2]

def get_translator(src: str, tgt: str):
    key = (src, tgt)
    name = MODEL_NAMES.get(key)
    if not name:
        if src != "en" and tgt != "en":
            return None
        raise RuntimeError(f"No MT model for {src}->{tgt}")
    if key not in _cache:
        tok = MarianTokenizer.from_pretrained(name)
        mdl = MarianMTModel.from_pretrained(name)
        _cache[key] = (tok, mdl)
    return _cache[key]

async def translate_text(text: str, src: str, tgt: str) -> str:
    src = norm_lang(src); tgt = norm_lang(tgt)
    if src == tgt: return text
    tr = get_translator(src, tgt)
    if tr is None:
        mid = await translate_text(text, src, "en")
        return await translate_text(mid, "en", tgt)
    tok, mdl = tr
    batch = tok([text], return_tensors="pt", padding=True)
    gen = mdl.generate(**batch, max_new_tokens=256)
    return tok.decode(gen[0], skip_special_tokens=True)

def pick_voice(tgt: str) -> str:
    tgt = norm_lang(tgt)
    return "en-US-AriaNeural" if tgt=="en" else ("nb-NO-IselinNeural" if tgt in ("no","nb","nn") else ("pl-PL-ZofiaNeural" if tgt=="pl" else "en-US-AriaNeural"))

def to_float32(pcm16: bytes) -> np.ndarray:
    i16 = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32)
    return i16 / 32768.0

def resample_to_16k(pcm: np.ndarray, src_rate: int) -> np.ndarray:
    if src_rate == 16000: return pcm
    return resample_poly(pcm, 16000, src_rate)

async def tts_to_frames(text: str, lang: str, sample_rate: int = 48000):
    voice = pick_voice(lang)
    tts = edge_tts.Communicate(text, voice=voice, rate="+0%")
    mp3_bytes = bytearray()
    async for chunk in tts.stream():
        if chunk["type"] == "audio":
            mp3_bytes.extend(chunk["data"])
    if not mp3_bytes: return
    audio = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
    audio = audio.set_channels(1).set_frame_rate(sample_rate)
    raw = audio.raw_data
    frame_size = int(sample_rate * 0.02); step = frame_size * 2
    for i in range(0, len(raw), step):
        chunk = raw[i:i+step]
        if len(chunk) < step: break
        frame = AudioFrame(format="s16", layout="mono", samples=frame_size)
        frame.planes[0].update(chunk); frame.sample_rate = sample_rate
        yield frame

class TTSAudioTrack(MediaStreamTrack):
    kind = "audio"
    def __init__(self):
        super().__init__()
        self.queue: asyncio.Queue = asyncio.Queue()
    async def recv(self) -> AudioFrame:
        return await self.queue.get()

class Session:
    def __init__(self, pc: RTCPeerConnection, target_lang: str = "en", log_dir: str = "logs"):
        self.pc = pc
        self.target_lang = norm_lang(target_lang)
        self.vad = webrtcvad.Vad(2)
        self.tts_track = TTSAudioTrack()
        self.caption_channel: Optional[RTCDataChannel] = None
        os.makedirs(log_dir, exist_ok=True)
        today = datetime.utcnow().strftime("%Y%m%d")
        self.log_path = os.path.join(log_dir, f"transcripts_{today}.txt")
    def log_line(self, src_lang: str, tgt_lang: str, text: str):
        ts = datetime.utcnow().isoformat()
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {src_lang}->{tgt_lang}: {text}\n")
    async def handle_audio_frame(self, frame: AudioFrame):
        pcm16 = frame.to_ndarray(format="s16", layout="mono")
        pcm_bytes = pcm16.tobytes()
        f32 = to_float32(pcm_bytes)
        f32_16k = resample_to_16k(f32, frame.sample_rate)
        i16_16k = (np.clip(f32_16k, -1, 1) * 32767.0).astype(np.int16).tobytes()
        step = int(16000 * 0.02) * 2
        voiced = bytearray()
        for i in range(0, len(i16_16k), step):
            chunk = i16_16k[i:i+step]
            if len(chunk) < step: break
            if self.vad.is_speech(chunk, 16000): voiced.extend(chunk)
        if len(voiced) >= 16000 * 2:
            await self.process_voiced(voiced)
    async def process_voiced(self, voiced_bytes: bytes):
        f32 = to_float32(voiced_bytes)
        segments, info = whisper.transcribe(f32, language=None, vad_filter=False, beam_size=1, condition_on_previous_text=False)
        text = " ".join([s.text.strip() for s in segments]).strip()
        if not text: return
        src_lang = norm_lang(info.language)
        translated = await translate_text(text, src_lang, self.target_lang)
        self.log_line(src_lang, self.target_lang, translated)
        if self.caption_channel and self.caption_channel.readyState == "open":
            try:
                self.caption_channel.send(json.dumps({"type":"caption","src_lang":src_lang,"tgt_lang":self.target_lang,"text":translated}))
            except Exception: pass
        async for af in tts_to_frames(translated, self.target_lang, sample_rate=48000):
            await self.tts_track.queue.put(af)

@app.get("/health")
async def health():
    return JSONResponse({"status":"ok"})

@app.post("/offer", response_class=PlainTextResponse)
async def offer(request: Request):
    body = await request.body()
    try:
        data = json.loads(body.decode("utf-8"))
        offer_sdp = data["sdp"]; target_lang = data.get("target_lang","en")
    except Exception:
        offer_sdp = body.decode("utf-8"); target_lang = "en"
    pc = RTCPeerConnection()
    session = Session(pc, target_lang=target_lang)
    pc.addTrack(session.tts_track)
    ch = pc.createDataChannel("captions"); session.caption_channel = ch
    @ch.on("open")
    def _():
        hello = {"type":"hello","message":"captions-channel-ready","log_path":session.log_path,"target_lang":session.target_lang}
        try: ch.send(json.dumps(hello))
        except Exception: pass
    @pc.on("track")
    def on_track(track: MediaStreamTrack):
        if track.kind == "audio":
            async def reader():
                while True:
                    try: frame = await track.recv()
                    except Exception: break
                    await session.handle_audio_frame(frame)
            asyncio.create_task(reader())
    await pc.setRemoteDescription({"type":"offer","sdp":offer_sdp})
    ans = await pc.createAnswer(); await pc.setLocalDescription(ans)
    return pc.localDescription.sdp
