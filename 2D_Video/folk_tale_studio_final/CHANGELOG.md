# Changelog

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
