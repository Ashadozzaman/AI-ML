"""
timeline.py - turns story.json "beats" into a timeline.

Beat types (the "do" field):
  title / end   full-screen card                 {"do":"title","text":"...","sub":"...","dur":3}
  scene         new background + who is on stage {"do":"scene","bg":"garden","cast":{"raja":{"x":0.4,"face":"right"}}}
  enter / exit / move   walking                  {"do":"enter","who":"chandu","from":"right","to":0.6,"dur":2}
  say           a spoken line (audio + lip sync) {"do":"say","who":"raja","text":"...","emotion":"angry","gesture":"point","to":"chandu"}
  act           an action without speech         {"do":"act","who":"chandu","action":"bow","dur":1.5}
  wait          pause                            {"do":"wait","dur":0.5}
  set           instant change                   {"do":"set","who":"raja","soot":true}
  dark          fade to dark / back              {"do":"dark","level":0.9,"dur":0.8,"text":"..."}
  prop          show/hide a prop                 {"do":"prop","name":"pot","x":0.5,"show":true}
  cam           camera                           {"do":"cam","zoom":1.1,"x":0.5}
x positions are fractions of the screen width (0 = left edge, 1 = right edge).
"""
import bisect
from pathlib import Path

from . import audio as A
from .text import split_caption

OFF_LEFT, OFF_RIGHT = -0.14, 1.14


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


class Keys:
    """Time -> value (step function)."""

    def __init__(self, default=None):
        self.t, self.v, self.default = [], [], default

    def add(self, t, v):
        i = bisect.bisect_right(self.t, t)
        self.t.insert(i, t)
        self.v.insert(i, v)

    def at(self, t):
        i = bisect.bisect_right(self.t, t) - 1
        return self.v[i] if i >= 0 else self.default


class Seg:
    __slots__ = ("t0", "t1", "kind", "p")

    def __init__(self, t0, t1, kind, p):
        self.t0, self.t1, self.kind, self.p = t0, t1, kind, p


class Track:
    def __init__(self):
        self.tw, self.tw_t0 = [], []                      # walking tweens (t0, t1, x0, x1)
        self.vis, self.face = Keys(False), Keys(1)
        self.emo, self.soot, self.look = Keys("neutral"), Keys(False), Keys(None)
        self.segs, self.seg_t0 = [], []

    def add_tween(self, t0, t1, x0, x1):
        self.tw.append((t0, t1, x0, x1))
        self.tw_t0.append(t0)

    def add_seg(self, seg):
        i = bisect.bisect_right(self.seg_t0, seg.t0)
        self.segs.insert(i, seg)
        self.seg_t0.insert(i, seg.t0)


