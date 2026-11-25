"""
audio.py - voices, lip-sync envelope, draft (placeholder) voices.

How voice files are named
  Every spoken line gets an id like  line_03_a1b2c3  (number + a short fingerprint of the text, the
  character's voice settings and the emotion).  So when you change the story, only the lines that
  changed get new voices - the rest are reused.

Where the timeline looks for a line's audio (first match wins)
  1. audio/line_03.mp3 / .wav     <- YOUR OWN recording (plain number, no fingerprint)
  2. audio/line_03_a1b2c3.mp3     <- generated voice
  3. audio/line_03_a1b2c3.draft.wav  <- offline humming draft (only when draft voices are allowed)
"""
import asyncio
import hashlib
import math
import random
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 16000
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".ogg", ".flac")


# ------------------------------------------------------------------ story helpers
def line_fingerprint(story, beat):
    voice = story["characters"][beat["who"]].get("voice", {})
    raw = "|".join(str(x) for x in (beat["text"], beat.get("emotion", "neutral"), sorted(voice.items())))
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:6]


def say_beats(story):
    """Yield (line_id, beat) for every spoken line, in order."""
    n = 0
    for b in story["beats"]:
        if b.get("do") == "say":
            n += 1
            yield b.get("id", f"line_{n:02d}_{line_fingerprint(story, b)}"), b


def plain_id(line_id):
    parts = line_id.split("_")
    return "_".join(parts[:2]) if len(parts) >= 2 else line_id


def find_audio(audio_dir, line_id):
    """Real audio for a line (your recording first, then generated voice)."""
    d = Path(audio_dir)
    for stem in (plain_id(line_id), line_id):
        for ext in AUDIO_EXT:
            p = d / f"{stem}{ext}"
            if p.exists() and p.stat().st_size > 1000:
                return p
    return None


def find_draft(audio_dir, line_id):
    p = Path(audio_dir) / f"{line_id}.draft.wav"
    return p if p.exists() else None


def audio_status(story, audio_dir):
    """List of (line_id, who, state, text) with state in real / draft / missing."""
    out = []
    for lid, b in say_beats(story):
        state = "real" if find_audio(audio_dir, lid) else "draft" if find_draft(audio_dir, lid) else "missing"
        out.append((lid, b["who"], state, b["text"]))
    return out


def clean_unused_audio(story, audio_dir, delete=False):
    """Lists (and optionally deletes) voice files that no line of the current story uses."""
    keep = set()
    for lid, _ in say_beats(story):
        keep |= {lid, plain_id(lid), lid + ".draft"}
    unused = []
    for p in sorted(Path(audio_dir).glob("*")):
        if p.is_file() and p.stem not in keep:
            unused.append(p)
    for p in unused:
        print(("deleted " if delete else "unused  ") + p.name)
        if delete:
            p.unlink()
    return unused


