"""
rig.py - a paper cut-out puppet.

A Rig owns the part images of one character and draws it for a given "pose".
All angles are in degrees, counter-clockwise on screen.

pose keys (all optional, see DEFAULT_POSE):
  bob, lift       vertical offsets in pixels (body bounce / jump)
  torso, head     lean of the body / tilt of the head
  arm_l, arm_r    (abduction, elbow flex): abduction swings the arm away from the body,
                  flex bends the forearm in/up.  arm_l is the arm on the screen-left side.
  hand_l, hand_r  'open' | 'fist' | 'point'
  leg_l, leg_r    leg swing
  eyes            'open' | 'wide' | 'closed' | 'happy' | 'squint'
  gaze            -1, 0, 1  (where the pupils look)
  brow            'neutral' | 'angry' | 'surprised' | 'sad' | 'happy'
  mouth           'closed' | 'smile' | 'frown' | 'small' | 'mid' | 'open' | 'wide' | 'O'
  soot            True -> black hands (for the pot scene)
"""
import math
from PIL import Image, ImageDraw, ImageFilter
from . import art

DEFAULT_POSE = dict(bob=0.0, lift=0.0, torso=0.0, head=0.0,
                    arm_l=(8.0, 12.0), arm_r=(8.0, 12.0), hand_l="open", hand_r="open",
                    leg_l=0.0, leg_r=0.0, eyes="open", gaze=0, brow="neutral", mouth="closed", soot=False)

LEG_REACH = 142          # hip joint -> ground in unscaled art pixels
HIP_DX = 24
TORSO_PIVOT_DROP = 4
SHOULDER_Y = -196


def R(angle, v):
    """Rotate vector v counter-clockwise (as seen on screen, y points down)."""
    a = math.radians(angle)
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c + v[1] * s, -v[0] * s + v[1] * c)


def _scaled(img, k):
    if abs(k - 1) < 1e-3:
        return img
    return img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)