class Timeline:
    def __init__(self, story, root, fps=None, draft_if_missing=False):
        self.story = story
        self.root = Path(root)
        self.fps = fps or story.get("fps", 24)
        self.audio_dir = self.root / "audio"
        self.draft_if_missing = draft_if_missing
        self.names = list(story["characters"])
        self.tr = {n: Track() for n in self.names}
        self.bg = Keys("court")
        self.fades = []                                    # (t0, t1, a0, a1)
        self.dark = Keys((0.0, 0.01, ""))
        self.cam = [(0.0, 1.0, 0.5, 0.01)]                 # (t, zoom, cx, transition seconds)
        self.props = []
        self.caps = []                                     # (t0, t1, text, label)
        self.cards = []                                    # (t0, t1, kind, text, sub)
        self.audio_events = []
        self.beat_log = []
        self.total = 0.0
        self._compile()

    # ------------------------------------------------------------------ compile
    def _pos(self, v, default=0.5):
        if v == "left":
            return OFF_LEFT
        if v == "right":
            return OFF_RIGHT
        return float(v) if v is not None else default

    def _compile(self):
        st = self.story
        beats = st["beats"]
        names = self.names
        lines = {id(b): lid for lid, b in A.say_beats(st)}
        x_now = {n: 0.5 for n in names}
        vis_now = {n: False for n in names}
        emo_now = {n: "neutral" for n in names}
        T = 0.0
        first_visual = True

        def fade_in(t):
            self.fades.append((t, t + 0.5, 1.0, 0.0))
            if t > 0.5:
                self.fades.append((t - 0.4, t, 0.0, 1.0))

        def target_x(to, who):
            if to is None:
                others = [(abs(x_now[n] - x_now[who]), x_now[n]) for n in names if n != who and vis_now[n]]
                return min(others)[1] if others else None, None
            if isinstance(to, (int, float)):
                return float(to), None
            return x_now[to], to

        def face_towards(who, tx, t):
            if tx is not None and abs(tx - x_now[who]) > 0.06:
                self.tr[who].face.add(t, 1 if tx > x_now[who] else -1)

        def apply_also(also, t0, t1, hold=False):
            for who, val in (also or {}).items():
                for v in ([val] if isinstance(val, str) else val):
                    if v in ACTION_NAMES:
                        self.tr[who].add_seg(Seg(t0, t1, "act", {"action": v, "to_x": None}))
                    else:
                        self.tr[who].emo.add(t0, v)
                        if not hold:
                            self.tr[who].emo.add(t1, emo_now[who])
                        else:
                            emo_now[who] = v

        for b in beats:
            do = b["do"]
            self.beat_log.append((round(T, 2), do, b.get("who") or b.get("text", "")[:24] or b.get("bg", "")))

            if do in ("title", "end"):
                dur = b.get("dur", 3.0)
                self.cards.append((T, T + dur, do, b.get("text", ""), b.get("sub", "")))
                self.bg.add(T, "title")
                for n in names:
                    self.tr[n].vis.add(T, False)
                    vis_now[n] = False
                self.cam.append((T, 1.0, 0.5, 0.01))
                self.dark.add(T, (0.0, 0.01, ""))
                fade_in(T) if not first_visual or do == "end" else self.fades.append((T, T + 0.7, 1.0, 0.0))
                first_visual = False
                T += dur

            elif do == "scene":
                self.bg.add(T, b["bg"])
                cast = b.get("cast", {})
                for n in names:
                    if n in cast:
                        c = cast[n] or {}
                        x = self._pos(c.get("x", 0.5))
                        self.tr[n].add_tween(T, T, x, x)
                        self.tr[n].vis.add(T, True)
                        face = c.get("face")
                        f = -1 if face == "left" else 1 if face == "right" else (1 if x < 0.5 else -1)
                        self.tr[n].face.add(T, f)
                        self.tr[n].emo.add(T, c.get("emotion", "neutral"))
                        self.tr[n].soot.add(T, False)
                        self.tr[n].look.add(T, None)
                        x_now[n], vis_now[n], emo_now[n] = x, True, c.get("emotion", "neutral")
                    else:
                        self.tr[n].vis.add(T, False)
                        vis_now[n] = False
                self.cam.append((T, b.get("zoom", 1.0), 0.5, 0.01))
                self.dark.add(T, (0.0, 0.01, ""))
                for p in self.props:                      # props do not follow you to the next scene
                    if p["t1"] is None:
                        p["t1"] = T
                fade_in(T)
                first_visual = False

            elif do in ("enter", "exit", "move"):
                who, dur = b["who"], b.get("dur", 2.0)
                x0 = self._pos(b.get("from"), x_now[who]) if do == "enter" else x_now[who]
                x1 = self._pos(b.get("to"), x0)
                if do == "exit":
                    x1 = self._pos(b.get("to", "right"))
                tr = self.tr[who]
                if do == "enter":
                    tr.vis.add(T, True)
                    vis_now[who] = True
                    if "emotion" in b:
                        tr.emo.add(T, b["emotion"])
                        emo_now[who] = b["emotion"]
                tr.add_tween(T, T + dur, x0, x1)
                if abs(x1 - x0) > 0.01:
                    tr.face.add(T, 1 if x1 > x0 else -1)
                if do == "exit":
                    tr.vis.add(T + dur, False)
                    vis_now[who] = False
                x_now[who] = x1
                apply_also(b.get("also"), T, T + dur)
                T += dur

            elif do == "say":
                who = b["who"]
                if not vis_now[who]:
                    raise ValueError(f"'{who}' speaks at {T:.1f}s but is not on stage (add them to the scene cast or use 'enter').")
                lid = lines[id(b)]
                path = A.find_audio(self.audio_dir, lid)
                if path is None:
                    if self.draft_if_missing:
                        path = A.make_draft_audio(b["text"], self.audio_dir / lid, seed=len(self.audio_events) + 1)
                    else:
                        raise FileNotFoundError(f"No audio for {lid}. Run notebook 02 (or turn on draft voices).")
                samples = A.decode(path)
                adur = len(samples) / A.SR
                env = A.envelope(samples, self.fps)
                pre, post = b.get("pre", 0.15), b.get("post", 0.5)
                a0, a1 = T + pre, T + pre + adur
                end = a1 + post
                emotion = b.get("emotion", "neutral")

                tx, tname = target_x(b.get("to"), who)
                face_towards(who, tx, T)
                self.tr[who].look.add(T, tname if tname else tx)
                for n in names:
                    if n != who and vis_now[n]:
                        face_towards(n, x_now[who], T)
                        self.tr[n].look.add(T, who)
                prev = emo_now[who]
                self.tr[who].emo.add(T, emotion)
                if b.get("hold"):
                    emo_now[who] = emotion
                else:
                    self.tr[who].emo.add(end, prev)
                self.tr[who].add_seg(Seg(a0, end - 0.1, "talk", dict(
                    line=lid, env=env, gesture=b.get("gesture"), emotion=emotion, to_x=tx,
                    seed=len(self.audio_events) * 7 + 3, a1=a1)))
                apply_also(b.get("also"), T, end, hold=b.get("hold", False))

                label = st["characters"][who].get("label", who)
                chunks = split_caption(b["text"])
                tot = sum(len(c) for c in chunks) or 1
                acc = a0
                for i, c in enumerate(chunks):
                    d = adur * len(c) / tot
                    self.caps.append((acc, (end - 0.05) if i == len(chunks) - 1 else acc + d, c, label))
                    acc += d
                self.audio_events.append((a0, path))
                zoom = b.get("zoom", st.get("speaker_zoom", 1.08))
                self.cam.append((T, zoom, 0.5 + (x_now[who] - 0.5) * 0.6, 0.9))
                T = end

            elif do == "act":
                who, dur = b["who"], b.get("dur", 1.5)
                tx, _ = target_x(b.get("to"), who) if b.get("to") is not None else (None, None)
                face_towards(who, tx, T)
                self.tr[who].add_seg(Seg(T, T + dur, "act", {"action": b["action"], "to_x": tx}))
                if "emotion" in b:
                    prev = emo_now[who]
                    self.tr[who].emo.add(T, b["emotion"])
                    self.tr[who].emo.add(T + dur, prev)
                apply_also(b.get("also"), T, T + dur)
                if "zoom" in b:
                    self.cam.append((T, b["zoom"], 0.5 + (x_now[who] - 0.5) * 0.6, 0.9))
                T += dur

            elif do == "wait":
                apply_also(b.get("also"), T, T + b.get("dur", 0.5))
                T += b.get("dur", 0.5)

            elif do == "set":
                who = b["who"]
                if "soot" in b:
                    self.tr[who].soot.add(T, bool(b["soot"]))
                if "emotion" in b:
                    self.tr[who].emo.add(T, b["emotion"])
                    emo_now[who] = b["emotion"]
                if "face" in b:
                    self.tr[who].face.add(T, -1 if b["face"] == "left" else 1)
                if "x" in b:
                    self.tr[who].add_tween(T, T, b["x"], b["x"])
                    x_now[who] = b["x"]

            elif do == "dark":
                self.dark.add(T, (float(b.get("level", 0.9)), max(0.01, b.get("dur", 0.8)), b.get("text", "")))

            elif do == "prop":
                if b.get("show", True):
                    self.props.append(dict(name=b["name"], x=b.get("x", 0.5), t0=T, t1=None, scale=b.get("scale", 0.8)))
                else:
                    for p in self.props:
                        if p["name"] == b["name"] and p["t1"] is None:
                            p["t1"] = T

            elif do == "cam":
                self.cam.append((T, b.get("zoom", 1.0), b.get("x", 0.5), b.get("dur", 0.9)))
            else:
                raise ValueError(f"Unknown beat type: {do}")

        self.total = T + 0.4
        self.fades.append((self.total - 0.7, self.total, 0.0, 1.0))
        self.cam.sort(key=lambda c: c[0])

    # ------------------------------------------------------------------ queries
    def fade_alpha(self, t):
        a = 0.0
        for t0, t1, a0, a1 in self.fades:
            if t0 <= t <= t1:
                a = max(a, a0 + (a1 - a0) * (t - t0) / max(t1 - t0, 1e-6))
        return a

    def camera(self, t):
        keys = self.cam
        i = bisect.bisect_right([k[0] for k in keys], t) - 1
        if i <= 0:
            return keys[0][1], keys[0][2]
        pt, pz, px, _ = keys[i - 1]
        kt, kz, kx, kd = keys[i]
        w = smoothstep((t - kt) / max(kd, 0.01))
        return pz + (kz - pz) * w, px + (kx - px) * w

    def dark_at(self, t):
        i = bisect.bisect_right(self.dark.t, t) - 1
        if i < 0:
            return 0.0, ""
        level, dur, text = self.dark.v[i]
        prev = self.dark.v[i - 1][0] if i > 0 else 0.0
        w = smoothstep((t - self.dark.t[i]) / dur)
        lv = prev + (level - prev) * w
        return lv, (text if lv > 0.4 else "")

    def bg_at(self, t):
        return self.bg.at(t)

    def card_at(self, t):
        for c in self.cards:
            if c[0] <= t < c[1]:
                return c
        return None

    def caption_at(self, t):
        for c in self.caps:
            if c[0] <= t < c[1]:
                return c
        return None

    def props_at(self, t):
        return [p for p in self.props if p["t0"] <= t and (p["t1"] is None or t < p["t1"])]

    def char_state(self, name, t):
        tr = self.tr[name]
        vis = bool(tr.vis.at(t))
        x, moving, direction, dist = 0.5, False, 0, 0.0
        i = bisect.bisect_right(tr.tw_t0, t) - 1
        if i >= 0:
            t0, t1, x0, x1 = tr.tw[i]
            if t >= t1 or t1 <= t0:
                x = x1
            else:
                u = (t - t0) / (t1 - t0)
                x = x0 + (x1 - x0) * u
                moving = abs(x1 - x0) > 0.01
                direction = 1 if x1 > x0 else -1
                dist = abs(x - x0)
        seg = None
        j = bisect.bisect_right(tr.seg_t0, t) - 1
        for jj in range(j, max(-1, j - 8), -1):
            s = tr.segs[jj]
            if s.t0 <= t < s.t1:
                seg = s
                break
        return dict(visible=vis, x=x, moving=moving, dir=direction, dist=dist, face=tr.face.at(t),
                    emotion=tr.emo.at(t), soot=bool(tr.soot.at(t)), seg=seg, look=tr.look.at(t))


from .anim import ACTION_NAMES  # noqa: E402  (after class definitions to avoid a cycle)
