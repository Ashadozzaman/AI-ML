"""Gopal-style 2D cut-out animation engine for JupyterLab (Pillow + numpy + ffmpeg)."""
import shutil
import subprocess


def check_setup(verbose=True):
    """Prints what works and what is missing on this computer."""
    from pathlib import Path
    ok = True
    rows = []

    ff = shutil.which("ffmpeg")
    rows.append(("ffmpeg installed", bool(ff), "Install ffmpeg: https://ffmpeg.org/download.html (add it to PATH)"))
    ok &= bool(ff)

    try:
        from PIL import features, __version__ as pv
        from .text import shaping_mode
        mode = shaping_mode()
        rows.append((f"Pillow {pv}", True, ""))
        label = {"raqm": "Bangla text shaping (Pillow raqm)", "harfbuzz": "Bangla text shaping (uharfbuzz - built-in fix)",
                 "broken": "Bangla text shaping"}[mode]
        rows.append((label, mode != "broken", "Bangla letters will look broken. Run:  pip install uharfbuzz  then restart the kernel"))
    except Exception as e:
        rows.append(("Pillow", False, f"pip install pillow ({e})"))
        ok = False

    for mod, tip in (("numpy", "pip install numpy"), ("fontTools", "pip install fonttools"),
                     ("edge_tts", "pip install edge-tts   (only needed for real voices)")):
        try:
            __import__(mod)
            rows.append((mod, True, ""))
        except ImportError:
            rows.append((mod, False, tip))
            ok &= mod == "edge_tts"

    font = Path("fonts/NotoSansBengali-Bold.ttf").exists()
    rows.append(("fonts/NotoSansBengali-Bold.ttf", font, "Run this notebook from the project folder"))
    ok &= font

    if verbose:
        for name, good, tip in rows:
            print(("  OK   " if good else "  !!   ") + name + ("" if good else f"   -> {tip}"))
        print("\nReady to go." if ok else "\nFix the lines marked !! first.")
    return ok
