"""
script.py - reads a plain-text screenplay (stories/*.txt) and turns it into the story dict.

    TITLE: Story name | subtitle | seconds
    CHARACTERS:
    raja   | রাজা   | king     | voice=bn-IN-BashkarNeural rate=-10 pitch=-12 fx=-2
    chandu | চাঁদু  | jester   | voice=bn-BD-PradeepNeural rate=6 fx=3  coat=20,100,150

    SCENE garden: raja@0.42 chandu@0.70:left
    raja (angry, point, to=chandu): Spoken line goes here. || chandu:nervous
    > enter mantri from right to 0.2 happy 2
    > act chandu bow 1.5
    END: সমাপ্ত | subtitle | 3

Full cheat sheet: see SYNTAX.md
"""
import difflib
import json
import re
import shlex
from pathlib import Path

from . import art
from .anim import ACTION_NAMES, EMOTIONS, GESTURES

BACKGROUNDS = ["garden", "garden_empty", "court", "court_evening", "market"]
VOICE_KEYS = {"voice", "rate", "pitch", "fx", "tempo"}
DEFAULT_VOICES = {"king": "bn-IN-BashkarNeural"}
LEFT_RIGHT = {"left", "right"}


class ScriptError(ValueError):
    pass


def _err(n, msg):
    raise ScriptError(f"Story line {n}: {msg}")


def _suggest(word, options):
    m = difflib.get_close_matches(word, list(options), n=1, cutoff=0.5)
    return f"  Did you mean '{m[0]}'?" if m else ""


def _val(v):
    v = v.strip().strip('"')
    if re.fullmatch(r"\d+(\s*,\s*\d+){2}", v):
        return [int(p) for p in v.split(",")]
    if v.lower() in ("true", "yes", "on"):
        return True
    if v.lower() in ("false", "no", "off"):
        return False
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v


def _pos(v, n):
    if v in LEFT_RIGHT:
        return v
    try:
        x = float(v)
    except ValueError:
        _err(n, f"'{v}' is not a position. Use a number between 0 (left edge) and 1 (right edge), or left / right.")
    return x


def _kv(text):
    return {k: _val(v) for k, v in re.findall(r'(\w+)=("[^"]*"|\S+)', text)}


def _reactions(text, chars, n):
    """'mantri:nervous raja:laugh+smirk' -> {'mantri': ['nervous'], 'raja': ['laugh', 'smirk']}"""
    out = {}
    for tok in text.split():
        if ":" not in tok:
            _err(n, f"reaction '{tok}' should look like  name:reaction  (example  mantri:nervous)")
        who, rest = tok.split(":", 1)
        if who not in chars:
            _err(n, f"unknown character '{who}' in a reaction." + _suggest(who, chars))
        items = rest.split("+")
        for r in items:
            if r not in ACTION_NAMES and r not in EMOTIONS:
                _err(n, f"unknown reaction '{r}'." + _suggest(r, list(ACTION_NAMES) + list(EMOTIONS)))
        out[who] = items
    return out


def _split_reactions(text):
    if " || " in text:
        a, b = text.split(" || ", 1)
        return a.strip(), b.strip()
    return text.strip(), ""


