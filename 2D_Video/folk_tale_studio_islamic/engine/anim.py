"""
anim.py - decides how a character stands, walks, talks and acts at time t.

Everything returns a "pose" dict for rig.Rig.draw(). Add your own actions to ACTIONS
and your own talking gestures to GESTURES - each is a small function of time.
"""
import math
import random

TAU = 2 * math.pi
STRIDE_PX = 200.0            # one full walking cycle = 200 px of screen movement


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def bump(u, u0, u1, att=0.25, rel=0.3):
    """0 -> 1 -> 0 weight between u0 and u1 (smooth in and out)."""
    if u < u0 or u > u1:
        return 0.0
    a = smoothstep((u - u0) / att) if att > 0 else 1.0
    r = smoothstep((u1 - u) / rel) if rel > 0 else 1.0
    return min(a, r)


def blend(a, b, w):
    """Mix pose b into pose a with weight w (numbers and tuples are mixed, words switch at 50%)."""
    out = dict(a)
    for k, v in b.items():
        if k not in a:
            out[k] = v
            continue
        av = a[k]
        if isinstance(v, bool) or isinstance(v, str) or v is None:
            out[k] = v if w > 0.5 else av
        elif isinstance(v, (int, float)):
            out[k] = av + (v - av) * w
        else:
            out[k] = tuple(x + (y - x) * w for x, y in zip(av, v))
    return out


# ------------------------------------------------------------------ emotions (face + small posture)
EMOTIONS = {
    "neutral": dict(brow="neutral", eyes="open", mouth="closed"),
    "happy": dict(brow="happy", eyes="open", mouth="smile"),
    "confident": dict(brow="happy", eyes="open", mouth="smile"),
    "angry": dict(brow="angry", eyes="open", mouth="frown"),
    "scared": dict(brow="sad", eyes="wide", mouth="small"),
    "nervous": dict(brow="sad", eyes="wide", mouth="small"),
    "surprised": dict(brow="surprised", eyes="wide", mouth="O"),
    "sad": dict(brow="sad", eyes="open", mouth="frown"),
    "thinking": dict(brow="sad", eyes="open", mouth="closed"),
    "scheming": dict(brow="angry", eyes="squint", mouth="smile"),
    "smirk": dict(brow="angry", eyes="squint", mouth="smile"),
}


def idle_pose(t, ph, emo):
    e = EMOTIONS.get(emo, EMOTIONS["neutral"])
    s = lambda f, p=0.0: math.sin(TAU * f * t + ph + p)
    p = dict(bob=1.2 * s(0.45), torso=0.7 * s(0.3), head=1.4 * s(0.27, 1.0), lift=0.0,
             arm_l=(8 + 1.8 * s(0.4, 0.5), 10 + 1.5 * s(0.35)), arm_r=(8 + 1.8 * s(0.4, 2.0), 10 + 1.5 * s(0.33, 1.0)),
             hand_l="open", hand_r="open", leg_l=0.0, leg_r=0.0, gaze=0, **e)
    if emo == "angry":
        p.update(hand_l="fist", hand_r="fist", arm_l=(14, 46), arm_r=(14, 46), head=-2)
    elif emo in ("scared", "nervous"):
        p.update(arm_l=(20, 96 + 6 * s(1.4)), arm_r=(20, 96 - 6 * s(1.4)), torso=1.2 * s(2.5), bob=-2)
    elif emo == "sad":
        p.update(head=9, bob=-3)
    elif emo in ("happy", "confident"):
        p.update(bob=1.8 * abs(s(0.8)))
    elif emo == "thinking":
        p.update(arm_r=(26, 138), hand_r="fist", head=6)
    return p


# ------------------------------------------------------------------ gestures while talking
def _arm(side):
    return ("arm_r", "hand_r") if side > 0 else ("arm_l", "hand_l")


def gesture_pose(name, u, side, tside):
    w = math.sin(TAU * 2.2 * u)
    ak, hk = _arm(side)
    tak, thk = _arm(tside)
    if name == "open":
        return dict(arm_l=(46 + 8 * w, 40), arm_r=(46 - 8 * w, 40))
    if name == "chest":
        return {ak: (22, 128), hk: "fist"}
    if name == "raise":
        return {ak: (150, 14), hk: "point"}
    if name == "point":
        return {tak: (80, 6), thk: "point"}
    if name == "shrug":
        return dict(arm_l=(42, 70), arm_r=(42, 70), bob=4)
    if name == "fist":
        return {ak: (66, 80), hk: "fist"}
    if name == "palm":
        return {ak: (56, 36 + 6 * w), hk: "open"}
    if name == "wave":
        return {ak: (140, 28 + 24 * w), hk: "open"}
    if name == "show_hands":
        return dict(arm_l=(52, 50), arm_r=(52, 50), hand_l="open", hand_r="open")
    if name == "salute":
        return dict(arm_l=(20, 120), arm_r=(20, 120), head=6)
    return {}


