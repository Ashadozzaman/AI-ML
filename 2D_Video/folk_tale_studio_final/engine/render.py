"""
render.py - the Studio: loads story.json, draws every frame, sends frames to ffmpeg.

    from engine.render import Studio
    studio = Studio(".", draft=True)          # draft=True -> offline test voices when audio is missing
    studio.preview(12.0)                      # one frame (PIL image)
    studio.render("output/test.mp4", start=0, end=10)
    studio.render("output/gopal_style.mp4")   # full video
"""
import math
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw

from . import art, audio as A
from .anim import make_pose
from .rig import Rig
from .script import load_story
from .text import caption_image, draw_text, get_fonts, text_len
from .timeline import Timeline

W, H = 1280, 720


class Studio:
    def __init__(self, root=".", story_file="story.txt", draft=False):
        self.root = Path(root)
        self.story_file = story_file
        self.story = load_story(self.root / story_file)
        self.fps = self.story.get("fps", 24)
        self.ground = self.story.get("ground_y", 596)
        self.tl = Timeline(self.story, self.root, self.fps, draft_if_missing=draft)
        self.rigs = {n: Rig(n, art.design(c.get("design", "king"))) for n, c in self.story["characters"].items()}
        self._bg, self._props, self._caps, self._cards = {}, {}, {}, {}
        self.draw_order = list(self.rigs)

    # ------------------------------------------------------------------ assets
    def bg(self, name):
        if name not in self._bg:
            p = self.root / "assets" / f"bg_{name}.png"
            if not p.exists():
                art.build_all_assets(self.root / "assets")
            self._bg[name] = Image.open(p).convert("RGB")
        return self._bg[name]

    def prop(self, name, scale):
        key = (name, scale)
        if key not in self._props:
            p = self.root / "assets" / f"prop_{name}.png"
            if not p.exists():
                art.build_all_assets(self.root / "assets")
            im = Image.open(p).convert("RGBA")
            self._props[key] = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        return self._props[key]

    def card_image(self, card):
        t0, t1, kind, text, sub = card
        key = (kind, text, sub)
        if key not in self._cards:
            im = self.bg("title").copy()
            d = ImageDraw.Draw(im)
            size = 92
            while True:
                fonts = get_fonts(self.root, size)
                if text_len(d, text, fonts) < 1120 or size <= 44:
                    break
                size -= 6
            draw_text(d, W / 2, 470, text, fonts, (255, 226, 140))
            if sub:
                draw_text(d, W / 2, 548, sub, get_fonts(self.root, 40), (240, 220, 200))
            self._cards[key] = im
        return self._cards[key]

    def caption(self, text, label):
        key = (text, label)
        if key not in self._caps:
            self._caps[key] = caption_image(self.root, text, label)
        return self._caps[key]

    # ------------------------------------------------------------------ one frame
    def frame(self, t):
        tl = self.tl
        card = tl.card_at(t)
        if card:
            img = self.card_image(card).copy()
        else:
            img = self.bg(tl.bg_at(t)).copy()
            for p in tl.props_at(t):
                sp = self.prop(p["name"], p["scale"])
                img.paste(sp, (int(p["x"] * W - sp.width / 2), int(self.ground + 10 - sp.height)), sp)
            states = []
            for n in self.draw_order:
                r = make_pose(tl, n, t, W)
                if r:
                    states.append((r[2], n, r))
            for _, n, (pose, f, x_px) in sorted(states):
                self.rigs[n].draw(img, x_px, self.ground, pose, f)
            zoom, cx = tl.camera(t)
            if zoom > 1.003:
                cw, ch = W / zoom, H / zoom
                x0 = min(max(cx * W - cw / 2, 0), W - cw)
                y0 = min(max((H - ch) * 0.62, 0), H - ch)
                img = img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
            lv, dtext = tl.dark_at(t)
            if lv > 0.01:
                img = Image.blend(img, Image.new("RGB", (W, H), (8, 6, 20)), min(lv, 0.97))
                if dtext:
                    d = ImageDraw.Draw(img)
                    draw_text(d, W / 2, 380, dtext, get_fonts(self.root, 40), (255, 226, 140))
            c = tl.caption_at(t)
            if c:
                cim, pos = self.caption(c[2], c[3])
                img.paste(cim, pos, cim)
            pop = tl.popup_at(t)
            if pop:
                u = t - pop[0]
                d = ImageDraw.Draw(img)
                fonts = get_fonts(self.root, 84)
                y = 190 - 14 * abs(math.sin(u * 11)) * max(0.0, 1 - u * 1.6)
                for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, 3), (-3, 3), (3, -3)):
                    draw_text(d, W / 2 + dx, y + dy, pop[2], fonts, (70, 24, 34))
                draw_text(d, W / 2, y, pop[2], fonts, (255, 226, 120))
        fa = tl.fade_alpha(t)
        if fa > 0.005:
            img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), min(fa, 1.0))
        return img

    def preview(self, t):
        return self.frame(t)

    def contact_sheet(self, times, cols=3, scale=0.5):
        ims = [self.frame(t).resize((int(W * scale), int(H * scale))) for t in times]
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * ims[0].width, rows * ims[0].height))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * im.width, (i // cols) * im.height))
        return sheet

    # ------------------------------------------------------------------ video
    def render(self, out_file="output/gopal_style.mp4", start=0.0, end=None, music="music/music.mp3"):
        out_file = Path(self.root) / out_file if not Path(out_file).is_absolute() else Path(out_file)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        tl, fps = self.tl, self.fps
        end = min(end or tl.total, tl.total)
        n0, n1 = int(start * fps), int(end * fps)

        samples, sr = A.mix_track(tl.audio_events, tl.total, self.root, music_path=self.root / music)
        wav = out_file.with_suffix(".mix.wav")
        A.write_wav(wav, samples[int(start * sr):int(end * sr)], sr)

        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(fps), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out_file)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        t_start = time.time()
        for i in range(n0, n1):
            proc.stdin.write(self.frame(i / fps).tobytes())
            if (i - n0) % (fps * 10) == 0:
                done = (i - n0) / max(n1 - n0, 1)
                print(f"  {i / fps:6.1f}s / {end:.1f}s  ({done * 100:3.0f}%)  elapsed {time.time() - t_start:4.0f}s")
        proc.stdin.close()
        proc.wait()
        wav.unlink()
        print(f"Saved {out_file}  ({(n1 - n0) / fps:.1f} s, {time.time() - t_start:.0f} s to render)")
        return out_file