# ------------------------------------------------------------------ decode / envelope
def decode(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


def envelope(samples, fps, sr=SR):
    """Loudness 0..1 for every video frame (drives the mouth)."""
    spf = max(1, int(sr / fps))
    n = len(samples) // spf + 1
    x = np.pad(samples, (0, n * spf - len(samples)))
    rms = np.sqrt((x.reshape(n, spf) ** 2).mean(axis=1))
    rms = rms / (np.percentile(rms, 95) + 1e-6)
    sm = np.convolve(rms, [0.25, 0.5, 0.25], mode="same")
    return np.clip(sm, 0, 1.2)


# ------------------------------------------------------------------ draft voice (offline)
def make_draft_audio(text, line_id, audio_dir, seed=1, base_hz=130.0):
    """A speech-like hum with word rhythm. ONLY for testing the animation timing - not a real voice."""
    rnd = random.Random(seed)
    parts = []
    for w in text.split():
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
    path = Path(audio_dir) / f"{line_id}.draft.wav"
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((np.clip(audio, -1, 1) * 32000).astype(np.int16).tobytes())
    return path


def make_all_draft_audio(story, audio_dir):
    for i, (lid, b) in enumerate(say_beats(story)):
        if not find_audio(audio_dir, lid) and not find_draft(audio_dir, lid):
            make_draft_audio(b["text"], lid, audio_dir, seed=i + 1)
            print("draft voice (placeholder hum):", lid)


# ------------------------------------------------------------------ voice effects (make characters sound different)
POLISH = True        # gentle warmth + presence EQ, soft compression and a tiny room echo: less "flat computer voice". Set audio.POLISH = False to turn off
ROOM_ECHO = 0.10     # 0 = dry, 0.10 = a little room. (only used when POLISH is on)


def voice_fx(src, dst, semitones=0.0, tempo=1.0, normalize=True):
    """Shift pitch by `semitones` (keeps the speed), optional tempo change, clean up and normalise loudness.
    Negative semitones = deeper / older voice, positive = higher / younger voice."""
    f = 2 ** (semitones / 12.0)
    chain = ["highpass=f=70", "aresample=44100"]            # edge-tts gives 24 kHz: bring it to 44.1 kHz first
    if abs(semitones) > 0.01:
        chain += [f"asetrate={int(44100 * f)}", "aresample=44100", f"atempo={1.0 / f:.5f}"]
    if abs(tempo - 1.0) > 0.005:
        chain.append(f"atempo={tempo:.4f}")
    if POLISH:
        chain += ["equalizer=f=180:t=q:w=1:g=1.5",           # warmth
                  "equalizer=f=3200:t=q:w=1:g=2.0",          # clarity / presence
                  "acompressor=threshold=0.125:ratio=3:attack=5:release=90:makeup=1.5"]   # even out loud and quiet words
        if ROOM_ECHO > 0:
            chain.append(f"aecho=0.85:0.9:38:{ROOM_ECHO:.2f}")
    if normalize:
        chain.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", ",".join(chain), "-ar", "44100",
                    "-ac", "1", "-b:a", "128k", str(dst)], check=True)


# ------------------------------------------------------------------ real voices
EMOTION_VOICE = {            # (rate %, pitch Hz) added on top of the character's own voice settings
    "neutral": (0, 0), "happy": (4, 4), "confident": (2, 2), "angry": (6, -3), "scared": (8, 6), "nervous": (8, 6),
    "surprised": (6, 8), "sad": (-8, -4), "thinking": (-6, 0), "scheming": (-4, -2), "smirk": (-2, 0),
}


def tts_settings(voice, emotion):
    dr, dp = EMOTION_VOICE.get(emotion, (0, 0))
    rate = int(voice.get("rate", 0)) + dr
    pitch = int(voice.get("pitch", 0)) + dp
    return f"{rate:+d}%", f"{pitch:+d}Hz"


async def edge_provider(text, voice, emotion, out_path):
    """Default voice service: Microsoft Edge neural voices (free, needs internet)."""
    import edge_tts
    rate, pitch = tts_settings(voice, emotion)
    await edge_tts.Communicate(text, voice["name"], rate=rate, pitch=pitch).save(str(out_path))


async def tts_all(story, audio_dir, provider=None, retries=3, fx=True):
    """Make a voice file for every line that does not have one yet. Use `await` in Jupyter.

    provider: an async function (text, voice_dict, emotion, out_path) that writes an audio file.
              Default = edge_provider. Plug in any other service here (see README, "Better voices").
    """
    provider = provider or edge_provider
    audio_dir = Path(audio_dir)
    raw_dir = audio_dir / "_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    made = 0
    for lid, b in say_beats(story):
        if find_audio(audio_dir, lid):
            print(f"  have   {lid}")
            continue
        voice = story["characters"][b["who"]].get("voice", {"name": "bn-BD-PradeepNeural"})
        raw = raw_dir / f"{lid}.mp3"
        for attempt in range(retries):
            try:
                await provider(b["text"], dict(voice, who=b["who"]), b.get("emotion", "neutral"), raw)
                if not raw.exists() or raw.stat().st_size < 1000:
                    raise RuntimeError("TTS provider returned an empty or incomplete audio file.")
                break
            except Exception as e:
                print(f"  retry {lid}: {e}")
                await asyncio.sleep(2)
        else:
            raise RuntimeError(f"Could not create the voice for {lid}. Check your internet connection and try again.")
        final = audio_dir / f"{lid}.mp3"
        if fx:
            voice_fx(raw, final, float(voice.get("fx", 0)), float(voice.get("tempo", 1.0)))
        else:
            final.write_bytes(raw.read_bytes())
        made += 1
        print(f"  made   {lid}  {b['who']:8s} {voice.get('name', '')}  fx {float(voice.get('fx', 0)):+.0f}")
    print(f"\nDone. {made} new voice file(s).")


