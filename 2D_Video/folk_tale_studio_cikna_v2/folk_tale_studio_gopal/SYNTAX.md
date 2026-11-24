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
