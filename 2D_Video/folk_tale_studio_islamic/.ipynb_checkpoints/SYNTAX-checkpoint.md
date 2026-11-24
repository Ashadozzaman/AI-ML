# Story format cheat sheet

A story is a plain text file in `stories/`. Lines starting with `#` are notes.

## 1. Title and end card
```
TITLE: Story name | subtitle | seconds
END:   সমাপ্ত | subtitle | seconds
```

## 2. Characters (once, at the top)
```
CHARACTERS:
# id    | name on screen    | look           | voice settings and look changes
raja    | রাজা কৃষ্ণচন্দ্র | krishnachandra | voice=bn-IN-BashkarNeural rate=-10 pitch=-8 fx=-2
mantri  | মন্ত্রী           | mantri         | voice=bn-BD-PradeepNeural rate=-4 pitch=-4 fx=-3
gopal   | চিকনা ভাঁড়      | gopal          | voice=bn-BD-PradeepNeural rate=6 pitch=10 fx=3
```
* **look:** `chikna`, `ginni`, `krishnachandra`, `mantri` (the series cast) or `king`, `minister`, `jester` (then change colours, hats... - see `characters.ipynb`)
* **voice:** `voice=` (Ginni's default voice is `bn-BD-NabanitaNeural`. Bangla voices: `bn-BD-PradeepNeural`, `bn-IN-BashkarNeural`, `bn-BD-NabanitaNeural`, `bn-IN-TanishaaNeural`),
  `rate=` speed in % (negative = slower), `pitch=` in Hz, `fx=` voice effect in semitones
  (**negative = deeper/older, positive = higher/younger**, try -4 ... +4), `tempo=` extra speed change (1.0 = normal)

## 3. Scenes
```
SCENE rajshobha: raja@0.76:left gopal@0.40:right mantri@0.18
```
* backgrounds: `rajshobha`, `rajshobha_evening`, `garden`, `garden_empty`, `court`, `court_evening`, `market`
  (or your own `assets/bg_<name>.png`, 1280x720)
* `@0.72` = place across the screen (0 = left edge, 1 = right edge). `:left` / `:right` = which way they face.
* Everyone not listed is off stage. A new SCENE fades in.

## 4. Dialogue
```
raja (angry, point, to=gopal): Spoken text goes here. || mantri:nervous gopal:cheer
```
In the brackets (all optional, any order):
* **emotion:** `neutral happy confident angry scared nervous surprised sad thinking scheming smirk`
* **gesture:** `open chest raise point shrug fist palm wave show_hands salute`  (otherwise gestures are chosen automatically)
* `to=gopal` or `to=0.8` - who/where he talks or points to
* `hold` - keep the emotion after the line;  `pre=0.3` / `post=0.8` - pause before / after
* After `||`: reactions of other people while this line is spoken: `name:reaction` (reaction = an action or emotion, join with `+`)

## 5. Commands (lines starting with `>`)
| command | example |
|---|---|
| walk in / out / move | `> enter gopal from right to 0.6 happy 2` &nbsp; `> exit mantri to left 2` &nbsp; `> move raja to 0.4 1.5` |
| action without speech | `> act gopal bow 1.8 || raja:laugh` |
| pause | `> wait 0.8` |
| darkness (with text) / light | `> dark 0.93 0.9 "text on screen"` &nbsp; `> light 0.9` |
| props | `> prop pot at 0.54 scale 0.8` &nbsp; `> prop pot off` |
| comic sound word | `> popup "ঝনঝন!" 1.8` |
| instant change | `> set raja soot on` &nbsp; `> set mantri emotion sad` &nbsp; `> set raja face left` |
| camera | `> cam 1.15 0.5 1.0` (zoom, x, seconds) |

* **actions:** `salute bow shock laugh think cheer nervous point show_hands guilty stomp smirk wave touch cower`

## Tips
* One line of dialogue = about 4-8 seconds. For a 2 minute video write about 14-18 lines.
* Every person who speaks must be in the SCENE line (or `> enter` first).
* Changing a line's text only re-makes that one voice file.


---
# Islamic videos (1-2 minutes: hujur, ma, baba, child, student)

Put `THEME: islamic` at the top of the story file. That one line switches the video to a calm style:
green-and-gold title card with "বিসমিল্লাহির রাহমানির রাহীম", **no dancing**, **no folk jingle**, **no background music** (add your own if you want, see below).

```
THEME: islamic
TITLE: খাওয়ার সুন্দর আদব | ছোটদের জন্য ইসলামিক শিক্ষা | 4
CHARACTERS:
hujur | হুজুর | hujur | voice=bn-IN-BashkarNeural rate=-8 pitch=-6 fx=-2
SCENE home: hujur@0.3:right child@0.7:left
> hadith "হাদীসের ভাবার্থ" "সহীহ বুখারী ৫৩৭৬"      <- card at the top, stays until the next line below
hujur (happy, palm, to=child): ...
> hadith off
> tip "আজকের টিপস, এক লাইনে।"                        <- gold "আজকের টিপস" card
> tip off
```

## Looks (use in the 3rd column of CHARACTERS)
| look | who | notes |
|---|---|---|
| `hujur` | Hujur | white amama (turban), long white beard, white panjabi |
| `baba` | Father | white topi, short beard, blue panjabi |
| `ma` | Mother | plum head scarf, teal modest dress |
| `child` | Boy (small) | topi, green panjabi |
| `girl` | Girl (small) | rose head scarf, yellow dress |
| `student` | Older boy | school shirt. Madrasa look: `hat=topi style=panjabi coat=240,240,232` |

Change anything with `key=value` on the CHARACTERS line, for example `coat=214,110,70` (colour), `scale=0.5` (size), `beard=short`
(`none` / `short` / `full`), `hat=topi` (`none` / `topi` / `amama` / `hijab`), `style=panjabi` (`panjabi` / `shirt` / `gown`).

## Backgrounds
`masjid`, `masjid_evening` (prayer hall) | `masjid_yard`, `masjid_yard_evening` (outside, dome and minarets) | `home`, `home_evening` | `classroom` (madrasa)

## Props (`> prop name at 0.5 scale 0.8` ... `> prop name off`)
`dastarkhan` (food spread) | `glass_pieces` | `rehal` (Quran stand with an open book, no writing drawn) | plus the old `pot`, `mango`

## `> hadith` and `> tip` cards
* `> hadith "text" "source"` shows a green card at the top (heading "হাদীসের বাণী"). Keep the text to about 2 lines (under ~120 characters).
* `> tip "text"` shows a gold card (heading "আজকের টিপস").
* The card stays on screen while the next lines are spoken, until `> hadith off` / `> tip off`, the next `SCENE`, or the end.
* A new `> hadith` replaces the old one. They do not add time, they are shown while the characters talk.

## Good practice for the content
* One video = one idea = one hadith. Problem (3-4 lines) -> explanation with the hadith (3-4 lines) -> change of behaviour (3-4 lines). About 160-200 spoken words = 1.5 minutes.
* Write Arabic phrases in Bangla letters (বিসমিল্লাহ, আলহামদুলিল্লাহ, আউযুবিল্লাহ). The Bangla font has no Arabic letters, and the voice reads Bangla spelling correctly.
* Say the full salawat (সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম) at least once when the Prophet's name is mentioned.
* Write the source of every hadith (book + number) on the card, and have a trusted alim check it. Numbering differs between Bangla editions.
* Only ordinary people are drawn. Prophets, the sahaba and angels are never drawn: the hujur / baba tells what they said or did, in words.

## Sound
* Voices: same as before (edge-tts). Hujur = `bn-IN-BashkarNeural` with `fx=-2`, child = `fx=5` (higher), ma = `bn-BD-NabanitaNeural`.
* No music by default. To add something that suits your audience, for example a nasheed with voice only or a soft nature sound:
  put it at `music/islamic_music.mp3` (quiet, ducks under speech) and/or `music/islamic_intro.wav` (plays on the title card).