class Rig:
    def __init__(self, name, design_spec):
        self.name = name
        self.d, parts = art.character_sheet_parts(design_spec)
        self.k = float(self.d.get("scale", 0.62))
        k = self.k
        self.parts = {n: _scaled(im, k) for n, im in parts.items()}
        self.shoulder_x = (62 * self.d["build"] - 14) * k
        self.sh_y = SHOULDER_Y * k
        self.neck = (0, -212 * k)
        self.hip_dx = HIP_DX * k
        self.leg_reach = LEG_REACH * k
        self.up_len = art.UP_LEN * k
        self.pivots = {
            "head": (art.HEAD_PIVOT[0] * k, art.HEAD_PIVOT[1] * k),
            "torso": (art.TORSO_PIVOT[0] * k, art.TORSO_PIVOT[1] * k),
            "upper": (art.UP_PIVOT[0] * k, art.UP_PIVOT[1] * k),
            "fore": (art.FA_PIVOT[0] * k, art.FA_PIVOT[1] * k),
            "leg": (art.LEG_PIVOT[0] * k, art.LEG_PIVOT[1] * k),
        }
        self._face = {}
        self._rot = {}
        self._flip = {}
        self.height = int(400 * k / 0.62 * 0.96)          # rough standing height (for UI/labels)
        self.shadow = self._make_shadow()

    # ------------------------------------------------------------------ helpers
    def _make_shadow(self):
        w, h = int(150 * self.k / 0.62), int(26 * self.k / 0.62)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse((0, 0, w - 1, h - 1), fill=(0, 0, 0, 80))
        return im.filter(ImageFilter.GaussianBlur(4))

    def face_head(self, eyes, gaze, brow, mouth):
        key = (eyes, gaze, brow, mouth)
        if key not in self._face:
            k = self.k
            im = self.parts["head"].copy()
            for layer in (art.eyes_img(self.d, eyes, gaze), art.brows_img(self.d, brow), art.mouth_img(self.d, mouth)):
                im.alpha_composite(_scaled(layer, k))
            self._face[key] = im
        return self._face[key]

    def _mirror(self, key, img):
        if key not in self._flip:
            self._flip[key] = img.transpose(Image.FLIP_LEFT_RIGHT)
        return self._flip[key]

    def _blit(self, frame, key, img, pivot, angle, pos, f):
        """Rotate img about pivot, put the pivot at pos. f = +1 / -1 mirror."""
        if f < 0:
            img = self._mirror(key, img)
            pivot = (img.width - pivot[0], pivot[1])
        aq = round(angle * 2) / 2.0
        ck = (key, f, aq)
        hit = self._rot.get(ck)
        if hit is None:
            w, h = img.size
            if aq % 360 == 0:
                rim, npv = img, pivot
            else:
                rim = img.rotate(aq, resample=Image.BICUBIC, expand=True)
                dx, dy = pivot[0] - w / 2, pivot[1] - h / 2
                rx, ry = R(aq, (dx, dy))
                npv = (rim.width / 2 + rx, rim.height / 2 + ry)
            if len(self._rot) > 6000:
                self._rot.clear()
            hit = self._rot[ck] = (rim, npv)
        rim, npv = hit
        frame.paste(rim, (round(pos[0] - npv[0]), round(pos[1] - npv[1])), rim)

    # ------------------------------------------------------------------ main draw
    def draw(self, frame, x, ground_y, pose, facing=1, shadow=True):
        p = dict(DEFAULT_POSE)
        p.update(pose)
        f = 1 if facing >= 0 else -1
        k = self.k
        lift = p["lift"] + p["bob"]

        def W(local):                                   # local (unmirrored, relative to root) -> world
            return (x + f * local[0], ground_y + local[1])

        if shadow:
            sh = self.shadow
            frame.paste(sh, (round(x - sh.width / 2), round(ground_y - sh.height / 2 + 4)), sh)

        hip = (0, -self.leg_reach - lift)
        # legs
        for side, name, ang in ((-1, "leg_l", p["leg_l"]), (1, "leg_r", p["leg_r"])):
            pos = W((hip[0] + side * self.hip_dx, hip[1]))
            self._blit(frame, name, self.parts[name], self.pivots["leg"], f * ang, pos, f)

        # torso
        tp = (hip[0], hip[1] + TORSO_PIVOT_DROP * k)
        t = p["torso"]
        self._blit(frame, "torso", self.parts["torso"], self.pivots["torso"], f * t, W(tp), f)

        # arms
        soot = "soot" if p["soot"] else "skin"
        for side, key_arm, key_hand in ((-1, "arm_l", "hand_l"), (1, "arm_r", "hand_r")):
            abd, flex = p[key_arm]
            sv = R(t, (side * self.shoulder_x, self.sh_y))          # shoulder offset from the torso pivot
            shoulder = (tp[0] + sv[0], tp[1] + sv[1])
            up_ang = t + side * abd
            self._blit(frame, "upper", self.parts["upper"], self.pivots["upper"], f * up_ang, W(shoulder), f)
            ev = R(up_ang, (0, self.up_len))
            elbow = (shoulder[0] + ev[0], shoulder[1] + ev[1])
            fore_ang = up_ang - side * flex
            fk = f"fore_{p[key_hand]}_{soot}"
            self._blit(frame, fk, self.parts[fk], self.pivots["fore"], f * fore_ang, W(elbow), f)

        # head
        nv = R(t, self.neck)
        neck = (tp[0] + nv[0], tp[1] + nv[1])
        head = self.face_head(p["eyes"], p["gaze"], p["brow"], p["mouth"])
        self._blit(frame, ("head", p["eyes"], p["gaze"], p["brow"], p["mouth"]), head, self.pivots["head"],
                   f * (t + p["head"]), W(neck), f)

    def head_world(self, x, ground_y):
        """Roughly where the head is (for camera / captions)."""
        return (x, ground_y - self.leg_reach - 330 * self.k)
