"""
intro_islamic.py - a short, calm, original instrumental opening tune (about 3 seconds), made from scratch with numpy.
No drums, no voices: a soft pad, a ney-like (reed flute) melody in the Hijaz scale (D Eb F# G A Bb C D), and a gentle string pluck.

    from engine import intro_islamic
    intro_islamic.make_islamic_intro("music/islamic_intro.wav")

Want a different tune (or none)?  Put your own file at  music/islamic_intro.wav / .mp3  - it is used instead of this one.
To switch the opening tune off:  studio.render(..., intro="none")
"""
import numpy as np

from .intro import SR, _add, _env, _hp, _reverb, bell, pluck, write_wav

HZ = {"D3": 146.83, "A3": 220.00, "D4": 293.66, "Eb4": 311.13, "F#4": 369.99, "G4": 392.00, "A4": 440.00, "Bb4": 466.16, "D5": 587.33}

# (start second, note, length in seconds): a short falling Hijaz phrase that settles on D
MELODY = [(0.15, "A4", 0.34), (0.50, "Bb4", 0.30), (0.82, "A4", 0.30), (1.12, "G4", 0.32),
          (1.44, "F#4", 0.36), (1.80, "Eb4", 0.32), (2.12, "D4", 0.95)]
TOTAL = 3.1


def ney(freq, dur, rng):
    """Reed-flute like note: soft attack, slow vibrato, a little breath."""
    n = int((dur + 0.12) * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.10) / 0.18, 0, 1)
    ph = 2 * np.pi * np.cumsum(freq * vib) / SR
    s = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    s += 0.030 * _hp(rng.standard_normal(n).astype(np.float32))
    return (s * _env(n, 0.05, 0.14)).astype(np.float32) * 0.55


def pad(freqs, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n, dtype=np.float32)
    for f in freqs:
        for det in (-0.6, 0.0, 0.6):
            s += np.sin(2 * np.pi * (f + det) * t).astype(np.float32)
    return s / (3 * len(freqs)) * _env(n, 0.9, 0.7)


def make_islamic_intro(path="music/islamic_intro.wav", seed=11):
    rng = np.random.default_rng(seed)
    out = np.zeros(int(TOTAL * SR), dtype=np.float32)
    _add(out, pad([HZ["D3"], HZ["A3"], HZ["D4"]], TOTAL), 0.0, 0.55)             # warm drone
    _add(out, pluck(HZ["D3"], 1.6), 0.0, 0.55)                                    # string pluck on D
    _add(out, pluck(HZ["A3"], 1.2), 1.05, 0.40)
    _add(out, bell(2600, 0.9), 0.05, 0.35)                                        # soft chime at the very start
    for start, note, ln in MELODY:
        _add(out, ney(HZ[note], ln, rng), start, 0.95)
    _add(out, bell(1950, 1.0), 2.12, 0.30)                                        # chime when the phrase lands on D
    out = _reverb(_reverb(out))
    out = out * (0.9 / (float(np.max(np.abs(out))) or 1.0))
    out *= _env(len(out), 0.0, 0.6)
    if path:
        write_wav(path, out)
    return out


if __name__ == "__main__":
    make_islamic_intro()