def parse_script(text):
    chars, beats = {}, []
    story = dict(title="", fps=24, ground_y=596, speaker_zoom=1.08, characters=chars, beats=beats)
    mode = None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        m = re.match(r"^(TITLE|END)\s*:\s*(.*)$", line, re.I)
        if m:
            parts = [p.strip() for p in m.group(2).split("|")]
            beat = {"do": "title" if m.group(1).upper() == "TITLE" else "end", "text": parts[0],
                    "sub": parts[1] if len(parts) > 1 else "", "dur": float(parts[2]) if len(parts) > 2 and parts[2] else 3.2,
                    "_line": n}
            if beat["do"] == "title" and not story["title"]:
                story["title"] = parts[0]
            beats.append(beat)
            mode = None
            continue

        m = re.match(r"^(FPS|ZOOM|GROUND)\s*:\s*([\d.]+)$", line, re.I)
        if m:
            key = {"FPS": "fps", "ZOOM": "speaker_zoom", "GROUND": "ground_y"}[m.group(1).upper()]
            story[key] = int(float(m.group(2))) if key != "speaker_zoom" else float(m.group(2))
            continue

        if re.match(r"^CHARACTERS\s*:?\s*$", line, re.I):
            mode = "chars"
            continue

        m = re.match(r"^SCENE\s+(\w+)\s*:?\s*(.*)$", line, re.I)
        if m:
            mode = None
            bg, rest = m.group(1), m.group(2)
            if bg not in BACKGROUNDS and not Path(f"assets/bg_{bg}.png").exists():
                _err(n, f"unknown background '{bg}'. Choices: {', '.join(BACKGROUNDS)}." + _suggest(bg, BACKGROUNDS))
            cast = {}
            for tok in rest.replace(",", " ").split():
                mm = re.fullmatch(r"(\w+)@([\d.]+)(?::(left|right))?", tok)
                if not mm:
                    _err(n, f"cast entry '{tok}' should look like  name@0.4  or  name@0.4:left")
                who = mm.group(1)
                if who not in chars:
                    _err(n, f"unknown character '{who}'. Define it under CHARACTERS first." + _suggest(who, chars))
                x = float(mm.group(2))
                if not 0 <= x <= 1:
                    _err(n, f"position {x} must be between 0 and 1.")
                cast[who] = {"x": x, **({"face": mm.group(3)} if mm.group(3) else {})}
            if not cast:
                _err(n, "a SCENE needs at least one character, for example  SCENE court: raja@0.7 chandu@0.3")
            beats.append({"do": "scene", "bg": bg, "cast": cast, "_line": n})
            continue

        if mode == "chars" and "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3:
                _err(n, "a character line needs:  id | Bangla name | look | settings(optional)")
            cid, label, base = parts[0], parts[1], parts[2]
            if not re.fullmatch(r"\w+", cid):
                _err(n, f"character id '{cid}' should be one word (letters/numbers/_).")
            if base not in art.DESIGNS:
                _err(n, f"unknown look '{base}'. Choices: {', '.join(art.DESIGNS)}." + _suggest(base, art.DESIGNS))
            kv = _kv(parts[3]) if len(parts) > 3 else {}
            voice = {"name": DEFAULT_VOICES.get(base, "bn-BD-PradeepNeural")}
            design = {"base": base}
            for k, v in kv.items():
                if k in VOICE_KEYS:
                    voice["name" if k == "voice" else k] = v
                else:
                    design[k] = v
            chars[cid] = {"label": label, "design": design, "voice": voice}
            continue

        if line.startswith(">"):
            mode = None
            beats.append(_command(line[1:].strip(), chars, n))
            continue

        m = re.match(r"^(\w+)\s*(?:\(([^)]*)\))?\s*:\s*(.+)$", line)
        if m and m.group(1) in chars:
            who, opts, body = m.group(1), m.group(2) or "", m.group(3)
            text_part, react = _split_reactions(body)
            beat = {"do": "say", "who": who, "text": text_part, "_line": n}
            for tok in [t.strip() for t in opts.split(",") if t.strip()]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    v = _val(v)
                    if k == "to":
                        if isinstance(v, str) and v not in chars:
                            _err(n, f"'to={v}': no such character." + _suggest(v, chars))
                        beat["to"] = v
                    elif k in ("pre", "post", "zoom"):
                        beat[k] = float(v)
                    else:
                        _err(n, f"unknown option '{k}='. Use to= pre= post= zoom=")
                elif tok == "hold":
                    beat["hold"] = True
                elif tok in EMOTIONS:
                    beat["emotion"] = tok
                elif tok in GESTURES:
                    beat["gesture"] = tok
                else:
                    _err(n, f"'{tok}' is not an emotion, gesture or option." + _suggest(tok, list(EMOTIONS) + GESTURES) +
                         f"\n  Emotions: {', '.join(EMOTIONS)}\n  Gestures: {', '.join(GESTURES)}")
            if react:
                beat["also"] = _reactions(react, chars, n)
            beats.append(beat)
            continue

        first = line.split()[0].rstrip(":")
        if re.match(r"^\w+\s*(\(.*\))?\s*:", line) and first not in chars:
            _err(n, f"'{first}' is not a character." + _suggest(first, chars) + "  (Define characters under CHARACTERS:)")
        _err(n, f"I do not understand this line:  {line[:60]}")

    if not chars:
        raise ScriptError("No characters found. Add a CHARACTERS: block.")
    if not any(b["do"] == "scene" for b in beats):
        raise ScriptError("No SCENE found. Add at least one line like  SCENE court: raja@0.5")
    return story


