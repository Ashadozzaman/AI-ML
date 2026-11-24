"""
intro.py - an original, bouncy Bengali-folk style opening jingle, made from scratch with numpy (no samples, no downloads).

    from engine import intro
    intro.make_intro("music/intro.wav")                 # default: 132 bpm, ~7.3 seconds
    intro.make_intro("music/intro.wav", bpm=120)        # slower

Instruments: dhak (big drum roll) + kansi (cymbal) + tabla taps + bamboo flute melody + ektara plucks + ghungur bells.
The melody is original (D major pentatonic). To change it, edit MELODY below: (start_beat, note, length_in_beats).

Want a different tune? Save any audio file as  music/intro.wav  (or .mp3) - it is used instead of this one.
"""
import wave
import numpy as np

SR = 44100

NOTES = {"D3": 146.83, "A3": 220.00, "D4": 293.66, "E4": 329.63, "F#4": 369.99, "A4": 440.00, "B4": 493.88,
         "D5": 587.33, "E5": 659.25, "F#5": 739.99, "A5": 880.00}

# (start beat, note, length in beats)   - 4 beats of drum roll first, then three short phrases
MELODY = [
    (4.0, "A4", 0.5), (4.5, "B4", 0.5), (5.0, "D5", 1.0), (6.0, "B4", 0.5), (6.5, "A4", 0.5), (7.0, "F#4", 1.0),
    (8.0, "A4", 0.5), (8.5, "B4", 0.5), (9.0, "D5", 0.5), (9.5, "E5", 0.5), (10.0, "F#5", 1.0), (11.0, "E5", 0.5),
    (11.5, "D5", 0.5),
    (12.0, "D5", 0.5), (12.5, "B4", 0.5), (13.0, "A4", 0.5), (13.5, "B4", 0.5), (14.0, "D5", 1.0), (15.0, "A5", 1.2),
]
TOTAL_BEATS = 16.0


def _env(n, attack, release, sr=SR):
    e = np.ones(n, dtype=np.float32)
    a, r = min(n, int(attack * sr)), min(n, int(release * sr))
    if a:
        e[:a] = np.linspace(0, 1, a, dtype=np.float32)
    if r:
        e[-r:] *= np.linspace(1, 0, r, dtype=np.float32)
    return e


def _hp(x):                                        # crude high-pass (keeps the "hissy" part of noise)
    return np.concatenate(([0.0], np.diff(x))).astype(np.float32)


def _add(out, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(out) or i < 0:
        return
    n = min(len(sig), len(out) - i)
    out[i:i + n] += sig[:n] * gain


def flute(freq, dur, rng):
    n = int((dur + 0.10) * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.6 * t) * np.clip((t - 0.12) / 0.2, 0, 1)
    ph = 2 * np.pi * np.cumsum(freq * vib) / SR
    s = np.sin(ph) + 0.32 * np.sin(2 * ph) + 0.10 * np.sin(3 * ph)
    s += 0.012 * _hp(rng.standard_normal(n).astype(np.float32))          # breath
    return (s * _env(n, 0.035, 0.10)).astype(np.float32) * 0.5


def pluck(freq, dur=0.9):                          # Karplus-Strong string (ektara / drone)
    n = int(dur * SR)
    period = max(2, int(SR / freq))
    buf = np.random.default_rng(int(freq)).uniform(-1, 1, period).astype(np.float32)
    out = np.zeros(n, dtype=np.float32)
    for i in range(n):
        out[i] = buf[i % period]
        buf[i % period] = 0.5 * (buf[i % period] + buf[(i + 1) % period]) * 0.9965
    return out * 0.6


def drum(f0, f1, dur, click=0.3, rng=None):         # dhak / dhol hit: pitch drops quickly
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (5.5 / dur))
    if rng is not None:
        s += 0.5 * click * rng.standard_normal(n).astype(np.float32) * np.exp(-t * 90)
    return s.astype(np.float32)


def tabla(freq, dur=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2.3 * t)) * np.exp(-t * 30)
    return s.astype(np.float32) * 0.6


def kansi(dur, rng):                                # bell-metal cymbal
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = 0.25 * _hp(rng.standard_normal(n).astype(np.float32)) * np.exp(-t * 4.5)
    for fr in (1180, 1670, 2450, 3330):
        s += 0.22 * np.sin(2 * np.pi * fr * t) * np.exp(-t * 5)
    return s.astype(np.float32) * 0.5


def bell(freq, dur=0.35):                           # ghungur sparkle
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2.76 * t)).astype(np.float32) * np.exp(-t * 14) * 0.3


def _reverb(x):
    out = x.copy()
    for d, g in ((0.043, 0.30), (0.071, 0.22), (0.109, 0.16), (0.163, 0.10)):
        k = int(d * SR)
        out[k:] += x[:-k] * g
    return out


def make_intro(path="music/intro.wav", bpm=132, seed=7):
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    total = TOTAL_BEATS * beat + 0.6
    out = np.zeros(int(total * SR), dtype=np.float32)

    # --- opening: kansi crash + dhak roll that speeds up (beats 0-4)
    _add(out, kansi(1.4, rng), 0.0, 0.9)
    roll = [0, 1, 2, 2.5, 3, 3.25, 3.5, 3.75]
    for k, b in enumerate(roll):
        amp = 0.55 + 0.45 * k / len(roll)
        _add(out, drum(190, 95, 0.22, rng=rng), b * beat, amp)
        if b >= 2:
            _add(out, tabla(520), (b + 0.12) * beat, 0.4 * amp)

    # --- groove (beats 4-15): dhak on 1 & 3, tabla taps, shaker eighths, ektara drone
    for b in np.arange(4, TOTAL_BEATS - 0.5, 0.5):
        whole = abs(b - round(b)) < 1e-6
        i = int(round(b))
        t0 = b * beat
        _add(out, _hp(rng.standard_normal(int(0.05 * SR)).astype(np.float32)) * np.linspace(1, 0, int(0.05 * SR)).astype(np.float32),
             t0, 0.10 if whole else 0.06)                               # ghungroo shaker
        if whole and i % 2 == 0:
            _add(out, drum(150, 70, 0.30, rng=rng), t0, 0.85)            # dhak "dha"
        if whole and i % 2 == 1:
            _add(out, tabla(540), t0, 0.7)                               # tabla "tin"
        if not whole and int(b * 2) % 4 == 3:
            _add(out, tabla(410), t0, 0.5)                               # tabla "na" pick-up
        if whole:
            _add(out, pluck(NOTES["D3"] if i % 4 in (0, 1) else NOTES["A3"]), t0, 0.5)   # ektara
    _add(out, kansi(1.0, rng), 8 * beat, 0.45)                           # accent at the second phrase
    _add(out, kansi(1.8, rng), 15 * beat, 0.85)                          # final crash
    _add(out, drum(150, 60, 0.5, rng=rng), 15 * beat, 1.0)

    # --- bamboo flute melody (+ little ghungur sparkle on the long notes)
    for start, note, ln in MELODY:
        _add(out, flute(NOTES[note], ln * beat, rng), start * beat, 0.9)
        if ln >= 1.0:
            _add(out, bell(2900), start * beat, 0.5)

    out = _reverb(out)
    peak = float(np.max(np.abs(out))) or 1.0
    out = out * (0.9 / peak)
    out *= _env(len(out), 0.0, 0.8)                                       # soft end
    if path:
        write_wav(path, out)
    return out


def write_wav(path, samples):
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((np.clip(samples, -1, 1) * 32000).astype(np.int16).tobytes())
    return path


if __name__ == "__main__":
    make_intro()
    print("saved music/intro.wav")
