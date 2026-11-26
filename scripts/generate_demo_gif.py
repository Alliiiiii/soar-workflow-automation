#!/usr/bin/env python3
from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FPS = 10
N = 100
DURATION = 1000 // FPS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "soar-demo.gif"

FONT_DIR = Path("/usr/share/fonts/liberation")


def F(name, size):
    path = FONT_DIR / name
    if not path.exists():
        path = Path("/usr/share/fonts/truetype/dejavu") / name
    return ImageFont.truetype(str(path), size)


TITLE = F("LiberationSans-Bold.ttf", 30)
SUBTITLE = F("LiberationSans-Regular.ttf", 15)
CARD_T = F("LiberationSans-Bold.ttf", 15)
CARD_S = F("LiberationSans-Regular.ttf", 11)
BODY = F("LiberationSans-Regular.ttf", 12)
BODY_B = F("LiberationSans-Bold.ttf", 12)
MONO = F("LiberationMono-Regular.ttf", 12)
MONO_B = F("LiberationMono-Bold.ttf", 12)
SMALL = F("LiberationSans-Regular.ttf", 10)
TINY = F("LiberationSans-Bold.ttf", 9)
BIG = F("LiberationSans-Bold.ttf", 38)
HUGE = F("LiberationSans-Bold.ttf", 50)

BG_TOP = (6, 10, 18)
BG_BOT = (12, 21, 40)
PANEL = (15, 23, 42, 245)
PANEL_H = (20, 30, 52, 255)
BORDER = (45, 58, 82)
TEXT = (241, 245, 249)
MUTED = (148, 163, 184)
DIM = (100, 116, 139)
CYAN = (34, 211, 238)
GREEN = (34, 197, 94)
AMBER = (245, 158, 11)
RED = (239, 68, 68)
PURPLE = (168, 85, 247)
PINK = (236, 72, 153)

ACCENTS = [RED, CYAN, PURPLE, GREEN]
TITLES = ["KALI ATTACKER", "WAZUH SIEM", "SOAR ENGINE", "CONTAINMENT"]
SUBTITLES = ["hydra + nikto", "rules 5712 / 31151", "playbooks + guardrails", "active response + slack"]

_MEAS = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def fit(s, f, maxw):
    if _MEAS.textlength(s, font=f) <= maxw:
        return s
    while s and _MEAS.textlength(s + "\u2026", font=f) > maxw:
        s = s[:-1]
    return s + "\u2026"


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def glow(base, box, r, color, alpha=80, spread=8):
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(spread, 0, -1):
        a = int(alpha * (1 - i / spread) ** 2)
        d.rounded_rectangle(
            (box[0] - i, box[1] - i, box[2] + i, box[3] + i),
            radius=r + i,
            outline=color + (a,),
            width=2,
        )
    base.alpha_composite(ov)