def _command(cmd, chars, n):
    try:
        tok = shlex.split(cmd)
    except ValueError:
        tok = cmd.split()
    if not tok:
        _err(n, "empty command after '>'")
    cmd_text, react = _split_reactions(cmd)
    if react:
        try:
            tok = shlex.split(cmd_text)
        except ValueError:
            tok = cmd_text.split()
    verb, args = tok[0].lower(), tok[1:]
    b = {"do": verb, "_line": n}
    if react:
        b["also"] = _reactions(react, chars, n)

    def need_char(i=0):
        if len(args) <= i:
            _err(n, f"'> {verb}' needs a character name.")
        who = args[i]
        if who not in chars:
            _err(n, f"unknown character '{who}'." + _suggest(who, chars))
        return who

    def num(s):
        try:
            return float(s)
        except ValueError:
            return None

    if verb in ("enter", "exit", "move"):
        b["who"] = need_char()
        i = 1
        while i < len(args):
            a = args[i]
            if a == "from" and i + 1 < len(args):
                b["from"] = _pos(args[i + 1], n); i += 2
            elif a == "to" and i + 1 < len(args):
                b["to"] = _pos(args[i + 1], n); i += 2
            elif a in EMOTIONS:
                b["emotion"] = a; i += 1
            elif num(a) is not None:
                b["dur"] = num(a); i += 1
            else:
                _err(n, f"don't understand '{a}' in '> {verb}'. Example:  > enter chandu from right to 0.6 happy 2")
        if verb == "enter":
            b.setdefault("from", "right" if b.get("to", 0.5) > 0.5 else "left")
            b.setdefault("to", 0.5)
        elif verb == "exit":
            b.setdefault("to", "right")
        elif "to" not in b:
            _err(n, "'> move' needs a target:  > move raja to 0.5 1.5")
    elif verb == "act":
        b["who"] = need_char()
        if len(args) < 2:
            _err(n, "'> act' needs an action:  > act chandu bow 1.5")
        b["action"] = args[1]
        if args[1] not in ACTION_NAMES:
            _err(n, f"unknown action '{args[1]}'." + _suggest(args[1], ACTION_NAMES) + f"\n  Actions: {', '.join(sorted(ACTION_NAMES))}")
        for a in args[2:]:
            if num(a) is not None:
                b["dur"] = num(a)
            elif a.startswith("to="):
                v = _val(a[3:])
                if isinstance(v, str) and v not in chars:
                    _err(n, f"'{a}': no such character." + _suggest(v, chars))
                b["to"] = v
            elif a in EMOTIONS:
                b["emotion"] = a
            else:
                _err(n, f"don't understand '{a}' in '> act'.")
    elif verb == "wait":
        b["dur"] = num(args[0]) if args and num(args[0]) is not None else 0.5
    elif verb in ("dark", "darken"):
        b["do"] = "dark"
        b["level"] = num(args[0]) if args and num(args[0]) is not None else 0.9
        for a in args[1:]:
            if num(a) is not None:
                b["dur"] = num(a)
            else:
                b["text"] = a
    elif verb == "light":
        b["do"] = "dark"
        b["level"] = 0.0
        b["dur"] = num(args[0]) if args and num(args[0]) is not None else 0.9
    elif verb == "set":
        b["who"] = need_char()
        if len(args) < 3:
            _err(n, "'> set' example:  > set raja soot on   |  > set raja emotion angry  |  > set raja face left")
        key, val = args[1], args[2]
        if key == "soot":
            b["soot"] = _val(val) is True
        elif key == "emotion":
            if val not in EMOTIONS:
                _err(n, f"unknown emotion '{val}'." + _suggest(val, EMOTIONS))
            b["emotion"] = val
        elif key == "face":
            b["face"] = val
        elif key == "x":
            b["x"] = float(val)
        else:
            _err(n, f"cannot set '{key}'. Use soot / emotion / face / x.")
    elif verb == "prop":
        b["name"] = args[0] if args else _err(n, "'> prop' needs a name:  > prop pot at 0.5")
        if len(args) > 1 and args[1] == "off":
            b["show"] = False
        else:
            b["show"] = True
            for i, a in enumerate(args[1:], 1):
                if a == "at" and i + 1 < len(args):
                    b["x"] = float(args[i + 1])
                elif a == "scale" and i + 1 < len(args):
                    b["scale"] = float(args[i + 1])
    elif verb == "popup":
        b["text"] = args[0] if args else ""
        b["dur"] = num(args[1]) if len(args) > 1 and num(args[1]) is not None else 1.5
    elif verb == "cam":
        b["zoom"] = num(args[0]) if args and num(args[0]) is not None else 1.0
        if len(args) > 1:
            b["x"] = num(args[1]) or 0.5
        if len(args) > 2:
            b["dur"] = num(args[2]) or 0.9
    else:
        _err(n, f"unknown command '> {verb}'. Commands: enter exit move act wait dark light set prop popup cam")
    return b


def load_story(path):
    path = Path(path)
    if path.suffix.lower() == ".json":
        return json.load(open(path, encoding="utf-8"))
    return parse_script(path.read_text(encoding="utf-8"))


def estimate_seconds(story):
    """Rough length before voices exist (about 0.42 s per word)."""
    t = 0.0
    for b in story["beats"]:
        d = b["do"]
        if d == "say":
            t += len(b["text"].split()) * 0.42 + 0.65
        elif d in ("title", "end", "act", "wait", "enter", "exit", "move"):
            t += b.get("dur", 2.0)
    return t


def describe(story):
    from .audio import say_beats
    lines = list(say_beats(story))
    print(f"Title: {story.get('title', '')}")
    print("Characters: " + ", ".join(f"{k} ({v['label']})" for k, v in story["characters"].items()))
    print(f"Scenes: {sum(1 for b in story['beats'] if b['do'] == 'scene')}   Spoken lines: {len(lines)}   "
          f"Estimated length: about {estimate_seconds(story):.0f} seconds")