GESTURES = ["open", "chest", "raise", "point", "shrug", "fist", "palm", "wave", "show_hands", "salute"]
POOLS = {
    "default": ["open", "chest", "palm", "raise", "shrug", "fist"],
    "angry": ["fist", "raise", "open", "fist"],
    "scared": ["chest", "palm", "shrug", "salute"],
    "nervous": ["chest", "palm", "shrug"],
    "happy": ["open", "chest", "palm", "wave"],
    "scheming": ["palm", "chest", "open"],
}


def make_schedule(seg):
    """Random but repeatable list of (start, end, gesture, side) for one spoken line."""
    p = seg.p
    rnd = random.Random(p["seed"])
    dur = seg.t1 - seg.t0
    sched = []
    t = 0.15
    if p.get("gesture"):
        sched.append((0.12, min(max(dur * 0.65, 1.3), 2.6), p["gesture"], rnd.choice((-1, 1))))
        t = sched[0][1] + 0.35
    pool = POOLS.get(p.get("emotion"), POOLS["default"])
    last = None
    while t < dur - 0.7:
        g = rnd.choice([x for x in pool if x != last])
        d = rnd.uniform(0.9, 1.5)
        sched.append((t, min(t + d, dur - 0.2), g, rnd.choice((-1, 1))))
        t += d + rnd.uniform(0.25, 0.7)
        last = g
    return sched


# ------------------------------------------------------------------ actions (no speech)
def act_pose(a, u, dur, tside):
    s = math.sin
    if a == "salute":
        return dict(arm_l=(20, 120), arm_r=(20, 120), head=7, brow="happy", mouth="smile")
    if a == "bow":
        w = s(math.pi * min(1.0, u / max(dur, 0.1)))
        return dict(arm_l=(20, 120), arm_r=(20, 120), torso=10 * w, head=16 * w, bob=-5 * w, brow="happy", mouth="smile")
    if a == "shock":
        return dict(lift=30 * max(0.0, s(math.pi * min(1.0, u / 0.5))), arm_l=(70, 35), arm_r=(70, 35),
                    eyes="wide", brow="surprised", mouth="O", torso=-5, head=-4)
    if a == "laugh":
        w = s(u * TAU * 3.2)
        return dict(bob=6 * abs(w), head=-7 + 3 * w, torso=2 * w, arm_l=(22, 72), arm_r=(22, 72),
                    eyes="happy", brow="happy", mouth="wide" if w > 0 else "open")
    if a == "think":
        return dict(arm_r=(26, 140), hand_r="fist", head=7, gaze=1, brow="sad", mouth="closed", eyes="open")
    if a == "cheer":
        w = s(u * TAU * 2.6)
        return dict(arm_l=(150 + 8 * w, 12), arm_r=(150 - 8 * w, 12), lift=8 * abs(w), eyes="happy",
                    brow="happy", mouth="wide")
    if a == "nervous":
        w = s(u * TAU * 5)
        return dict(arm_l=(22 + 4 * w, 102), arm_r=(22 - 4 * w, 102), torso=1.6 * w, eyes="wide",
                    brow="sad", mouth="small")
    if a == "point":
        ak = "arm_r" if tside > 0 else "arm_l"
        hk = "hand_r" if tside > 0 else "hand_l"
        return {ak: (80, 6), hk: "point"}
    if a == "show_hands":
        return dict(arm_l=(52, 50), arm_r=(52, 50), hand_l="open", hand_r="open")
    if a == "guilty":
        return dict(head=12, arm_l=(20, 102), arm_r=(20, 102), eyes="squint", brow="sad", mouth="frown", bob=-3)
    if a == "stomp":
        w = abs(s(u * TAU * 2.5))
        return dict(lift=7 * w, hand_l="fist", hand_r="fist", arm_l=(16, 92), arm_r=(16, 92),
                    brow="angry", mouth="frown", torso=2 * s(u * TAU * 5))
    if a == "smirk":
        return dict(eyes="squint", brow="angry", mouth="smile", head=6, torso=2)
    if a == "wave":
        ak = "arm_r"
        return {ak: (140, 28 + 24 * s(u * TAU * 2.4)), "hand_r": "open", "mouth": "smile"}
    if a == "touch":
        return dict(arm_r=(46, 52), hand_r="open", torso=2, head=-3)
    if a == "cower":
        return dict(bob=-8, head=10, arm_l=(20, 110), arm_r=(20, 110), eyes="wide", mouth="small", torso=3)
    return {}