def pill(d, box, text, f, fg, bg, border=None):
    rrect(d, box, (box[3] - box[1]) // 2, fill=bg, outline=border)
    d.text(((box[0] + box[2]) // 2, (box[1] + box[3]) // 2), text, font=f, fill=fg, anchor="mm")


def make_bg():
    g = Image.new("RGB", (1, H))
    for y in range(H):
        g.putpixel((0, y), lerp(BG_TOP, BG_BOT, y / (H - 1)))
    bg = g.resize((W, H))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for x in range(0, W, 40):
        d.line([(x, 0), (x, H)], fill=(56, 189, 248, 12))
    for y in range(0, H, 40):
        d.line([(0, y), (W, y)], fill=(56, 189, 248, 12))
    return Image.alpha_composite(bg.convert("RGBA"), ov)


def shield(d, cx, cy, w, h, color):
    pts = [
        (cx, cy - h / 2),
        (cx + w / 2, cy - h / 2 + 7),
        (cx + w / 2, cy + h / 4),
        (cx, cy + h / 2),
        (cx - w / 2, cy + h / 4),
        (cx - w / 2, cy - h / 2 + 7),
    ]
    d.polygon(pts, fill=color)


def stamp(base, text, center, size, color, angle=-8):
    f = F("LiberationSans-Bold.ttf", size)
    tmp = Image.new("RGBA", (200, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    rrect(d, (4, 4, 196, 60), 10, outline=color + (255,), width=3)
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((200 - tw) / 2, (64 - th) / 2 - 2), text, font=f, fill=color + (255,))
    tmp = tmp.rotate(angle, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(tmp, (int(center[0] - tmp.width / 2), int(center[1] - tmp.height / 2)))


def header(base, p):
    d = ImageDraw.Draw(base)
    d.text((28, 18), "SOAR INCIDENT RESPONSE", font=TITLE, fill=(248, 250, 252))
    d.text(
        (30, 56),
        "Wazuh SIEM/XDR  \u2192  Python playbook engine  \u2192  Active Response",
        font=SUBTITLE,
        fill=MUTED,
    )
    pulse = 0.5 + 0.5 * math.sin(p * math.pi * 8)
    box = (W - 170, 24, W - 70, 54)
    rrect(d, box, 15, fill=(40, 10, 15), outline=RED)
    r = 4 + 2 * pulse
    d.ellipse((box[0] + 14 - r, 39 - r, box[0] + 14 + r, 39 + r), fill=RED)
    d.text((box[0] + 32, 39), "LIVE", font=BODY_B, fill=(252, 165, 165), anchor="lm")
    pill(d, (W - 330, 24, W - 185, 54), "MTTC < 3s", BODY_B, GREEN, (10, 30, 20), GREEN)


def rail(base, p, active):
    d = ImageDraw.Draw(base)
    y = 100
    x0, x1 = 40, W - 40
    d.line((x0, y, x1, y), fill=(30, 41, 59), width=3)
    seg = (x1 - x0) / 4
    d.line((x0, y, x0 + seg * (active + 1), y), fill=CYAN, width=3)
    for i in range(4):
        cx = x0 + seg * i + seg / 2
        on = active >= i
        d.ellipse((cx - 7, y - 7, cx + 7, y + 7), fill=CYAN if on else (30, 41, 59), outline=(15, 23, 42), width=2)
        d.text((cx, y - 21), f"0{i + 1}", font=TINY, fill=CYAN if on else MUTED, anchor="mm")
    for k in range(7):
        px = x0 + ((p * 2.2 + k / 7) % 1) * (x1 - x0)
        d.ellipse((px - 3, y - 3, px + 3, y + 3), fill=(125, 211, 252))


def card(base, x, y, w, h, i, active, done, lt):
    accent = ACCENTS[i]
    box = (x, y, x + w, y + h)
    if active:
        glow(base, box, 14, accent, 95, 9)
    d = ImageDraw.Draw(base)
    outline = accent if (active or done) else BORDER
    rrect(d, box, 14, fill=PANEL, outline=outline, width=2 if active else 1)
    rrect(d, (x + 1, y + 1, x + w - 1, y + 50), 14, fill=PANEL_H)
    d.rectangle((x + 1, y + 34, x + w - 1, y + 50), fill=PANEL_H)
    d.line((x + 12, y + 50, x + w - 12, y + 50), fill=BORDER, width=1)
    cx, cy = x + 26, y + 25
    d.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), fill=accent)
    d.text((cx, cy), f"0{i + 1}", font=TINY, fill=(7, 11, 20), anchor="mm")
    d.text((x + 48, y + 14), TITLES[i], font=CARD_T, fill=TEXT)
    d.text((x + 48, y + 31), SUBTITLES[i], font=CARD_S, fill=MUTED)
    if done:
        d.text((x + w - 20, cy), "\u2713", font=BODY_B, fill=GREEN, anchor="mm")


def stage1(base, x, y, w, h, lt):
    d = ImageDraw.Draw(base)
    pill(d, (x + 12, y + 62, x + 214, y + 84), "KALI \u00b7 192.168.56.133", TINY, RED, (40, 15, 20), RED)
    tx, ty, tw, th = x + 12, y + 92, w - 24, 236
    rrect(d, (tx, ty, tx + tw, ty + th), 10, fill=(5, 8, 14), outline=BORDER)
    d.ellipse((tx + 10, ty + 8, tx + 18, ty + 16), fill=RED)
    d.ellipse((tx + 22, ty + 8, tx + 30, ty + 16), fill=AMBER)
    d.ellipse((tx + 34, ty + 8, tx + 42, ty + 16), fill=GREEN)
    d.text((tx + 50, ty + 6), "root@kali", font=TINY, fill=DIM)
    lines = [
        ("$ hydra -l labuser -P rockyou.txt", TEXT),
        ("  192.168.56.20 ssh", MUTED),
        ("[ATTEMPT] labuser:123456", (251, 146, 60)),
        ("[ATTEMPT] labuser:password", (251, 146, 60)),
        ("[ERROR] 47 failed logins", RED),
        ("$ nikto -h 192.168.56.20", TEXT),
        ("+ web burst -> rule 31151", AMBER),
    ]
    n = int(ease(lt) * len(lines)) + 1
    yy = ty + 28
    for s, c in lines[:n]:
        d.text((tx + 12, yy), fit(s, MONO, tw - 24), font=MONO, fill=c)
        yy += 22
    cy = ty + th + 20
    d.text((x + 14, cy), "FAILED LOGINS", font=TINY, fill=MUTED)
    val = int(47 * clamp(lt * 1.25))
    d.text((x + 14, cy + 10), f"{val:02d}", font=BIG, fill=RED)
    d.text((x + w - 14, cy + 18), "ATTACK", font=TINY, fill=RED, anchor="ra")
    r = 4 + 2 * math.sin(lt * math.pi * 10)
    d.ellipse((x + w - 32 - r, cy + 24 - r, x + w - 32 + r, cy + 24 + r), fill=RED)


def stage2(base, x, y, w, h, lt):
    d = ImageDraw.Draw(base)
    pill(d, (x + 12, y + 62, x + 212, y + 84), "WAZUH \u00b7 192.168.56.10", TINY, CYAN, (8, 30, 40), CYAN)
    cx, cy = x + w // 2, y + 120
    pulse = 3 + 3 * math.sin(lt * math.pi * 8)
    d.ellipse((cx - 30 - pulse, cy - 30 - pulse, cx + 30 + pulse, cy + 30 + pulse), outline=CYAN + (45,), width=2)
    shield(d, cx, cy, 46, 54, (8, 47, 73))
    shield(d, cx, cy, 36, 44, CYAN)
    d.text((cx, cy + 2), "W", font=BODY_B, fill=(7, 11, 20), anchor="mm")

    def alert(box, rule, level, mitre, color, reveal):
        if reveal <= 0:
            return
        off = int((1 - ease(reveal)) * 24)
        b = (box[0] + off, box[1], box[2] + off, box[3])
        rrect(d, b, 8, fill=(9, 16, 28), outline=color)
        d.text((b[0] + 10, b[1] + 8), rule, font=MONO_B, fill=color)
        d.text((b[0] + 10, b[1] + 26), level, font=SMALL, fill=MUTED)
        d.text((b[2] - 10, b[1] + 9), mitre, font=TINY, fill=TEXT, anchor="ra")

    alert((x + 12, y + 158, x + w - 12, y + 214), "RULE 5712", "LEVEL 10", "MITRE T1110", CYAN, lt - 0.12)
    alert((x + 12, y + 222, x + w - 12, y + 278), "RULE 31151", "LEVEL 10", "WEB BURST", AMBER, lt - 0.34)

    jy = y + 292
    if lt > 0.55:
        rrect(d, (x + 12, jy, x + w - 12, jy + 66), 8, fill=(5, 8, 14), outline=BORDER)
        d.text((x + 20, jy + 8), '{"rule_id": "5712",', font=MONO, fill=(125, 211, 252))
        d.text((x + 20, jy + 26), ' "level": 10,', font=MONO, fill=(125, 211, 252))
        d.text((x + 20, jy + 44), ' "srcip": "192.168.56.133"}', font=MONO, fill=(125, 211, 252))
    if lt > 0.7:
        d.text((x + 12, y + 374), "wazuh-integratord", font=MONO_B, fill=CYAN)
        d.text((x + w - 12, y + 374), "\u2192", font=BODY_B, fill=CYAN, anchor="ra")


def stage3(base, x, y, w, h, lt):
    d = ImageDraw.Draw(base)
    pill(d, (x + 12, y + 62, x + 226, y + 84), "custom-soar.py \u00b7 ENGINE", TINY, PURPLE, (28, 16, 45), PURPLE)
    chips = ["pb01_ssh_bruteforce", "pb02_compromised_account", "pb03_web_attack_burst"]
    for i, name in enumerate(chips):
        by = y + 94 + i * 30
        on = i == 0 and lt > 0.15
        b = (x + 12, by, x + w - 12, by + 24)
        rrect(d, b, 7, fill=(38, 22, 60) if on else (12, 18, 32), outline=PURPLE if on else BORDER)
        d.text((b[0] + 8, by + 5), fit(name, MONO if on else SMALL, b[2] - b[0] - 34), font=MONO if on else SMALL, fill=TEXT if on else MUTED)
        if on:
            d.text((b[2] - 8, by + 12), "\u25b6", font=TINY, fill=PURPLE, anchor="rm")
    ccx, ccy, r = x + 66, y + 252, 36
    d.ellipse((ccx - r, ccy - r, ccx + r, ccy + r), outline=(45, 58, 82), width=7)
    d.arc((ccx - r, ccy - r, ccx + r, ccy + r), -90, -90 + 360 * ease(lt), fill=PURPLE, width=7)
    d.text((ccx, ccy - 6), "600s", font=BODY_B, fill=TEXT, anchor="mm")
    d.text((ccx, ccy + 12), "COOLDOWN", font=TINY, fill=MUTED, anchor="mm")
    guards = [("IP allowlist", 0.3), ("Protected accounts", 0.45), ("Stateful dedupe", 0.6)]
    for i, (g, th) in enumerate(guards):
        gy = y + 216 + i * 24
        on = lt > th
        d.text((x + 122, gy), "\u2713" if on else "\u25cb", font=BODY_B, fill=GREEN if on else (71, 85, 105))
        d.text((x + 140, gy), g, font=SMALL, fill=TEXT if on else MUTED)
    if lt > 0.72:
        b = (x + 12, y + 326, x + w - 12, y + 356)
        rrect(d, b, 7, fill=(20, 15, 35), outline=PURPLE)
        d.text((b[0] + 9, b[1] + 9), "actions: firewall-drop", font=MONO, fill=GREEN)


def stage4(base, x, y, w, h, lt):
    d = ImageDraw.Draw(base)
    pill(d, (x + 12, y + 62, x + 222, y + 84), "ACTIVE RESPONSE \u00b7 ENDPOINT", TINY, GREEN, (8, 30, 18), GREEN)
    tx, ty, tw, th = x + 12, y + 94, w - 24, 78
    rrect(d, (tx, ty, tx + tw, ty + th), 9, fill=(5, 8, 14), outline=BORDER)
    d.text((tx + 10, ty + 8), "$ sudo iptables -L INPUT -n -v", font=MONO, fill=TEXT)
    d.text((tx + 10, ty + 30), "DROP  all -- 192.168.56.133", font=MONO_B, fill=RED)
    d.text((tx + 10, ty + 52), "0.0.0.0/0  ->  BLOCKED", font=MONO, fill=GREEN)
    if lt > 0.3:
        size = int(18 + 6 * ease((lt - 0.3) / 0.4))
        stamp(base, "BLOCKED", (x + w // 2, y + 218), size, GREEN, -8)
    d.text((x + 14, y + 270), "0.84s" if lt > 0.45 else "--", font=BIG, fill=GREEN)
    d.text((x + 14, y + 314), "MTTC < 3s", font=BODY_B, fill=GREEN)
    if lt > 0.52:
        sx, sy, sw, sh = x + 12, y + 330, w - 24, 90
        rrect(d, (sx, sy, sx + sw, sy + sh), 9, fill=(24, 17, 38), outline=(88, 28, 135))
        d.text((sx + 10, sy + 8), "#soc-alerts", font=BODY_B, fill=(216, 180, 254))
        d.text((sx + sw - 10, sy + 8), "Slack", font=TINY, fill=MUTED, anchor="ra")
        lines = [("SOAR alert \u00b7 Rule 5712", TEXT), ("Action: firewall-drop", GREEN), ("User: labuser \u00b7 T1110", MUTED)]
        for i, (s, c) in enumerate(lines):
            d.text((sx + 10, sy + 30 + i * 18), fit(s, SMALL, sw - 20), font=SMALL, fill=c)


def timeline(base, p, active):
    d = ImageDraw.Draw(base)
    x0, x1 = 28, W - 28
    y = 596
    d.line((x0, y, x1, y), fill=(30, 41, 59), width=8)
    if p > 0:
        d.line((x0, y, x0 + (x1 - x0) * p, y), fill=CYAN, width=8)
    labels = ["ATTACK", "DETECT", "DECIDE", "CONTAIN"]
    for i, lab in enumerate(labels):
        mx = x0 + (x1 - x0) * (i / 3)
        on = active >= i
        d.ellipse((mx - 6, y - 6, mx + 6, y + 6), fill=CYAN if on else (30, 41, 59), outline=(15, 23, 42), width=2)
        d.text((mx, y + 16), lab, font=TINY, fill=TEXT if on else MUTED, anchor="ma")
    stage_names = ["ATTACK", "WAZUH CORRELATION", "SOAR DECISION", "CONTAINMENT"]
    d.text((x0, 566), f"STAGE {min(active + 1, 4)}/4 \u00b7 {stage_names[active]}", font=SMALL, fill=MUTED)
    d.text((x1, 566), f"T+{p * 10:04.1f}s", font=MONO_B, fill=CYAN, anchor="ra")
    d.text((x0, 650), "github.com/Alliiiiii/soar-workflow-automation", font=SMALL, fill=DIM)
    d.text((x1, 650), "ISOLATED LAB \u00b7 192.168.56.0/24", font=TINY, fill=DIM, anchor="ra")


def build():
    bg = make_bg()
    frames = []
    for f in range(N):
        p = f / (N - 1)
        active = min(3, int(p / 0.2375)) if p < 0.95 else 3
        base = bg.copy()
        header(base, p)
        rail(base, p, active)
        for i in range(4):
            start = i * 0.2375
            end = start + 0.2375
            lt = clamp((p - start) / 0.2375)
            is_active = active == i and p < 0.95
            done = p >= end
            x = 36 + i * (264 + 24)
            card(base, x, 118, 264, 424, i, is_active, done, lt)
            if i == 0:
                stage1(base, x, 118, 264, 424, lt)
            elif i == 1:
                stage2(base, x, 118, 264, 424, lt)
            elif i == 2:
                stage3(base, x, 118, 264, 424, lt)
            else:
                stage4(base, x, 118, 264, 424, lt)
        timeline(base, p, active)
        frames.append(base.convert("RGB"))
    pal = [fr.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for fr in frames]
    pal[0].save(
        OUT,
        save_all=True,
        append_images=pal[1:],
        duration=DURATION,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024 / 1024:.2f} MiB, {N} frames, {FPS} fps)")


if __name__ == "__main__":
    build()
