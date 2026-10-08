#!/usr/bin/env python3
"""Generate images/linkedin-cover.png.

Usage:  python3 scripts/linkedin_cover.py [variant ...]
  With no arguments, renders the published design (PUBLISHED) straight to
  images/linkedin-cover.png. Set OUT=path to write somewhere else. Other
  variants are written to local/banner-variants/ (git-ignored).
  Needs Pillow and numpy; fonts are downloaded on first run to
  ~/.cache/spitfiresatya-banner-fonts (override with BANNER_FONTS).
  The Menlo fallback for ∅ ∪ ∩ means it renders correctly only on macOS.

LinkedIn cover variants that drop the name/headline (LinkedIn renders those
directly below the cover) and instead present the career as a rewrite.

Variants:
  trace  - a vertical reduction trace, one career step per line
  chain  - a horizontal reduction sequence, left to right
  type   - one inference rule: credentials as premises, a typing judgment below

Layout math is in logical px (1584x396); fonts are built at size*S.
LinkedIn's avatar overlaps roughly x<240, y>250, so content stays clear of it.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, S = 1584, 396, 3
CW, CH = W * S, H * S
FONT_URLS = {
    "JetBrainsMono.ttf": "ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
    "Inter.ttf": "ofl/inter/Inter%5Bopsz,wght%5D.ttf",
    "SpaceGrotesk.ttf": "ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf",
}
F = os.environ.get("BANNER_FONTS",
                   os.path.expanduser("~/.cache/spitfiresatya-banner-fonts"))


def ensure_fonts():
    """The site's fonts come from Google Fonts and aren't installed locally;
    fetch the variable TTFs once into a cache directory."""
    import urllib.request
    os.makedirs(F, exist_ok=True)
    for name, path in FONT_URLS.items():
        dest = os.path.join(F, name)
        if not os.path.exists(dest):
            url = "https://github.com/google/fonts/raw/main/" + path
            print("downloading", url)
            urllib.request.urlretrieve(url, dest)

TL, TR = (0x09, 0x5e, 0x7b), (0x2f, 0x2f, 0x90)
BLc, BRc = (0x10, 0x19, 0x42), (0x24, 0x31, 0x80)
CYAN = (0x0c, 0xb0, 0xd8)
WHITE = (0xff, 0xff, 0xff)
CODE = (0xe3, 0xec, 0xfa)
MUTED = (0x9d, 0xb0, 0xd8)
DIM = (0x7d, 0x90, 0xb8)
NAVY = (0x13, 0x1c, 0x42)


def mono(size, weight=400):
    f = ImageFont.truetype(f"{F}/JetBrainsMono.ttf", int(size * S))
    f.set_variation_by_axes([weight])
    return f


def build(variant):
    # derive variants differ only in brand mark and background texture
    ROSE_200 = (0xfe, 0xcd, 0xd3)   # site's dark-theme --accent-red-deep
    ROSE_400 = (0xfb, 0x71, 0x85)   # same family, more saturated
    DERIVE_OPTS = {
        "derive":        dict(mark="crescent", grid=False, url=None),
        "derive-nomark": dict(mark=None,       grid=False, url=None),
        "derive-stamp":  dict(mark="stamp",    grid=False, url=None),
        "derive-grid":   dict(mark=None,       grid=True,  url=None),
        "derive-both":   dict(mark="stamp",    grid=True,  url=None),
        "derive-url":    dict(mark=None,       grid=True,  url=ROSE_200),
        "derive-url-hot": dict(mark=None,      grid=True,  url=ROSE_400),
        # grid dropped: at 23% relative brightness it competed with the
        # starfield, and the stars are brand (favicon.svg carries three)
        "final":         dict(mark=None,       grid=False, url=ROSE_400),
    }
    DERIVE_OPTS["aurora"] = dict(mark=None, grid=False, url=ROSE_400)
    # og-card mark + a sparser starfield: the card reads cleaner than a dense sky
    DERIVE_OPTS["emerald"] = dict(mark="ogcard", grid=False, url=ROSE_400,
                                  stars=60)
    DERIVE_OPTS["sparse"] = dict(mark="ogcard", grid=False, url=ROSE_400,
                                 stars=22)
    DERIVE_OPTS["minimal"] = dict(mark="ogcard", grid=False, url=ROSE_400,
                                  stars=9)
    # mark alternatives to the og-card eclipse, same background and stars
    for name, mark in (("mark-moon", "moon"), ("mark-moonstars", "moonstars"),
                       ("mark-tile", "stamp"), ("mark-none", None)):
        DERIVE_OPTS[name] = dict(DERIVE_OPTS["minimal"], mark=mark,
                                 tile_px=56, tile_at=(124, 56))
    # astral backgrounds in place of a brand mark
    for name, feats in (("astro-blackhole", {"disk"}), ("astro-nebula", {"nebula"}),
                        ("astro-both", {"nebula", "disk"}),
                        ("astro-webb", {"cliffs", "spikes"}),
                        ("astro-lensed", {"nebula", "lens"}),
                        ("astro-trails", {"trails"}),
                        ("astro-gargantua", {"nebula", "lens", "disk", "spikes"}),
                        ("astro-cliffs-hole", {"cliffs", "spikes", "disk"}),
                        ("astro-trails-spikes", {"trails", "spikes"}),
                        ("astro-cliffs-trails", {"cliffs", "trails"}),
                        ("astro-m78", {"m78"})):
        DERIVE_OPTS[name] = dict(DERIVE_OPTS["minimal"], mark=None, astro=feats)
    # trails replace the static stars: a point star contradicts a long exposure
    for name in ("astro-trails", "astro-trails-spikes", "astro-cliffs-trails",
                 "astro-m78"):
        DERIVE_OPTS[name]["stars"] = 0
    # black hole hung above the right-hand crags
    DERIVE_OPTS["astro-cliffs-hole"]["bh"] = (1474, 112, 26)
    DERIVE_OPTS["astro-cliffs-hole"]["spike_stars"] = [
        (118, 64, 1.0), (1392, 330, 0.55), (196, 168, 0.45), (1556, 262, 0.4)]
    # landscape astrophotography: the pole sits low over the crags
    DERIVE_OPTS["astro-cliffs-trails"]["pole"] = (1480, 120)
    base = ("derive" if variant.startswith(("derive", "mark-", "astro-"))
            or variant in ("final", "aurora", "emerald", "sparse", "minimal")
            else variant)
    opts = DERIVE_OPTS.get(variant, DERIVE_OPTS["derive"])

    def site_night_sky():
        """Faithful reproduction of the site's dark-mode background from
        _sass/_custom.scss: deep-navy canvas, five aurora curtains, and three
        tiled star layers. CSS lists topmost first, so composite in reverse."""
        arr = np.zeros((CH, CW, 3)) + np.array([0x07, 0x0d, 0x20], float)
        REM = 16.0
        # (w_rem, h_rem, x%, y%, rgb, alpha, transparent-stop)
        curtains = [
            (50, 40, 12, -6, (34, 197, 94), 0.34, 0.62),
            (46, 38, 92, 4, (16, 185, 129), 0.30, 0.62),
            (52, 44, 70, 96, (20, 184, 166), 0.26, 0.60),
            (40, 34, 16, 104, (52, 211, 153), 0.24, 0.60),
            (46, 40, 46, 44, (6, 182, 212), 0.20, 0.62),
        ]
        # (tile_w, tile_h, off_x, off_y, dot_r, rgb, alpha)
        stars = [
            (150, 150, 12, 24, 1.1, (255, 255, 255), 0.95),
            (91, 103, 43, 9, 0.9, (255, 255, 255), 0.75),
            (57, 61, 71, 37, 0.7, (214, 232, 255), 0.55),
        ]
        yy, xx = np.mgrid[0:CH, 0:CW].astype(float)

        for tw, th, ox, oy, dr, rgb, a in reversed(stars):
            m = Image.new("L", (CW, CH), 0)
            md = ImageDraw.Draw(m)
            r = dr * S
            gx = (ox + tw / 2.0) * S
            while gx < CW + tw * S:
                gy = (oy + th / 2.0) * S
                while gy < CH + th * S:
                    md.ellipse([gx - r, gy - r, gx + r, gy + r], fill=255)
                    gy += th * S
                gx += tw * S
            mk = (np.asarray(m, float) / 255.0) * a
            for i in range(3):
                arr[:, :, i] = arr[:, :, i] * (1 - mk) + rgb[i] * mk

        for w, h, px, py, rgb, a, stop in reversed(curtains):
            cx, cy = px / 100.0 * CW, py / 100.0 * CH
            rx, ry = w * REM * S / 2.0, h * REM * S / 2.0
            rad = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
            mk = np.clip(1.0 - rad / stop, 0, 1) * a
            for i in range(3):
                arr[:, :, i] = arr[:, :, i] * (1 - mk) + rgb[i] * mk
        return arr

    fy, fx = np.mgrid[0:CH, 0:CW]
    fx, fy = fx / (CW - 1), fy / (CH - 1)
    bg = np.zeros((CH, CW, 3))
    for i in range(3):
        bg[:, :, i] = ((TL[i] * (1 - fx) + TR[i] * fx) * (1 - fy)
                       + (BLc[i] * (1 - fx) + BRc[i] * fx) * fy)
    core = np.exp(-(((fx - 0.46) ** 2) / .1352 + ((fy - 0.58) ** 2) / .5408))
    for i, a in enumerate((16, 36, 54)):
        bg[:, :, i] -= a * core
    # Teal light source, softened and pulled inward. It used to peak at (79,47)
    # — an empty corner — creating a focal point that competed with the type.
    # Broad and dim now, so the brightest thing in the frame is the text.
    glow = np.exp(-(((fx - 0.12) ** 2) / .1152 + ((fy - 0.20) ** 2) / .4232))
    # "emerald" borrows the hue of the site's dark-mode aurora curtains
    # (green-500 / emerald-500) without inheriting their viewport-tall geometry
    glow_amt = (6, 42, 25) if variant == "emerald" else (6, 36, 46)
    for i, a in enumerate(glow_amt):
        bg[:, :, i] += a * glow
    if variant == "emerald":
        # bottom curtain pulled to centre-left: at (0.80, 1.05) it sat directly
        # behind the URL and dropped rose-400 to 3.61:1, under AA
        curtain = np.exp(-(((fx - 0.52) ** 2) / .16 + ((fy - 1.20) ** 2) / .26))
        for i, a in enumerate((5, 34, 21)):
            bg[:, :, i] += a * curtain
    bloom = np.exp(-(((fx - 1.0) ** 2) / .08 + ((fy - 0.38) ** 2) / .5408))
    for i, a in enumerate((28, 18, 64)):
        bg[:, :, i] += a * bloom

    astro = set(opts.get("astro") or ()) if base == "derive" else set()
    # logical-pixel coordinates for the astral layers
    LXg, LYg = fx * (W - 1), fy * (H - 1)
    # the text block (rule grid, closing line, caption, URL) in logical px
    TXT = (237, 40, 1347, 376)

    def outside_text(soft=60.0):
        """0 inside the text block, rising to 1 within `soft` px outside it."""
        x0, y0, x1, y1 = TXT
        ddx = np.maximum(np.maximum(x0 - LXg, LXg - x1), 0)
        ddy = np.maximum(np.maximum(y0 - LYg, LYg - y1), 0)
        return np.clip(np.hypot(ddx, ddy) / soft, 0, 1)

    def fbm(seed, base_cells, octaves=5, gain=0.55):
        """Fractal value noise in [0, 1]: random grids upsampled bicubically
        (no scipy here), summed over octaves."""
        r = np.random.default_rng(seed)
        acc = np.zeros((CH, CW))
        amp, tot = 1.0, 0.0
        for o in range(octaves):
            gw = int(base_cells * 2 ** o) + 2
            gh = max(2, int(gw * H / W) + 2)
            g = Image.fromarray(r.random((gh, gw)).astype(np.float32), "F")
            acc += amp * np.asarray(g.resize((CW, CH), Image.BICUBIC), float)
            tot += amp
            amp *= gain
        acc /= tot
        return np.clip((acc - acc.min()) / (acc.max() - acc.min()), 0, 1)

    def screen(arr, rgb_layer):
        """Screen blend: adds light without ever darkening or clipping hard."""
        return 255 - (255 - arr) * (255 - np.clip(rgb_layer, 0, 255)) / 255.0

    def noise1d(seed, cells, octaves=6):
        r = np.random.default_rng(seed)
        acc, amp, tot = np.zeros(CW), 1.0, 0.0
        for o in range(octaves):
            n = int(cells * 2 ** o) + 2
            pts = r.random(n)
            u = np.linspace(0, n - 1, CW)
            i0 = np.floor(u).astype(int).clip(0, n - 2)
            f = u - i0
            f = f * f * (3 - 2 * f)
            acc += amp * (pts[i0] * (1 - f) + pts[i0 + 1] * f)
            tot += amp
            amp *= 0.5
        return acc / tot

    if "cliffs" in astro:
        # After Webb's "Cosmic Cliffs" (NGC 3324): a ridge of dust lit along
        # its edge, glowing gas rising above it. The ridge stays flat at the
        # divider under the text and rises into peaks in the empty margins,
        # so the closing derivation sits on dark dust.
        xs = np.arange(CW) / S
        jag = noise1d(71, 7) - 0.5
        rise = np.clip((np.abs(xs - 792) - 545) / 250, 0, 1) ** 1.25
        # asymmetric, like the real cliffs: tall crags on the right, a lower
        # shoulder on the left (which LinkedIn's avatar mostly covers anyway)
        rise *= np.where(xs < 792, 0.6, 1.0)
        crag = noise1d(75, 64, 4) - 0.5
        ridge = (298 + 22 * jag + 110 * rise * crag
                 - 140 * rise * (0.75 + 0.5 * noise1d(73, 3)))
        ry = ridge[None, :]
        below = np.clip((LYg - ry) / 2.5, 0, 1)
        tex = fbm(79, 6, octaves=5)
        dust = below * (0.62 - 0.22 * tex)
        dust_col = np.array([14, 14, 40], float)
        bg = bg * (1 - dust[..., None]) + dust_col * dust[..., None]
        cliff_mask = below
        # wisps of lit dust inside the cliff face
        wisp = below * np.exp(-(LYg - ry) / 38) * np.clip(tex - 0.45, 0, 1) * 1.6
        bg = screen(bg, np.array([40, 120, 170.]) * wisp[..., None])
        above = np.clip((ry - LYg), 0, None)
        rim = (np.exp(-(above / 1.6) ** 2) * 0.75 + np.exp(-above / 16) * 0.22) * (1 - below)
        rim *= 0.6 + 0.8 * np.clip(noise1d(83, 20, 4)[None, :] - 0.3, 0, 1)
        bg = screen(bg, np.array([150, 225, 250.]) * rim[..., None])
        # ionised gas streaming up off the ridge, in vertical streaks
        r = np.random.default_rng(89)
        g = Image.fromarray(r.random((4, 140)).astype(np.float32), "F")
        streak = np.asarray(g.resize((CW, CH), Image.BICUBIC), float)
        gas = np.exp(-above / 70) * (1 - below) * np.clip(streak, 0, 1) ** 2
        gas *= 0.12 + 0.88 * outside_text(70)
        bg = screen(bg, np.array([40, 150, 200.]) * gas[..., None] * 0.55)

    if "m78" in astro:
        # After M78-style reflection/emission nebulae: near-black space,
        # saturated violet-magenta clouds with lavender-white cores, blue
        # reflection lobes, and sharp dark dust lanes cutting through.
        # Replaces the brand gradient entirely.
        space = np.array([5, 4, 14], float)
        bg = np.zeros((CH, CW, 3)) + space
        # cloud masses: one big diagonal sweep plus two margin lobes
        def blob(x, y, sx, sy, a=0.0):
            ca, sa = np.cos(a), np.sin(a)
            u = ((LXg - x) * ca + (LYg - y) * sa) / sx
            v = (-(LXg - x) * sa + (LYg - y) * ca) / sy
            return np.exp(-(u * u + v * v))
        shape = (0.9 * blob(105, 120, 210, 140, 0.5)
                 + 1.0 * blob(1430, 170, 300, 170, -0.4)
                 + 0.55 * blob(800, 210, 700, 120, -0.18))
        n1 = fbm(211, 3, octaves=6, gain=0.58)
        n2 = fbm(223, 6, octaves=5, gain=0.6)
        dens = shape * (0.55 + 1.8 * np.clip(n1 - 0.25, 0, 1)) * (0.6 + 0.9 * n2)
        # bright cores where density peaks
        core = np.clip(dens - 0.45, 0, None) ** 1.2 * 2.2
        # dust: thin dark filaments from ridged noise, strongest at cloud edges
        # dust: broad feathery patches (thresholded fbm) plus a few soft
        # filaments; thin ridged lines alone read as cracks, not dust
        patch = np.clip((fbm(233, 5, octaves=6, gain=0.62) - 0.56) / 0.16, 0, 1) ** 1.5
        fil = (1 - np.abs(2 * fbm(241, 3, octaves=6, gain=0.65) - 1)) ** 4
        fil *= np.clip((fbm(247, 4, octaves=3) - 0.45) / 0.2, 0, 1)
        absorb = np.clip(0.85 * patch + 0.45 * fil, 0, 0.88) * np.clip(dens / 0.6, 0, 1)
        dens *= 1 - absorb
        core *= 1 - absorb
        # scrim: the type sits in a calmer, darker pocket of the cloud
        scrim = 0.32 + 0.68 * outside_text(110)
        dens *= scrim
        core *= scrim ** 3
        # reflection (blue) vs emission (magenta) regions
        refl = np.clip((fbm(251, 2, octaves=3) - 0.42) / 0.3, 0, 1)
        # keep the rose URL the only warm colour: the cloud turns blue around
        # the bottom-right corner, magenta survives higher up
        near_url = np.exp(-(((LXg - 1290) / 330) ** 2 + ((LYg - 372) / 150) ** 2))
        refl = np.maximum(refl, np.clip(near_url * 1.4, 0, 1))
        violet = np.array([70, 22, 120], float)
        magenta = np.array([200, 55, 200], float)
        blue = np.array([70, 95, 255], float)
        lav = np.array([238, 222, 255], float)
        t = np.clip(dens / 0.9, 0, 1)[..., None]
        hot = violet * (1 - t) + magenta * t
        col = hot * (1 - refl[..., None]) + blue * refl[..., None]
        light = col * np.clip(dens, 0, 1.2)[..., None] * 1.25
        bg = screen(bg, light)
        bg = screen(bg, lav * np.clip(core, 0, 1)[..., None] * 0.85)
        # a dense, varied starfield baked in: warm, white and blue stars with a
        # power-law brightness, thinned behind the type
        r = np.random.default_rng(263)
        tint = [np.array(c, float) for c in
                ((255, 214, 170), (255, 245, 235), (205, 220, 255), (255, 190, 140))]
        n_st = opts.get("m78_stars", 900)
        for _ in range(n_st):
            x, y = r.uniform(0, W), r.uniform(0, H)
            inside = TXT[0] - 8 < x < TXT[2] + 8 and TXT[1] - 8 < y < TXT[3] + 4
            if inside and r.uniform() > 0.12:
                continue
            b = r.pareto(2.0) * 0.35 + 0.14
            b = min(b, 1.0) * (0.45 if inside else 1.0)
            rad = 0.45 + 1.4 * b
            win = int(np.ceil(rad * 3 + 2))
            x0, x1 = max(0, int((x - win) * S)), min(CW, int((x + win) * S))
            y0, y1 = max(0, int((y - win) * S)), min(CH, int((y + win) * S))
            if x0 >= x1 or y0 >= y1:
                continue
            wy, wx = np.mgrid[y0:y1, x0:x1].astype(float)
            g = np.exp(-(((wx / S - x) ** 2 + (wy / S - y) ** 2) / (rad * rad * 0.6)))
            c = tint[r.integers(len(tint))]
            bg[y0:y1, x0:x1] = screen(bg[y0:y1, x0:x1], c * np.clip(g * b * 1.6, 0, 1)[..., None])
        # a few bright stars with the classic four-point cross, as in the
        # reference (a Newtonian telescope's spider vanes)
        for x, y, b in opts.get("cross_stars", [(96, 52, 1.0), (1500, 64, 0.85),
                                                (1388, 318, 0.6), (210, 178, 0.5),
                                                (1560, 250, 0.45)]):
            L = 34 * b
            Rw = L * 3
            x0, x1 = int(max(0, (x - Rw) * S)), int(min(CW, (x + Rw) * S))
            y0, y1 = int(max(0, (y - Rw) * S)), int(min(CH, (y + Rw) * S))
            wy, wx = np.mgrid[y0:y1, x0:x1].astype(float)
            ddx, ddy = wx / S - x, wy / S - y
            acc = (np.exp(-np.abs(ddx) / L) * np.exp(-(ddy / 0.5) ** 2)
                   + np.exp(-np.abs(ddy) / L) * np.exp(-(ddx / 0.5) ** 2))
            rr2 = ddx ** 2 + ddy ** 2
            acc += 1.5 * np.exp(-rr2 / (2.0 * b + 0.4)) + 0.3 * np.exp(-rr2 / (50 * b))
            bg[y0:y1, x0:x1] = screen(bg[y0:y1, x0:x1],
                                      np.array([240, 235, 255.]) * np.clip(acc * b, 0, 1)[..., None])

    if "nebula" in astro:
        dens = fbm(11, 3)
        hue = fbm(23, 2, octaves=3)
        dust = fbm(37, 5, octaves=4)
        # ridged noise gives the filaments; plain fbm gives the soft body
        ridge = (1 - np.abs(2 * fbm(53, 4, octaves=5, gain=0.6) - 1)) ** 5
        body = np.clip((dens - 0.40) / 0.60, 0, 1) ** 1.4
        cloud = body * (0.45 + 1.6 * ridge)
        # dark dust lanes cut through the glow
        cloud *= np.clip(1.2 - 2.6 * np.clip(dust - 0.52, 0, 1), 0.1, 1)
        # full strength in the margins, a quarter of it behind the type
        cloud *= 0.25 + 0.75 * outside_text(90)
        teal = np.array([20, 170, 175], float)
        violet = np.array([120, 80, 220], float)
        mix = np.clip((hue - 0.35) / 0.3, 0, 1)[..., None]
        col = teal * (1 - mix) + violet * mix
        bg = screen(bg, col * np.clip(cloud, 0, 1.3)[..., None] * opts.get("neb_amt", 0.8))

    BH = opts.get("bh", (1468, 170, 30))      # centre x, y and horizon radius
    if "lens" in astro:
        # Gravitational lensing done for real: every pixel near the hole
        # samples the background at its point-lens source position
        # beta = theta * (1 - theta_E^2 / |theta|^2). A galaxy sitting almost
        # exactly behind the hole is smeared into an Einstein ring, and the
        # nebula and background stars bend around it.
        cx, cy, rh = BH
        thE = 1.9 * rh
        R = 6.5 * rh
        rr = np.random.default_rng(97)
        # faint background stars inside the lens window, baked into the array
        # so they get lensed into arcs
        for _ in range(26):
            a, rad = rr.uniform(0, 2 * np.pi), rr.uniform(0.6, 1.0) * R
            sx_, sy_ = cx + rad * np.cos(a), cy + rad * np.sin(a)
            amp = rr.uniform(60, 170)
            dot = np.exp(-(((LXg - sx_) ** 2 + (LYg - sy_) ** 2) / 0.9))
            bg = screen(bg, np.array([235, 242, 255.]) * (amp / 255) * dot[..., None])
        gx_, gy_ = cx + 0.32 * rh, cy - 0.12 * rh
        gal = np.exp(-(((LXg - gx_) / (0.34 * rh)) ** 2 + ((LYg - gy_) / (0.22 * rh)) ** 2))
        bg = screen(bg, np.array([150, 215, 255.]) * gal[..., None] * 0.95)
        x0, x1 = int(max(0, (cx - R) * S)), int(min(CW, (cx + R) * S))
        y0, y1 = int(max(0, (cy - R) * S)), int(min(CH, (cy + R) * S))
        sy, sx = np.mgrid[y0:y1, x0:x1].astype(float)
        tx_, ty_ = sx / S - cx, sy / S - cy
        t2 = tx_ ** 2 + ty_ ** 2 + 1e-6
        # deflection fades out at the window edge so there is no seam
        fade = np.clip((R - np.sqrt(t2)) / (2.0 * rh), 0, 1)
        k = 1 - fade * thE ** 2 / t2
        si = np.clip(((cy + ty_ * k) * S).round().astype(int), 0, CH - 1)
        sj = np.clip(((cx + tx_ * k) * S).round().astype(int), 0, CW - 1)
        bg[y0:y1, x0:x1] = bg[si, sj]
        if "disk" not in astro:
            dd = np.hypot(LXg - cx, LYg - cy)
            shadow = np.clip((rh - dd) / (0.05 * rh), 0, 1)
            bg *= (1 - 0.97 * shadow)[..., None]
            ring = 0.5 * np.exp(-((dd - 1.03 * rh) / (0.035 * rh)) ** 2)
            bg = screen(bg, np.array([200, 235, 255.]) * ring[..., None])
    if "disk" in astro:
        cx, cy, rh = BH
        dx, dy = LXg - cx, LYg - cy
        dd = np.hypot(dx, dy)
        tilt = 0.11                             # cos of the viewing inclination
        re = np.hypot(dx, dy / tilt)            # radius in the disk plane
        r_in, r_out = 1.5 * rh, 3.9 * rh
        disk = np.where(re > r_in, (r_in / np.maximum(re, 1e-3)) ** 1.6, 0.0)
        disk *= np.clip((re - r_in) / (0.25 * rh), 0, 1)
        disk *= np.clip((r_out - re) / (1.6 * rh), 0, 1)
        # relativistic beaming: the approaching (left) side is brighter
        disk *= 1 + 0.4 * np.clip(-dx / np.maximum(re, 1e-3), -1, 1)
        # far half of the disk is hidden behind the shadow
        disk *= np.where((dy < 0) & (dd < rh * 1.02), 0.0, 1.0)
        # the far side of the disk, lensed up over (and faintly under) the hole
        # Interstellar-style: a wide arc over the top, a thinner one beneath,
        # both fading toward the sides where they meet the disk
        sin_t = -dy / np.maximum(dd, 1e-3)      # +1 straight up, -1 straight down
        top = np.clip(sin_t, 0, 1) ** 0.7
        bot = np.clip(-sin_t, 0, 1) ** 1.2
        lens = (np.exp(-((dd - 1.30 * rh) / (0.20 * rh)) ** 2) * top * 1.0
                + np.exp(-((dd - 1.12 * rh) / (0.10 * rh)) ** 2) * bot * 0.6)
        lens *= 1 + 0.35 * np.clip(-dx / np.maximum(dd, 1e-3), -1, 1)
        ring = 0.45 * np.exp(-((dd - 1.03 * rh) / (0.03 * rh)) ** 2)
        halo = 0.12 * np.exp(-(dd / (3.4 * rh)) ** 2)
        inten = np.clip(disk * 1.1 + lens + ring + halo, 0, 1.4)
        # the shadow itself: darken first, then let the near disk pass over it
        shadow = np.clip((rh * 1.0 - dd) / (0.06 * rh), 0, 1)
        front = (dy > 0) * np.clip(disk * 3, 0, 1)
        bg *= (1 - shadow * (1 - np.clip(front * 1.5, 0, 1)) * 0.96)[..., None]
        # colour ramp: indigo-blue at the edge, cyan, then white-hot
        c_lo = np.array([60, 110, 230], float)
        c_mid = np.array([80, 215, 245], float)
        c_hi = np.array([250, 252, 255], float)
        t1 = np.clip(inten / 0.55, 0, 1)[..., None]
        t2 = np.clip((inten - 0.55) / 0.6, 0, 1)[..., None]
        col = c_lo * (1 - t1) + c_mid * t1
        col = col * (1 - t2) + c_hi * t2
        bg = screen(bg, col * np.clip(inten, 0, 1)[..., None])

    if "spikes" in astro:
        # Webb's signature: six spikes from the hexagonal mirror segments
        # (vertical and +/-60 deg from it) plus a faint horizontal pair from
        # the vertical strut. Only a handful of bright stars, all in margins.
        bright = opts.get("spike_stars",
                          [(118, 64, 1.0), (1528, 46, 0.75), (1392, 330, 0.55),
                           (196, 168, 0.45), (1556, 262, 0.4)])
        for sx_, sy_, b in bright:
            L = 46 * b
            Rw = L * 3.2
            x0, x1 = int(max(0, (sx_ - Rw) * S)), int(min(CW, (sx_ + Rw) * S))
            y0, y1 = int(max(0, (sy_ - Rw) * S)), int(min(CH, (sy_ + Rw) * S))
            wy, wx = np.mgrid[y0:y1, x0:x1].astype(float)
            ddx, ddy = wx / S - sx_, wy / S - sy_
            acc = np.zeros(ddx.shape)
            for ang, ln, amp, w in ((90, 1.0, 1.0, 0.55), (30, 1.0, 1.0, 0.55),
                                    (150, 1.0, 1.0, 0.55), (0, 0.45, 0.55, 0.45)):
                a = np.deg2rad(ang)
                along = np.abs(np.cos(a) * ddx + np.sin(a) * ddy)
                perp = np.abs(-np.sin(a) * ddx + np.cos(a) * ddy)
                acc += amp * np.exp(-along / (L * ln)) * np.exp(-(perp / w) ** 2)
            rr2 = ddx ** 2 + ddy ** 2
            acc += 1.4 * np.exp(-rr2 / (2.2 * b + 0.4)) + 0.25 * np.exp(-rr2 / (60 * b))
            layer = np.array([225, 238, 255.]) * np.clip(acc * b, 0, 1)[..., None]
            bg[y0:y1, x0:x1] = screen(bg[y0:y1, x0:x1], layer)

    if "trails" in astro:
        # A long exposure around the celestial pole, placed in the empty right
        # margin. Every trail spans the same angle, as it must for one
        # exposure time, so the whole field reads as one  ->*  of the sky.
        pcx, pcy = opts.get("pole", (1468, 170))
        dxp, dyp = LXg - pcx, LYg - pcy
        rad = np.hypot(dxp, dyp)
        phi = np.arctan2(dyp, dxp)
        r = np.random.default_rng(131)
        span = np.deg2rad(opts.get("trail_deg", 24))
        pmin, pmax = -np.pi, np.pi
        rmin, rmax = 6, np.hypot(pcx, H - pcy)
        acc = np.zeros((CH, CW))
        for _ in range(opts.get("n_trails", 650)):
            # weighted toward the pole so the vortex reads in the margin
            r0 = rmin + (rmax - rmin) * r.uniform(0, 1) ** 2.2
            p0 = r.uniform(pmin, pmax)
            amp = r.uniform(0.15, 0.9) ** 2
            band = np.abs(rad - r0) < 2.5
            if not band.any():
                continue
            u = np.mod(phi[band] - p0, 2 * np.pi) / span
            taper = np.where(u <= 1, np.clip(np.minimum(u, 1 - u) / 0.08, 0, 1), 0.0)
            acc[band] += amp * np.exp(-((rad[band] - r0) / 0.6) ** 2) * taper
        acc *= 0.12 + 0.88 * outside_text(50)
        if "cliffs" in astro:
            acc *= 1 - cliff_mask          # the ridge hides the sky behind it
        bg = screen(bg, np.array([200, 225, 255.]) * np.clip(acc, 0, 1)[..., None])

    # graph-paper texture, added to the background array so it genuinely blends
    if base == "derive" and opts["grid"]:
        step = 44 * S
        for gx in range(0, CW, step):
            bg[:, gx:gx + S, :] += 11
        for gy in range(0, CH, step):
            bg[gy:gy + S, :, :] += 11

    if variant == "aurora":
        bg = site_night_sky()

    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(img)

    def circle(cx, cy, r, fill):
        d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=fill)

    def tx(x, baseline, s, f, col, align="l"):
        w = f.getlength(s) / S
        if align == "c":
            x -= w / 2
        elif align == "r":
            x -= w
        d.text((x * S, baseline * S), s, font=f, fill=col, anchor="ls")
        return w

    def capH(f):
        bb = f.getbbox("T")
        return (bb[3] - bb[1]) / S

    def turnstile(x, baseline, f, col):
        adv = f.getlength("0") / S
        ch = capH(f)
        lw = max(1, int(2.0 * S))
        bx = x + adv * 0.26
        d.line([bx * S, (baseline - ch) * S, bx * S, baseline * S], fill=col, width=lw)
        d.line([bx * S, (baseline - ch * 0.52) * S,
                (bx + adv * 0.5) * S, (baseline - ch * 0.52) * S], fill=col, width=lw)
        return adv

    # --- starfield (kept off the content band) -----------------------------
    rng = np.random.default_rng(5)
    placed = 0
    # the aurora background brings the site's own tiled star layers
    target = (0 if variant == "aurora" else
              opts.get("stars", 70 if (base == "derive" and opts["grid"]) else 150))
    while placed < target:
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if base == "trace" and 430 < x < 1140 and 95 < y < 345:
            continue
        if base == "chain" and 255 < x < 1540 and 150 < y < 250:
            continue
        if base == "derive" and 235 < x < 1355 and 36 < y < 392:
            continue
        if astro & {"disk", "lens"} and np.hypot(x - BH[0], y - BH[1]) < 4.6 * BH[2]:
            continue
        if base == "rules" and 300 < x < 1290 and 80 < y < 365:
            continue
        if base == "type" and 300 < x < 1290 and 140 < y < 265:
            continue
        # og-card's stars are small specks; keep them under ~1.6px
        rmax = 1.6 if base == "derive" and opts.get("stars", 99) <= 30 else 2.1
        circle(x, y, rng.uniform(0.7, rmax), (255, 255, 255, int(rng.uniform(45, 150))))
        placed += 1

    def favicon_tile(px):
        """Faithful render of images/favicon.svg: gradient rounded square,
        white crescent via mask, three stars."""
        n = int(px * S)
        k = n / 64.0
        gy, gx = np.mgrid[0:n, 0:n]
        t = ((gx / (n - 1)) + (gy / (n - 1))) / 2.0
        stops = [(0.0, (0x06, 0xb6, 0xd4)), (0.5, (0x3b, 0x82, 0xf6)),
                 (1.0, (0x4f, 0x46, 0xe5))]
        arr = np.zeros((n, n, 3))
        for j in range(2):
            (t0, c0), (t1, c1) = stops[j], stops[j + 1]
            m = (t >= t0) & (t <= t1)
            u = np.clip((t - t0) / (t1 - t0), 0, 1)
            for i in range(3):
                arr[:, :, i] = np.where(m, c0[i] * (1 - u) + c1[i] * u, arr[:, :, i])
        tile = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
        td = ImageDraw.Draw(tile)
        # crescent: white disc minus an offset disc
        cres = Image.new("L", (n, n), 0)
        cd = ImageDraw.Draw(cres)
        cd.ellipse([(30 - 15) * k, (32 - 15) * k, (30 + 15) * k, (32 + 15) * k], fill=255)
        cd.ellipse([(39 - 13) * k, (26 - 13) * k, (39 + 13) * k, (26 + 13) * k], fill=0)
        tile.paste(Image.new("RGBA", (n, n), (255, 255, 255, 255)), (0, 0), cres)
        for sx, sy, sr, sa in ((47, 15, 2.1, 255), (16, 16, 1.5, 217), (20, 48, 1.3, 178)):
            td.ellipse([(sx - sr) * k, (sy - sr) * k, (sx + sr) * k, (sy + sr) * k],
                       fill=(255, 255, 255, sa))
        # round the corners
        rc = Image.new("L", (n, n), 0)
        ImageDraw.Draw(rc).rounded_rectangle([0, 0, n - 1, n - 1], radius=14 * k, fill=255)
        tile.putalpha(rc)
        return tile

    if base != "derive" or opts["mark"] == "crescent":
        LX, LY, LR = 112, 74, 34
        circle(LX, LY, LR, (0xe8, 0xed, 0xff, 255))
        circle(LX + LR * 0.44, LY - LR * 0.08, LR * 0.93, NAVY + (255,))
    elif opts["mark"] == "ogcard":
        # Measured off images/og-card.png (pale r=29 at (149,150), occluder
        # r=25 at (168,138)) — the same proportions as favicon.svg's mask:
        # occluder radius 0.867r, offset (+0.6r, -0.4r). The vertical offset is
        # what makes it an eclipse rather than two circles side by side.
        LX, LY, LR = 152, 84, 28
        circle(LX, LY, LR, (0xec, 0xf0, 0xfd, 255))
        circle(LX + LR * 0.6, LY - LR * 0.4, LR * 0.867, (0x0e, 0x16, 0x38, 255))
    elif opts["mark"] in ("moon", "moonstars"):
        # favicon.svg's crescent as a real cut-out: the occluding disc is
        # erased from the mask, so the background shows through instead of a
        # navy disc that reads as an eclipse against the teal glow
        LX, LY, LR = 152, 84, 28
        m = Image.new("L", (W * S, H * S), 0)
        md = ImageDraw.Draw(m)
        md.ellipse([(LX - LR) * S, (LY - LR) * S, (LX + LR) * S, (LY + LR) * S], fill=255)
        ox, oy, orr = LX + LR * 0.6, LY - LR * 0.4, LR * 0.867
        md.ellipse([(ox - orr) * S, (oy - orr) * S, (ox + orr) * S, (oy + orr) * S], fill=0)
        img.paste(Image.new("RGBA", img.size, (0xec, 0xf0, 0xfd, 255)), (0, 0), m)
        if opts["mark"] == "moonstars":
            # favicon.svg's three stars, in its 64-unit frame scaled to the moon
            k = LR / 15.0
            for sx, sy, sr, sa in ((47, 15, 2.1, 255), (16, 16, 1.5, 217), (20, 48, 1.3, 178)):
                circle(LX + (sx - 30) * k, LY + (sy - 32) * k, sr * k * 0.8,
                       (255, 255, 255, sa))
    elif opts["mark"] == "stamp":
        px = opts.get("tile_px", 46)
        tile = favicon_tile(px)
        x0, y0 = opts.get("tile_at", (88, 50))
        img.alpha_composite(tile, (int(x0 * S), int(y0 * S)))

    STEPS = [
        ("software developer",     "TCS",          "2015"),
        ("code auditor",           "TCS",          "2018"),
        ("M.S. Cybersecurity",     "Northeastern", "2019"),
        ("Ph.D. Computer Science", "Northeastern", "2021"),
        ("applied scientist",      "AWS",          "2025"),
    ]

    if variant == "trace":
        f_term, f_an = mono(24, 500), mono(16, 500)
        f_ar = mono(24, 600)
        # centre the whole two-column block on the canvas
        tw_max = max(f_term.getlength(s) / S for s, _, _ in STEPS)
        aw_max = max(f_an.getlength(f"{o} · {y}") / S for _, o, y in STEPS)
        block = 24 + 28 + tw_max + 60 + aw_max
        x_ar = (W - block) / 2
        x_term = x_ar + 52
        x_an = x_term + tw_max + 60
        y = 120
        for i, (term, org, year) in enumerate(STEPS):
            if i:
                tx(x_ar, y, "→", f_ar, CYAN)
            col = WHITE if i == len(STEPS) - 1 else CODE
            tw = tx(x_term, y, term, f_term, col)
            # dotted leader ties the term to its annotation
            dot_y = y - capH(f_term) / 2
            dx = x_term + tw + 16
            while dx < x_an - 16:
                circle(dx, dot_y, 1.05, (*MUTED, 85))
                dx += 9
            tx(x_an, y, f"{org} · {year}", f_an, MUTED)
            y += 44
        tx(x_an + aw_max, 330, "(career)", mono(14, 500), (*CYAN, 190), align="r")

    elif variant == "chain":
        # short terms so five nodes fit; the detail moves to the line beneath
        CHAIN = [
            ("developer", "TCS",                    "2015"),
            ("auditor",   "TCS",                    "2018"),
            ("M.S.",      "Cybersecurity · NEU",    "2019"),
            ("Ph.D.",     "Computer Science · NEU", "2021"),
            ("scientist", "AWS",                    "2025"),
        ]
        f_term, f_org, f_yr = mono(25, 600), mono(14, 500), mono(14, 500)
        centers = [340, 620, 900, 1180, 1460]
        y_t, y_o, y_y = 181, 211, 235
        mid = y_t - capH(f_term) / 2
        halves = [f_term.getlength(s) / S / 2 for s, _, _ in CHAIN]
        for i, ((term, org, year), cx) in enumerate(zip(CHAIN, centers)):
            tx(cx, y_t, term, f_term, WHITE if i == 4 else CODE, align="c")
            tx(cx, y_o, org, f_org, MUTED, align="c")
            tx(cx, y_y, year, f_yr, (*CYAN, 225), align="c")
        for i in range(4):
            a = centers[i] + halves[i] + 18
            b = centers[i + 1] - halves[i + 1] - 18
            d.line([a * S, mid * S, (b - 7) * S, mid * S],
                   fill=(*MUTED, 190), width=max(1, int(1.7 * S)))
            d.polygon([(b * S, mid * S), ((b - 9) * S, (mid - 4.5) * S),
                       ((b - 9) * S, (mid + 4.5) * S)], fill=CYAN)

    elif base == "derive":
        # The rule set, closed with the multi-step reduction it derives, so the
        # accumulating skill set R actually pays off.
        MENLO = "/System/Library/Fonts/Menlo.ttc"
        FALLBACK = set("∪∩∧∅")

        def menlo(size):
            return ImageFont.truetype(MENLO, int(size * S), index=0)

        def gridseg(x, baseline, segs, size, hl=None, weight=500):
            """Lay segments of (text, colour) on one monospace grid so the
            Menlo fallback glyphs stay cell-aligned."""
            f = mono(size, weight)
            adv = f.getlength("0") / S
            i = 0
            for text, col in segs:
                for ch in text:
                    if ch != " ":
                        use = menlo(size * 1.16) if ch in FALLBACK else f
                        c = (hl or {}).get(ch, col)
                        gw = use.getlength(ch) / S
                        d.text(((x + i * adv + (adv - gw) / 2) * S, baseline * S),
                               ch, font=use, fill=c, anchor="ls")
                    i += 1
            return i * adv

        def seglen(segs):
            return sum(len(t) for t, _ in segs)

        # sizes tuned against a 900px-wide render (LinkedIn's desktop scale)
        SZ, N_SZ = 17, 14.5
        HL = {"R": CYAN}

        RULES = [
            # This rule fires from the start state ⟨developer, ∅⟩, so its
            # premises must not constrain R: `reviews ⊆ R` would reduce to
            # `reviews ⊆ ∅` and make the closing derivation unsound.
            # Must not presuppose a security interest: Rule 2 lists
            # `security ∈ interests` as a precondition, so that interest has to
            # emerge FROM this rule's auditing, not before it.
            ("quality ∈ goals     compliance = 100%",
             "⟨developer, R⟩  →  ⟨auditor, R ∪ {code audits}⟩",
             "TCS · 2017", "(Audit-Code)"),
            ("{code audits} ⊆ R     security ∈ interests",
             "⟨auditor, R⟩  →  ⟨MS CY, R ∪ {pen testing}⟩",
             "Northeastern · 2019", "(Enter-Grad-School)"),
            ("advisor = Frank Tip     research ⊆ PL ∩ SE",
             "⟨MS CY, R⟩  →  ⟨PhD, R ∪ {program analysis}⟩",
             "Northeastern · 2021", "(Start-Research)"),
            ("defended(thesis)     internships = 3",
             "⟨PhD, R⟩  →  ⟨scientist, R ∪ {correctness}⟩",
             "AWS · 2025", "(Apply-Research)"),
        ]
        adv = mono(SZ, 500).getlength("0") / S
        bar_w = 24 + adv * max(max(len(p) for p, _, _, _ in RULES),
                               max(len(c) for _, c, _, _ in RULES))
        # half the gap between columns
        GUTTER = 34
        cols = (792 - bar_w / 2 - GUTTER, 792 + bar_w / 2 + GUTTER)
        grid_l, grid_r = cols[0] - bar_w / 2, cols[1] + bar_w / 2
        f_n = mono(N_SZ, 500)
        for i, (prem, conc, when, name) in enumerate(RULES):
            cx, p = cols[i % 2], (66, 190)[i // 2]
            gridseg(cx - len(prem) * adv / 2, p, [(prem, MUTED)], SZ, HL)
            d.line([(cx - bar_w / 2) * S, (p + 15) * S,
                    (cx + bar_w / 2) * S, (p + 15) * S],
                   fill=(*MUTED, 165), width=max(1, int(1.6 * S)))
            gridseg(cx - len(conc) * adv / 2, p + 45, [(conc, CODE)], SZ, HL)
            # lifted off MUTED: over the brighter glow the year measured
            # 3.87:1, under AA for normal text
            tx(cx - bar_w / 2, p + 71, when, f_n, (0xc6, 0xd3, 0xea))
            tx(cx + bar_w / 2, p + 71, name, f_n, (*CYAN, 205), align="r")

        # the derivation these four rules add up to
        close = [("⟨developer, ∅⟩", MUTED), ("  ", MUTED), ("→*", CYAN),
                 ("  ⟨", CODE), ("scientist", WHITE),
                 (", {code audits, pen testing, program analysis, correctness}⟩", CODE)]
        CSZ = 20
        cadv = mono(CSZ, 500).getlength("0") / S
        close_w = seglen(close) * cadv
        div_l, div_r = min(grid_l, 792 - close_w / 2), max(grid_r, 792 + close_w / 2)
        d.line([div_l * S, 288 * S, div_r * S, 288 * S],
               fill=(*MUTED, 95), width=max(1, int(1.4 * S)))
        gridseg(792 - close_w / 2, 332, close, CSZ, weight=600)

        f_cap = ImageFont.truetype(f"{F}/Inter.ttf", int(14 * S))
        f_cap.set_variation_by_axes([32, 400])
        cap = "Fig. 1.  Career transitions as rewrite rules;  R is the set of skills acquired so far."
        d.text(((792 - f_cap.getlength(cap) / S / 2) * S, 370 * S), cap,
               font=f_cap, fill=DIM, anchor="ls")

        # site URL, bottom-right, opposite LinkedIn's avatar overlay
        if opts["url"]:
            f_u = ImageFont.truetype(f"{F}/Inter.ttf", int(17 * S))
            f_u.set_variation_by_axes([32, 600])
            url = "spitfiresatya.github.io"
            d.text((div_r * S, 370 * S), url, font=f_u, fill=opts["url"],
                   anchor="rs")

    elif variant == "rules":
        # A *set* of rewrite rules in the style of Fig. 8 of the OOPSLA paper.
        # Above the bar: preconditions that must hold for the rule to fire.
        # Below: an actual term rewrite. R is a metavariable bound on the
        # left-hand side and extended on the right, so responsibilities
        # visibly accumulate across the derivation.
        MENLO = "/System/Library/Fonts/Menlo.ttc"
        FALLBACK = set("∪∩∧")      # glyphs JetBrains Mono lacks

        def menlo(size):
            return ImageFont.truetype(MENLO, int(size * S), index=0)

        def grid(x, baseline, s, size, base, hl=None, weight=500):
            """Lay a string on the monospace grid, one cell per character, so
            fallback glyphs stay aligned. hl recolours individual chars."""
            f, fb = mono(size, weight), menlo(size)
            adv = f.getlength("0") / S
            for i, ch in enumerate(s):
                if ch == " ":
                    continue
                # Menlo's math glyphs read smaller than JetBrains Mono's, so
                # scale the fallback up to match the optical size
                use = menlo(size * 1.16) if ch in FALLBACK else f
                col = (hl or {}).get(ch, base)
                gw = use.getlength(ch) / S
                d.text(((x + i * adv + (adv - gw) / 2) * S, baseline * S), ch,
                       font=use, fill=col, anchor="ls")
            return len(s) * adv

        P_SZ, C_SZ, N_SZ = 15, 15, 13
        HL_P = {"R": CYAN}
        HL_C = {"R": CYAN, "→": WHITE}

        RULES = [
            # This rule fires from the start state ⟨developer, ∅⟩, so its
            # premises must not constrain R: `reviews ⊆ R` would reduce to
            # `reviews ⊆ ∅` and make the closing derivation unsound.
            # Must not presuppose a security interest: Rule 2 lists
            # `security ∈ interests` as a precondition, so that interest has to
            # emerge FROM this rule's auditing, not before it.
            ("quality ∈ goals     led(migration)",
             "⟨developer, R⟩  →  ⟨auditor, R ∪ {code audits}⟩",
             "TCS · 2018", "(Audit-Code)"),
            ("{code audits} ⊆ R     security ∈ interests",
             "⟨auditor, R⟩  →  ⟨M.S., R ∪ {pen testing}⟩",
             "Northeastern · 2019", "(Enter-Grad-School)"),
            ("advisor = Frank Tip     interests = PL ∩ SE",
             "⟨M.S., R⟩  →  ⟨Ph.D., R ∪ {program analysis}⟩",
             "Northeastern · 2021", "(Start-Research)"),
            ("defended(thesis)     internships = 3",
             "⟨Ph.D., R⟩  →  ⟨scientist, R ∪ {correctness}⟩",
             "AWS · 2025", "(Join-Industry)"),
        ]

        adv_c = mono(C_SZ, 500).getlength("0") / S
        bar_w = 24 + adv_c * max(max(len(p) for p, _, _, _ in RULES),
                                 max(len(c) for _, c, _, _ in RULES))
        cols = (792 - bar_w / 2 - 43, 792 + bar_w / 2 + 43)
        rows = (105, 235)
        f_n = mono(N_SZ, 500)
        for i, (prem, conc, when, name) in enumerate(RULES):
            cx, p = cols[i % 2], rows[i // 2]
            grid(cx - len(prem) * adv_c / 2, p, prem, P_SZ, MUTED, HL_P)
            d.line([(cx - bar_w / 2) * S, (p + 14) * S,
                    (cx + bar_w / 2) * S, (p + 14) * S],
                   fill=(*MUTED, 165), width=max(1, int(1.6 * S)))
            grid(cx - len(conc) * adv_c / 2, p + 42, conc, C_SZ, CODE, HL_C)
            tx(cx - bar_w / 2, p + 68, when, f_n, DIM)
            tx(cx + bar_w / 2, p + 68, name, f_n, (*CYAN, 205), align="r")

        # figure caption, echoing the papers
        f_cap = ImageFont.truetype(f"{F}/Inter.ttf", int(15 * S))
        f_cap.set_variation_by_axes([32, 400])
        cap_a = "Fig. 1. "
        cap_b = "Career transitions as rewrite rules. R denotes the set of current responsibilities."
        wa = f_cap.getlength(cap_a) / S
        wb = f_cap.getlength(cap_b) / S
        xs = 792 - (wa + wb) / 2
        d.text((xs * S, 352 * S), cap_a, font=f_cap, fill=MUTED, anchor="ls")
        d.text(((xs + wa) * S, 352 * S), cap_b, font=f_cap, fill=DIM, anchor="ls")

    elif variant == "type":
        f_p, f_c, f_n = mono(17, 500), mono(26, 500), mono(14, 500)
        prem = ["4 yrs industry", "M.S. Cybersecurity", "Ph.D. Programming Languages"]
        gap = f_p.getlength("0") / S * 5
        pw = sum(f_p.getlength(p) / S for p in prem) + gap * (len(prem) - 1)
        cx = 792
        x = cx - pw / 2
        for i, p in enumerate(prem):
            x += tx(x, 162, p, f_p, CODE) + (gap if i < len(prem) - 1 else 0)
        # conclusion: a drawn turnstile, then the typing judgment
        conc_a, conc_b = "satya : ", "Code → Correctness"
        cw = (f_c.getlength("0") / S) + 10 + f_c.getlength(conc_a + conc_b) / S
        bar_w = max(pw, cw) + 34
        d.line([(cx - bar_w / 2) * S, 178 * S, (cx + bar_w / 2) * S, 178 * S],
               fill=(*MUTED, 170), width=max(1, int(1.7 * S)))
        xs = cx - cw / 2
        xs += turnstile(xs, 222, f_c, CYAN) + 10
        xs += tx(xs, 222, conc_a, f_c, MUTED)
        tx(xs, 222, conc_b, f_c, WHITE)
        tx(cx + bar_w / 2, 258, "(Applied-Scientist)", f_n, (*CYAN, 210), align="r")

    out = img.convert("RGB").resize((W, H), Image.LANCZOS)
    dest = os.environ.get("OUT") or (
        COVER if variant == PUBLISHED
        else os.path.join(REPO, "local", "banner-variants", f"career-{variant}.png"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    out.save(dest, "PNG", optimize=True)
    print("wrote", dest)


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVER = os.path.join(REPO, "images", "linkedin-cover.png")
# the variant installed as the cover; the earlier gradient design is "minimal"
PUBLISHED = "astro-m78"

if __name__ == "__main__":
    ensure_fonts()
    for v in (sys.argv[1:] or [PUBLISHED]):
        build(v)
