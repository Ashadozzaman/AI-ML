"""
audio.py - voices, lip-sync envelope, draft (placeholder) voices.

  * tts_all()           make one voice file per line with edge-tts (needs internet)
  * make_draft_audio()  offline "robot mumble" so you can test the animation without TTS
  * envelope()          loudness per video frame, used to open/close the mouth
"""
import asyncio
import math
import random
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 16000
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".ogg", ".flac")


# ------------------------------------------------------------------ story helpers
def say_beats(story):
    """Yield (line_id, beat) for every spoken line, in order."""
    n = 0
    for b in story["beats"]:
        if b.get("do") == "say":
            n += 1
            yield b.get("id", f"line_{n:02d}"), b


def find_audio(audio_dir, line_id):
    for ext in AUDIO_EXT:
        p = Path(audio_dir) / f"{line_id}{ext}"
        if p.exists() and p.stat().st_size > 1000:
            return p
    return None


# ------------------------------------------------------------------ decode / envelope
def decode(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


def envelope(samples, fps, sr=SR):
    """Loudness 0..1 for every video frame."""
    spf = max(1, int(sr / fps))
    n = len(samples) // spf + 1
    x = np.pad(samples, (0, n * spf - len(samples)))
    rms = np.sqrt((x.reshape(n, spf) ** 2).mean(axis=1))
    rms = rms / (np.percentile(rms, 95) + 1e-6)
    sm = np.convolve(rms, [0.25, 0.5, 0.25], mode="same")
    return np.clip(sm, 0, 1.2)


# ------------------------------------------------------------------ draft voice (offline)
def make_draft_audio(text, path, seed=1, base_hz=130.0):
    """A speech-like hum with word rhythm. Only for testing animation timing."""
    rnd = random.Random(seed)
    words = text.split()
    parts = []
    for w in words:
        dur = 0.12 + 0.045 * len(w)
        n = int(dur * SR)
        t = np.arange(n) / SR
        f0 = base_hz * (1 + 0.12 * math.sin(rnd.random() * 6.28) + 0.1 * np.sin(2 * math.pi * 3 * t))
        phase = 2 * math.pi * np.cumsum(f0) / SR
        sig = np.sin(phase) + 0.5 * np.sin(2 * phase) + 0.25 * np.sin(3 * phase)
        syl = max(1, round(len(w) / 2.4))
        am = np.abs(np.sin(math.pi * syl * t / dur)) ** 0.6
        edge = np.minimum(1, np.minimum(t / 0.02, (dur - t) / 0.03))
        parts.append((sig * am * edge * 0.35).astype(np.float32))
        gap = 0.28 if w.endswith(",") else 0.5 if w[-1] in "।?!" else 0.05
        parts.append(np.zeros(int(gap * SR), np.float32))
    audio = np.concatenate(parts) if parts else np.zeros(SR, np.float32)
    path = Path(path).with_suffix(".wav")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((np.clip(audio, -1, 1) * 32000).astype(np.int16).tobytes())
    return path


def make_all_draft_audio(story, audio_dir, overwrite=False):
    Path(audio_dir).mkdir(parents=True, exist_ok=True)
    for i, (lid, b) in enumerate(say_beats(story)):
        if not overwrite and find_audio(audio_dir, lid):
            continue
        make_draft_audio(b["text"], Path(audio_dir) / lid, seed=i + 1)
        print("draft voice:", lid)


# ------------------------------------------------------------------ real voices (edge-tts)
EMOTION_VOICE = {            # (rate %, pitch Hz) added on top of the character's own voice settings
    "neutral": (0, 0), "happy": (4, 4), "angry": (6, -3), "scared": (8, 6), "nervous": (8, 6),
    "surprised": (6, 8), "sad": (-8, -4), "thinking": (-6, 0), "scheming": (-4, -2), "smirk": (-2, 0),
}


def tts_settings(voice, emotion):
    dr, dp = EMOTION_VOICE.get(emotion, (0, 0))
    rate = int(voice.get("rate", 0)) + dr
    pitch = int(voice.get("pitch", 0)) + dp
    return f"{rate:+d}%", f"{pitch:+d}Hz"


async def tts_all(story, audio_dir, overwrite=False, retries=3):
    """Create audio/line_XX.mp3 for every 'say' beat with edge-tts. Run with `await` in Jupyter."""
    import edge_tts
    Path(audio_dir).mkdir(parents=True, exist_ok=True)
    for lid, b in say_beats(story):
        out = Path(audio_dir) / f"{lid}.mp3"
        if out.exists() and out.stat().st_size > 1000 and not overwrite:
            print("skip (exists):", lid)
            continue
        voice = story["characters"][b["who"]]["voice"]
        rate, pitch = tts_settings(voice, b.get("emotion", "neutral"))
        for attempt in range(retries):
            try:
                await edge_tts.Communicate(b["text"], voice["name"], rate=rate, pitch=pitch).save(str(out))
                print(f"ok {lid}  {b['who']:8s} {voice['name']} {rate} {pitch}")
                break
            except Exception as e:                       # network hiccup -> retry
                print("retry", lid, e)
                await asyncio.sleep(2)
        else:
            raise RuntimeError(f"Could not create audio for {lid}. Check your internet connection.")


# ------------------------------------------------------------------ mixing
def mix_track(events, total_sec, root, sr=44100, music_path=None, music_gain=0.10):
    """events = [(start_sec, path)] -> mono float array with every line placed at its start."""
    out = np.zeros(int(total_sec * sr) + sr, np.float32)
    for t0, path in events:
        s = decode(path, sr)
        i = int(t0 * sr)
        out[i:i + len(s)] += s[: len(out) - i]
    peak = np.abs(out).max()
    if peak > 0:
        out *= 0.9 / peak
    if music_path and Path(music_path).exists():
        m = decode(music_path, sr)
        reps = int(len(out) / max(len(m), 1)) + 1
        m = np.tile(m, reps)[: len(out)]
        out = out + m * music_gain
        out /= max(1.0, np.abs(out).max() / 0.95)
    return out, sr


def write_wav(path, samples, sr):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((np.clip(samples, -1, 1) * 32000).astype(np.int16).tobytes())