ACTION_NAMES = {"salute", "bow", "shock", "laugh", "think", "cheer", "nervous", "point", "show_hands", "guilty",
                "stomp", "smirk", "wave", "touch", "cower"}


# ------------------------------------------------------------------ main entry
def _phase(name):
    return (sum(ord(c) for c in name) % 63) / 10.0


def local_side(world_side, f):
    """A screen side (+1 right / -1 left) -> which arm of the (possibly mirrored) rig."""
    return world_side * f


def make_pose(tl, name, t, stage_w=1280):
    """Returns (pose, facing, x_pixels) or None if the character is not on stage."""
    s = tl.char_state(name, t)
    if not s["visible"]:
        return None
    ph = _phase(name)
    f = 1 if s["face"] >= 0 else -1
    x_px = s["x"] * stage_w
    pose = idle_pose(t, ph, s["emotion"])

    # where am I looking?
    look = s["look"]
    tx = None
    if isinstance(look, str):
        o = tl.char_state(look, t)
        tx = o["x"] if o["visible"] else None
    elif isinstance(look, (int, float)):
        tx = look
    if tx is not None and abs(tx - s["x"]) > 0.05:
        pose["gaze"] = int((1 if tx > s["x"] else -1) * f)

    # walking
    if s["moving"]:
        wp = TAU * s["dist"] * stage_w / STRIDE_PX
        pose.update(leg_l=26 * math.sin(wp), leg_r=-26 * math.sin(wp), bob=5 * abs(math.sin(wp)),
                    arm_l=(11 + 9 * math.sin(wp), 14), arm_r=(11 - 9 * math.sin(wp), 14),
                    torso=2.4 * math.sin(wp), head=-1.5 * math.sin(wp))

    seg = s["seg"]
    if seg is not None and seg.kind == "talk":
        pose = _talk(pose, seg, t, tl.fps, f, s)
    elif seg is not None and seg.kind == "act":
        u, dur = t - seg.t0, seg.t1 - seg.t0
        to_x = seg.p.get("to_x")
        world = 1 if (to_x is not None and to_x > s["x"]) or to_x is None else -1
        w = bump(u, 0, dur, 0.22, 0.28)
        if seg.p["action"] in ("shock", "laugh", "cheer", "nervous", "stomp"):
            w = bump(u, 0, dur, 0.08, 0.2)
        pose = blend(pose, act_pose(seg.p["action"], u, dur, local_side(world, f)), w)

    # blinking
    if pose["eyes"] == "open" and ((t * 0.27 + ph / TAU) % 1.0) < 0.045:
        pose["eyes"] = "closed"
    pose["soot"] = s["soot"]
    return pose, f, x_px


def _talk(pose, seg, t, fps, f, s):
    p = seg.p
    env = p["env"]
    k = int((t - seg.t0) * fps)
    lv = float(env[k]) if 0 <= k < len(env) and t <= p["a1"] else 0.0
    emo = p["emotion"]
    if lv > 0.62:
        shape = "wide" if (emo in ("angry", "happy", "surprised") and lv > 0.95) else "open"
    elif lv > 0.30:
        shape = "mid"
    elif lv > 0.10:
        shape = "small"
    else:
        shape = pose["mouth"] if pose["mouth"] in ("smile", "frown") else "closed"
    pose["mouth"] = shape
    pose["bob"] += lv * 2.6
    pose["head"] += 3.0 * math.sin(t * 3.1) * lv - 2.5 * lv
    pose["torso"] += 1.2 * math.sin(t * 1.7)

    sched = p.get("_sched")
    if sched is None:
        sched = p["_sched"] = make_schedule(seg)
    u = t - seg.t0
    to_x = p.get("to_x")
    world_t = 1 if (to_x is None or to_x > s["x"]) else -1
    for g0, g1, name, side in sched:
        w = bump(u, g0, g1, 0.22, 0.32)
        if w > 0:
            tgt = gesture_pose(name, u - g0, local_side(side, f), local_side(world_t, f))
            if name == "point" and to_x is not None:
                tgt = gesture_pose(name, u - g0, 1, local_side(world_t, f))
            pose = blend(pose, tgt, w)
    return pose
