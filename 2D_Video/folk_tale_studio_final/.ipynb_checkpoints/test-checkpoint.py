
import sys
import traceback
from pathlib import Path

print("=" * 60)
print("FOLK TALE STUDIO - BANGLA SHAPING DIAGNOSTICS")
print("=" * 60)

# --------------------------------------------------
# 1. Python environment
# --------------------------------------------------

print("\n[1] Python Environment")
print("Python:", sys.version)
print("Executable:", sys.executable)

# --------------------------------------------------
# 2. Dependency tests
# --------------------------------------------------

print("\n[2] Dependency Tests")

try:
    import PIL
    print("Pillow:", PIL.__version__)
except Exception as e:
    print("Pillow ERROR:", repr(e))

try:
    import uharfbuzz as hb
    print("uharfbuzz:", hb.__version__)
except Exception as e:
    print("uharfbuzz ERROR:", repr(e))

try:
    import fontTools
    from fontTools.pens.basePen import BasePen
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.ttLib import TTFont

    print("fontTools:", fontTools.__version__)
    print("BasePen: OK")
    print("SVGPathPen: OK")
    print("TTFont: OK")

except Exception as e:
    print("fontTools ERROR:", repr(e))
    traceback.print_exc()
    sys.exit(1)

# --------------------------------------------------
# 3. Find Bengali fonts
# --------------------------------------------------

print("\n[3] Searching for Bengali fonts")

project = Path(__file__).resolve().parent

font_files = list(project.rglob("*.ttf")) + list(project.rglob("*.otf"))

font_files = [
    f for f in font_files
    if any(word in f.name.lower() for word in
           ("bengali", "bangla", "noto", "kalpurush", "solaiman"))
]

for font in font_files:
    print("FOUND:", font)

if not font_files:
    print("No matching fonts found.")
    print("Please provide a Bengali .ttf or .otf font path.")
    sys.exit(1)

# --------------------------------------------------
# 4. Import custom shaping module
# --------------------------------------------------

print("\n[4] Importing engine.shaping")

try:
    from engine.shaping import HBText, AVAILABLE

    print("Shaping module imported successfully")
    print("AVAILABLE:", AVAILABLE)

except Exception as e:
    print("SHAPING MODULE ERROR:", repr(e))
    traceback.print_exc()
    sys.exit(1)

if not AVAILABLE:
    print("Shaping dependencies are unavailable.")
    sys.exit(1)

# --------------------------------------------------
# 5. Test Bengali font and HarfBuzz
# --------------------------------------------------

font_path = font_files[0]

print("\n[5] Loading Bengali font")
print("Font:", font_path)

try:
    font = HBText(font_path, 48)
    print("Font loaded successfully")
except Exception as e:
    print("FONT ERROR:", repr(e))
    traceback.print_exc()
    sys.exit(1)

# --------------------------------------------------
# 6. Bengali text shaping
# --------------------------------------------------

print("\n[6] Bengali Shaping Tests")

samples = [
    "বাংলাদেশ",
    "আমার সোনার বাংলা",
    "শিক্ষা",
    "প্রযুক্তি",
    "ক্ষ",
    "ক্ত",
    "ক্রিকেট",
    "বাংলা ভাষা",
]

for text in samples:
    try:
        width = font.length(text)
        mask, baseline = font.mask(text)

        print(
            f"PASS: {text} | "
            f"Width: {width:.2f} | "
            f"Mask: {mask.size} | "
            f"Baseline: {baseline}"
        )

    except Exception as e:
        print(f"FAIL: {text} | {repr(e)}")
        traceback.print_exc()

# --------------------------------------------------
# 7. Generate Bengali preview image
# --------------------------------------------------

print("\n[7] Generating Bengali preview")

from PIL import Image, ImageDraw

try:
    width, height = 1000, 600

    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)

    y = 30

    for text in samples:
        mask, baseline = font.mask(text)

        x = 40

        canvas.paste(
            (20, 20, 20),
            (x, y, x + mask.width, y + mask.height),
            mask
        )

        y += mask.height + 15

    output = project / "bangla_shaping_preview.png"
    canvas.save(output)

    print("SUCCESS:", output)

except Exception as e:
    print("IMAGE ERROR:", repr(e))
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSTIC FINISHED")
print("=" * 60)
