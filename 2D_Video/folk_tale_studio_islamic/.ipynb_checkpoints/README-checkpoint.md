# Folk-tale cartoon studio · JupyterLab

> **NEW: Islamic-content videos (1-2 minutes)** - hujur, ma, baba, child, girl and student, with mosque / home / classroom scenes,
> on-screen **hadith cards** and **tip cards**, calm green-and-gold title card, no dancing and no music by default.
> Start here: `stories/islamic/1_sotto_kotha.txt` (6 ready stories + `0_template.txt`), then read the last section of `SYNTAX.md`.
> Preview pictures: `islamic_cast_preview.png`, `islamic_backgrounds_preview.png`.
>
> | story | topic | hadith on the card |
> |---|---|---|
> | `1_sotto_kotha` | honesty (child breaks a glass) | Bukhari 6094, Muslim 2607 |
> | `2_maayer_hok` | honouring your mother (student and his phone) | Bukhari 5971, Muslim 2548 |
> | `3_khawar_adab` | eating manners | Bukhari 5376, Muslim 2022 |
> | `4_rag_somlano` | controlling anger (baba) | Bukhari 6114, Muslim 2609 |
> | `5_bhalo_kotha` | good speech, no backbiting (students) | Bukhari 6018, Muslim 47 |
> | `6_quran_shekha` | learning the Quran, never give up | Bukhari 5027, Bukhari 4937 / Muslim 798 |
>
> Make one: copy `stories/islamic/0_template.txt`, write your story, set `STORY = "stories/islamic/my_story.txt"` in `MAKE_VIDEO.ipynb`, Run All.
> Please have the hadith wording and numbering checked by a trusted alim before you publish.

Write a story as plain text → run one notebook → get a 2D cut-out cartoon video (Chikna Bhar folk tales with Raja Krishnachandra, the Mantri and a royal rajshobha court,
Bangla captions, lip sync, walking, gestures, camera moves). Runs on a normal laptop, **no GPU**.

```
stories/1_golden_mango.txt       চিকনা ভাঁড় ও সোনালি আম   - the stolen golden mango, the magic pot
stories/2_smell_of_sweets.txt    গন্ধের দাম               - the price of a smell (market + court)
stories/3_straw_on_the_thief.txt চোরের মাথায় খড়          - the straw on the thief's head
stories/4_feast_for_the_coat.txt জামার ভোজ               - a feast for the coat (two versions of Chandu)
stories/5_counting_the_crows.txt কাকের হিসাব              - how many crows are in the city?
stories/6_ginni_and_the_sweets.txt গিন্নির রাগ ও মিষ্টির হাঁড়ি - Chikna and his wife Ginni at home (new)
stories/7_electricity_bill.txt   বিদ্যুৎ বিলের ঝামেলা     - Ginni and Chikna argue about the bill (new, ~50 s)
stories/8_hilsa_in_the_market.txt বাজারে ইলিশ             - Chikna "asks the fish" its price (new, ~55 s)
stories/9_dream_money.txt        স্বপ্নের মোহর             - 100 gold coins... in a dream (new, ~45 s)
stories/10_stars_and_the_turban.txt আকাশের তারা          - how many stars? count the Mantri's turban (new, ~50 s)
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

## The cast (Chikna Bhar series style)
| id (suggested) | look | who |
|---|---|---|
| `chikna` | `chikna` | **Chikna Bhar** (TV-cartoon look) - very round and plump, bald with dark hair only above the ears, no moustache, big round pink nose, yellow kurta, orange-red dhoti, red gamchha (scarf) round the neck, black shoes |
| `raja` | `krishnachandra` | **Raja Krishnachandra** - royal pagri with jewel and plume, maroon-and-gold coat, pearls |
| `ginni` | `ginni` | **Ginni** (Chikna's wife) - plump and round-faced, hair parted and pulled back in a small bun, red bindi, blue saree with yellow blouse, red bangles, bare feet |
| `mantri` | `mantri` | **Mantri** - tall violet pagri, white moustache and pointed beard, the one who always schemes against Chikna |

Backgrounds: `rajshobha` (royal court: canopied throne on a dais, seated courtiers, chandeliers, marigold garlands, gold frame)
and `rajshobha_evening`. The older `court` / `court_evening` are still there.
All drawings are original (inspired by the folk tradition, not copied from any TV series artwork).

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

## Opening music and the dancing title card (new)
Every video now starts with a bouncy Bengali-folk jingle (dhak drum roll, kansi cymbal, bamboo flute, ektara, tabla and ghungur bells) while
**Chikna and Ginni dance** on the title card in time with the beat. At the end card they wave goodbye.
* The jingle is **original** (made by `engine/intro.py`, saved as `music/intro.wav` the first time you render). It does not copy any existing song.
* **Use your own tune instead:** save any audio file as `music/intro.wav` (or `.mp3`). It is used automatically.
* **Change the tune or the speed:** edit `MELODY` in `engine/intro.py`, or `intro.make_intro("music/intro.wav", bpm=120)`, then render again.
* **Title length:** the third part of the `TITLE:` line is the seconds (7.5 fits the jingle).
* **Turn the dancers off:** `Studio(".", STORY, party=False)`.

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
