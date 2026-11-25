# Changelog

## Islamic content update
- **Voices are more robust**: `audio.tts_all` retries 5 times with waiting, the last try uses plain speed/pitch, one failed line no longer stops the others, and the error message tells you what to do. Just run the Voices cell again.
- **Opening tune + faster start**: every Islamic video now begins with a short calm instrumental tune (`engine/intro_islamic.py`, file `music/islamic_intro.wav`) that fades out when the voice starts.
  The title card is shorter (2.6 s instead of 4 s). Switch the tune off with `render(..., intro="none")`.
- **New story theme**: `THEME: islamic` (first lines of a story). Calm green-and-gold title card with Bismillah, no dancing Chikna/Ginni, no folk jingle,
  no background music unless you add `music/islamic_intro.*` / `music/islamic_music.mp3`. Folk stories are unchanged (`Studio(party=None)` = automatic).
- **New characters** (`engine/art.py`): `hujur`, `baba`, `ma`, `child`, `girl`, `student`. New drawing options: hats `amama`, `hijab`; beards `full`, `short`;
  styles `panjabi`, `gown`, `shirt`. Only ordinary people are drawn.
- **New backgrounds and props** (`engine/art_islamic.py`): `masjid`, `masjid_evening`, `masjid_yard`, `masjid_yard_evening`, `home`, `home_evening`, `classroom`;
  props `dastarkhan`, `glass_pieces`, `rehal`. Files are in `assets/` and rebuilt automatically if missing.
- **New commands**: `> hadith "text" "source"` / `> hadith off` and `> tip "text"` / `> tip off` (cards that stay on screen while people talk).
- **6 new stories** in `stories/islamic/` + `0_template.txt`. New default voices for the new looks.
- **Stories 7-16** added, including a 5-minute story (`16_ramadan_ek_din`).
- **Voices**: removed the stacked pitch changes from the Islamic stories (they made voices robotic); new voice polish (`audio.POLISH`, `audio.ROOM_ECHO`);
  new `engine/voices_pro.py` for ElevenLabs / Google voices; providers now receive the character id (`voice["who"]`).
- `MAKE_VIDEO.ipynb` now starts with `stories/islamic/1_sotto_kotha.txt`.

## Chikna rename + 4 short stories
- The lead character is now **Chikna Bhar** (চিকনা ভাঁড়), look name `chikna` (the old name `gopal` still works). All stories, titles and docs updated.
  Every line that said "গোপাল" now says "চিকনা", so those lines need new voice files: run the Voices cell once (internet needed).
- New short stories 7-10 (45-55 s each): electricity bill, hilsa in the market, money from a dream, stars and the turban.
- The opening jingle now ends when the title card ends, so short stories can use a short title (`TITLE: ... | 4.5`).

## Ginni + opening music update
- **Chikna and Ginni redrawn to match the reference pictures**: Chikna is now round and plump, bald, no moustache or tilak, yellow kurta + orange dhoti + red gamchha, black shoes (`style=kurta_dhoti`, `hat=bald`). Ginni has a blue saree, yellow blouse, red bangles and no sindoor/earrings/nose ring (still available: `sindoor=true earrings=true nath=true flowers=true`). New option `shoulder=` sets where the arms attach on wide bodies.
- **New character `ginni`** (Chikna's wife). New code in `engine/art.py` (`draw_torso_saree`, hat `bun`, options `bindi`, `sindoor`, `earrings`, `nath`,
  `style=saree`, colour `blouse`). Default voice `bn-BD-NabanitaNeural`.
- **New story** `stories/6_ginni_and_the_sweets.txt` (8 lines of speech). Needs the Voices cell once (internet).
- **Opening jingle**: `engine/intro.py` makes `music/intro.wav`; `audio.mix_track(..., intro_path=...)` mixes it at the start, quieter if speech begins.
- **Dancing title card**: Chikna and Ginni dance to the beat on the title card and wave on the end card (`Studio(party=True)`, `render.py`).
  Title text moved up to make room. `TITLE:` time in stories 1-5 changed from 3.6 to 7.5 seconds so the whole jingle plays.
- **Bug fix**: the cheek blush was see-through (the background showed through the cheeks of every character). Now blended properly.

## Chikna Bhar update
- New looks: `gopal` (bald with tuft + tilak, handlebar moustache, dhoti and shoulder cloth, bare feet), `krishnachandra`
  (royal pagri with jewel and plume) and `mantri` (tall violet pagri, white beard). New drawing code is in `engine/art.py`
  (`draw_torso_dhoti`, hats `tiki` / `pagri` / `pagri_tall`, beard `handlebar`, option `tilak=true`).
- New background `rajshobha` (+ `rajshobha_evening`): royal durbar with cusped arches, canopied throne on a dais,
  seated courtiers on both sides, chandeliers, marigold garlands and a gold frame. Built by `art.make_rajshobha()`.
- All five stories now use Chikna Bhar / Raja Krishnachandra / Mantri and the rajshobha court.
  Lines that contained the old name "চাঁদু" changed, so they need new voice files (run the Voices cell; unchanged lines keep their voice).

## Update (merged with your edits)
**Kept from your version**
- `engine/audio.py`: safer `mix_track` - background music that ducks under speech, fades in/out, peak limiter, clipped events;
  check that rejects empty/incomplete voice files.
- Your real voices for story 1 (`audio/line_*.mp3`).
- Your improved Voices cell in `MAKE_VIDEO.ipynb` (error traceback + AUDIO STATUS table + summary), now also honours
  `USE_DRAFT_VOICE_IF_OFFLINE` and stops cleanly if a voice is missing.

**New**
- Bangla fix: `engine/shaping.py` (uses `uharfbuzz`) - correct vowel signs and conjuncts even when Pillow has no raqm engine.
  `check_setup()` shows which engine is used.
- Three more stories: 3_straw_on_the_thief, 4_feast_for_the_coat, 5_counting_the_crows.
- Clean notebook: removed the duplicated / commented-out cells and the empty cell; the Pillow diagnostics are now part of "Check this computer".
- README: fixed a stray literal `\n`, added the Background music section; requirements now include `uharfbuzz`.
- Removed `.ipynb_checkpoints` and the temporary `audio/_raw` files (they are recreated when voices are made).