# ------------------------------------------------------------------ mixing
def mix_track(
    events,
    total_sec,
    root,
    sr=44100,
    music_path=None,
    music_gain=0.10,
    duck_gain=0.28,
    intro_path=None,
    intro_gain=0.85,
    intro_len=None,
):
    """Mix dialogue and optional background music safely.

    Dialogue is placed at its scheduled start time. Background music is kept
    quieter while someone is speaking (automatic ducking), then brought back
    during pauses. Events outside the output duration are safely clipped.
    """
    total_samples = max(0, int(round(float(total_sec) * sr)))
    out = np.zeros(total_samples, dtype=np.float32)

    # Mix dialogue first. Each event is clipped to the output boundaries so
    # an unusually long line or invalid timestamp cannot cause a shape error.
    for t0, path in events:
        samples = decode(path, sr)
        start_sample = int(round(float(t0) * sr))
        source_start = max(0, -start_sample)
        dest_start = max(0, start_sample)
        if dest_start >= total_samples or source_start >= len(samples):
            continue
        count = min(len(samples) - source_start, total_samples - dest_start)
        if count > 0:
            out[dest_start:dest_start + count] += samples[source_start:source_start + count]

    # Keep dialogue headroom before adding music.
    dialogue_peak = float(np.max(np.abs(out))) if out.size else 0.0
    if dialogue_peak > 0.0:
        out *= min(1.0, 0.78 / dialogue_peak)

    if music_path and Path(music_path).is_file() and total_samples:
        music = decode(music_path, sr)
        if music.size:
            repeats = (total_samples + len(music) - 1) // len(music)
            music = np.tile(music, repeats)[:total_samples]

            # Detect speech activity using a smoothed short-window RMS.
            window = max(1, int(sr * 0.08))
            kernel = np.ones(window, dtype=np.float32) / window
            level = np.sqrt(np.convolve(out * out, kernel, mode="same") + 1e-10)
            activity = np.clip((level - 0.008) / 0.055, 0.0, 1.0)

            # Smooth the ducking envelope to avoid audible pumping.
            smooth_n = max(1, int(sr * 0.18))
            smooth_kernel = np.ones(smooth_n, dtype=np.float32) / smooth_n
            activity = np.convolve(activity, smooth_kernel, mode="same")
            music_level = music_gain * (1.0 - activity * (1.0 - duck_gain))

            # Short fade-in/out prevents clicks at the beginning and end.
            fade_n = min(int(sr * 1.0), total_samples // 2)
            fade = np.ones(total_samples, dtype=np.float32)
            if fade_n > 0:
                ramp = np.linspace(0.0, 1.0, fade_n, dtype=np.float32)
                fade[:fade_n] = ramp
                fade[-fade_n:] = ramp[::-1]

            out += music * music_level * fade

    # Opening jingle: plays from 0:00 over the title card. It is much louder than the quiet background music,
    # and also gets quieter if somebody starts to speak while it is still playing.
    if intro_path and Path(intro_path).is_file() and total_samples:
        jingle = decode(intro_path, sr)
        n = min(len(jingle), total_samples)
        if intro_len:                                   # the jingle ends (fades) when the title card ends
            n = min(n, int(float(intro_len) * sr) + int(sr * 0.3))
        if n > 0:
            level = np.sqrt(np.convolve(out * out, np.ones(int(sr * 0.08), dtype=np.float32) / int(sr * 0.08), mode="same") + 1e-10)
            activity = np.clip((level - 0.008) / 0.055, 0.0, 1.0)[:n]
            gain = intro_gain * (1.0 - activity * 0.75)
            tail = np.ones(n, dtype=np.float32)
            k = min(n, int(sr * 0.6))
            tail[-k:] = np.linspace(1.0, 0.0, k, dtype=np.float32)
            out[:n] += jingle[:n] * gain * tail

    # Final peak limiter with a little headroom for AAC encoding.
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    if peak > 0.95:
        out *= 0.95 / peak

    return out, sr


def write_wav(path, samples, sr):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((np.clip(samples, -1, 1) * 32000).astype(np.int16).tobytes())
