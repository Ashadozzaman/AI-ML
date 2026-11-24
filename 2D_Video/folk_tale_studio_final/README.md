# Folk-tale cartoon studio · JupyterLab

Write a story as plain text → run one notebook → get a 2D cut-out cartoon video (Gopal-Bhar-style folk tales,
Bangla captions, lip sync, walking, gestures, camera moves). Runs on a normal laptop, **no GPU**.

```
stories/1_golden_mango.txt       চতুর চাঁদু ও সোনালি আম   - the stolen golden mango, the magic pot
stories/2_smell_of_sweets.txt    গন্ধের দাম               - the price of a smell (market + court)
stories/3_straw_on_the_thief.txt চোরের মাথায় খড়          - the straw on the thief's head
stories/4_feast_for_the_coat.txt জামার ভোজ               - a feast for the coat (two versions of Chandu)
stories/5_counting_the_crows.txt কাকের হিসাব              - how many crows are in the city?
MAKE_VIDEO.ipynb                 <- the only notebook you need: pick a story, Run All
characters.ipynb                 preview / change how characters look
SYNTAX.md                        how to write a story (one page)
```

## Install (once)
```bash
# ffmpeg must be on PATH    (Ubuntu: sudo apt install ffmpeg | macOS: brew install ffmpeg | Windows: https://ffmpeg.org)
pip install -r requirements.txt
jupyter lab        # run inside this folder
```

## Make a new video
1. Copy `stories/1_golden_mango.txt` to `stories/my_story.txt` and write your story (see `SYNTAX.md`).
2. Open `MAKE_VIDEO.ipynb`, set `STORY = "stories/my_story.txt"`, **Run → Run All Cells**.
3. The video is saved in `output/my_story.mp4`.

If something in the story file is wrong, the notebook tells you the line number and what to fix.

## About the voices (important)
* Real voices are made by **edge-tts** (free Microsoft neural voices) when you run the *Voices* cell. This needs internet.
* The *humming* sound some previews use is **only a placeholder** for testing timing. It is never used unless you set
  `USE_DRAFT_VOICE_IF_OFFLINE = True`.
* Only lines you changed get a new voice; all other lines are reused. (Voice files are named `line_03_ab12cd.mp3`.)

**Make the characters sound different and better**
| tool | how |
|---|---|
| speed / pitch | `rate=-10` (slower) and `pitch=-8` in the character's `CHARACTERS:` line |
| voice effect | `fx=-3` makes a voice deeper/older, `fx=+3` higher/younger (works on any voice, changes no speed) |
| different voices | `voice=bn-BD-PradeepNeural`, `bn-IN-BashkarNeural` (male), `bn-BD-NabanitaNeural`, `bn-IN-TanishaaNeural` (female) |
| emotion | `(angry)`, `(scared)`, `(happy)`... in a dialogue line change speed and pitch a little |
| **your own voice** | record a line on your phone, save it as `audio/line_03.mp3` (number of the line). It is used instead of the generated voice. Best quality of all. |
| another voice service | `await audio.tts_all(story, "audio", provider=my_provider)` where `my_provider` is an async function `(text, voice, emotion, out_path)` that saves an audio file using your service (ElevenLabs, Google, Azure...). Check that service's documentation for Bangla support. |

## Background music
Put any music file at `music/music.mp3`. It is mixed in at low volume, **ducks automatically** (gets quieter while a character speaks and
returns in the pauses), fades in and out, and the final mix is peak-limited to avoid clipping.

## How it works
`engine/script.py` reads your story → `timeline.py` plans every moment → `anim.py` poses the puppets
(breathing, walking, gestures, emotions) → `rig.py` draws paper-cut-out characters (parts rotated around joints, made by `art.py`) →
`audio.py` makes voices and turns loudness into mouth shapes → `render.py` adds camera, captions and sends frames to ffmpeg.

## Troubleshooting
* **Bangla letters look broken** (dotted circles, vowel signs ি ে ো in the wrong place): Pillow's text engine *raqm* is missing on your computer.
  Fix: `pip install uharfbuzz`, then **restart the Jupyter kernel**. The project then uses its own built-in shaper (`engine/shaping.py`) and needs no system libraries.
  (Alternative: install the system libraries - Linux `sudo apt install libraqm0 libfribidi0`, macOS `brew install fribidi` - and reinstall Pillow.)
  `MAKE_VIDEO.ipynb` > "Check this computer" tells you which engine is used.
* **Boxes instead of commas in captions:** add a font path to `LATIN_FONT_CANDIDATES` in `engine/text.py`.
* **"No voice file for line_..":** run the Voices cell (needs internet) or record the line yourself.
* **Video too long/short:** the notebook prints the length before rendering. Add or remove lines or `> wait` pauses.

Credits: Noto Sans Bengali font (SIL Open Font License). Characters, backgrounds and both stories are original.
