#!/usr/bin/env python3
"""Generate the dark-mode background: an M78-style nebula, matching the
LinkedIn cover (scripts/linkedin_cover.py, variant astro-m78).

Usage:  python3 scripts/night_sky.py
  Writes images/night-sky.webp (landscape, desktop) and
  images/night-sky-portrait.webp (phones). Needs Pillow (with WebP) and numpy.

The page content sits over this image, so the clouds are kept to the edges:
the right-hand margin (where the moon toggle lives), the left edge and the
bottom-left corner. Behind the content column the cloud drops to a faint
bridge and the stars thin out, so body text stays on near-black.
"""
import os

import numpy as np
from PIL import Image

import earth

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPACE = np.array([6, 5, 15], float)          # keep in sync with --global-bg-color

VARIANTS = {
    # size; cloud lobes (x, y, sx, sy, angle, weight) in 0-1 units; calm boxes
    # (x0, y0, x1, y1, cloud strength inside) where page content sits; the
    # number of stars; and bright four-point stars (x, y, brightness).
    # 16:10 so a typical laptop window (1440x900) shows the full width: at
    # 16:9, background-size: cover cropped away most of the left cloud.
    "night-sky": dict(
        size=(2400, 1500),
        lobes=[(0.94, 0.28, 0.13, 0.34, -0.35, 1.0),     # right, below the moon
               (0.90, 0.88, 0.12, 0.20, 0.4, 0.8),
               (0.02, 0.30, 0.10, 0.30, 0.25, 1.0),     # left, mirrored
               (0.06, 0.92, 0.14, 0.18, -0.4, 0.9),
               (0.50, 0.55, 0.45, 0.20, -0.15, 0.30)],  # faint bridge
        boxes=[(0.235, 0.07, 0.785, 1.0, 0.18),          # main column
               (0.065, 0.07, 0.215, 0.62, 0.50)],        # sidebar
        stars=3200,
        # none in the top-right: the theme toggle is drawn as a cross star
        # there and must be the only one, or it reads as a double star
        crosses=[(0.975, 0.50, 1.0), (0.03, 0.07, 0.85), (0.025, 0.62, 0.6),
                 (0.20, 0.80, 0.45)],
        # Earth's limb, shared with day_sky.py: three points it passes through
        # (0-1 units). Tilted, as in most ISS photos, so the horizon rises
        # into the right margin where the sun comes up (sun_x).
        horizon=[(0.0, 1.07), (0.5, 0.83), (1.0, 0.71)],
        sun_x=0.90,
    ),
    "night-sky-portrait": dict(
        size=(1080, 1920),
        # Phones have no margins, so the cloud runs at near full structure
        # everywhere and `cap` limits its brightness behind text instead:
        # white text needs a dark background, not an empty one.
        lobes=[(0.95, 0.10, 0.30, 0.12, -0.5, 1.0),
               (0.08, 0.68, 0.32, 0.12, 0.4, 1.0),       # above the horizon
               (0.02, 0.38, 0.14, 0.18, 0.2, 0.8),
               (0.98, 0.52, 0.14, 0.18, -0.2, 0.8),
               (0.55, 0.42, 0.50, 0.25, -0.6, 0.55)],
        boxes=[(0.04, 0.0, 0.96, 1.0, 0.75)],
        cap=0.37,                       # brightest 1% of cloud still >= 4.5:1 for links
        lights_floor=0.75,
        blue_bias=0.3,                  # the cap keeps magenta dim enough
        inside_stars=(0.85, 0.8),
        dust_max=0.5,
        stars=1500,
        crosses=[(0.12, 0.62, 0.7), (0.92, 0.55, 0.5)],
        horizon=[(0.0, 0.95), (0.5, 0.86), (1.0, 0.81)],
        sun_x=0.86,
    ),
}


def fbm(rng, w, h, cells, octaves=5, gain=0.55):
    """Fractal value noise in [0, 1] from bicubically upsampled random grids."""
    acc = np.zeros((h, w))
    amp = tot = 0.0
    amp = 1.0
    for o in range(octaves):
        gw = int(cells * 2 ** o) + 2
        gh = max(2, int(gw * h / w) + 2)
        g = Image.fromarray(rng.random((gh, gw)).astype(np.float32), "F")
        acc += amp * np.asarray(g.resize((w, h), Image.BICUBIC), float)
        tot += amp
        amp *= gain
    acc /= tot
    return (acc - acc.min()) / (acc.max() - acc.min())


def screen(a, layer):
    return 255 - (255 - a) * (255 - np.clip(layer, 0, 255)) / 255.0


def render(name, size, lobes, boxes, stars, crosses, horizon=None, sun_x=None,
           cap=None, lights_floor=None, blue_bias=1.0, inside_stars=(0.4, 0.45),
           dust_max=0.75):
    W, H = size
    rng = np.random.default_rng(78)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    u, v = xx / (W - 1), yy / (H - 1)
    # aspect-corrected coordinates so lobes are round in pixels, not in units
    ar = W / H

    shape = np.zeros((H, W))
    for x, y, sx, sy, a, wgt in lobes:
        ca, sa = np.cos(a), np.sin(a)
        dx, dy = (u - x) * ar, v - y
        p = (dx * ca + dy * sa) / (sx * ar)
        q = (-dx * sa + dy * ca) / sy
        shape += wgt * np.exp(-(p * p + q * q))

    n1 = fbm(rng, W, H, 3, 6, 0.58)
    n2 = fbm(rng, W, H, 6, 5, 0.6)
    dens = shape * (0.55 + 1.8 * np.clip(n1 - 0.25, 0, 1)) * (0.6 + 0.9 * n2)
    core = np.clip(dens - 0.45, 0, None) ** 1.2 * 2.2

    # dust: broad feathery patches plus soft filaments
    patch = np.clip((fbm(rng, W, H, 7, 6, 0.66) - 0.55) / 0.24, 0, 1) ** 1.3
    fil = (1 - np.abs(2 * fbm(rng, W, H, 3, 6, 0.65) - 1)) ** 4
    fil *= np.clip((fbm(rng, W, H, 4, 3) - 0.45) / 0.2, 0, 1)
    absorb = np.clip(0.7 * patch + 0.5 * fil, 0, dust_max) * np.clip(dens / 0.6, 0, 1)
    dens *= 1 - absorb
    core *= 1 - absorb

    # keep the content areas calm, with a wide smoothstep falloff (a narrow
    # one leaves a hard vertical edge); `out` is 0 inside any box, 1 far away
    scrim = np.ones((H, W))
    out = np.ones((H, W))
    for x0, y0, x1, y1, inside in boxes:
        ox = np.maximum(np.maximum(x0 - u, u - x1), 0) * W
        oy = np.maximum(np.maximum(y0 - v, v - y1), 0) * H
        o = np.clip(np.hypot(ox, oy) / (0.12 * W), 0, 1)
        o = o * o * (3 - 2 * o)
        scrim = np.minimum(scrim, inside + (1 - inside) * o)
        out = np.minimum(out, o)
    dens *= scrim
    core *= scrim ** 3

    # emission (violet -> magenta) vs reflection (blue); blue wherever the
    # cloud reaches into the content area, so pale-rose headings stay distinct
    refl = np.clip((fbm(rng, W, H, 2, 3) - 0.42) / 0.3, 0, 1)
    refl = np.maximum(refl, (1 - out) * blue_bias)
    violet = np.array([70, 22, 120], float)
    magenta = np.array([200, 55, 200], float)
    blue = np.array([70, 95, 255], float)
    lav = np.array([238, 222, 255], float)
    t = np.clip(dens / 0.9, 0, 1)[..., None]
    col = (violet * (1 - t) + magenta * t) * (1 - refl[..., None]) + blue * refl[..., None]

    img = np.zeros((H, W, 3)) + SPACE
    img = screen(img, col * np.clip(dens, 0, 1.0)[..., None] * 1.05)
    img = screen(img, lav * np.clip(core, 0, 0.8)[..., None] * 0.6)

    if cap is not None:
        # tone the cloud down behind text without flattening it: scale each
        # pixel's light above the base so its brightest channel stays under
        # `cap`, rising back to full strength away from the content
        # soft roll-off rather than a hard clip, so cores still read brighter
        # than their edges and dust lanes don't flatten into black blotches
        light = img - SPACE
        peak = np.maximum(light.max(axis=2), 1e-3) / 255.0
        limit = cap + (1 - cap) * out
        soft = limit * (1 - np.exp(-peak / limit))
        img = SPACE + light * (soft / peak)[..., None]

    # starfield: warm/white/blue, power-law brightness, sparse behind content
    tints = [np.array(c, float) for c in
             ((255, 214, 170), (255, 245, 235), (205, 220, 255), (255, 190, 140))]
    for _ in range(stars):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        inside_box = out[min(int(y), H - 1), min(int(x), W - 1)] < 0.5
        if inside_box and rng.uniform() > inside_stars[0]:
            continue
        b = min(rng.pareto(2.0) * 0.35 + 0.14, 1.0) * (inside_stars[1] if inside_box else 1.0)
        rad = 0.6 + 1.6 * b
        win = int(np.ceil(rad * 3 + 2))
        xa, xb = max(0, int(x) - win), min(W, int(x) + win + 1)
        ya, yb = max(0, int(y) - win), min(H, int(y) + win + 1)
        sy, sx = np.mgrid[ya:yb, xa:xb].astype(float)
        g = np.exp(-((sx - x) ** 2 + (sy - y) ** 2) / (rad * rad * 0.6))
        c = tints[rng.integers(len(tints))]
        img[ya:yb, xa:xb] = screen(img[ya:yb, xa:xb], c * np.clip(g * b * 1.6, 0, 1)[..., None])

    # a few bright stars with the four-point cross from the reference photo
    k = W / 1584                      # scale relative to the cover's width
    for cx, cy, b in crosses:
        x, y = cx * W, cy * H
        L = 34 * b * k
        win = int(L * 3)
        xa, xb = max(0, int(x) - win), min(W, int(x) + win + 1)
        ya, yb = max(0, int(y) - win), min(H, int(y) + win + 1)
        sy, sx = np.mgrid[ya:yb, xa:xb].astype(float)
        dx, dy = sx - x, sy - y
        w = 0.5 * k
        acc = (np.exp(-np.abs(dx) / L) * np.exp(-(dy / w) ** 2)
               + np.exp(-np.abs(dy) / L) * np.exp(-(dx / w) ** 2))
        rr2 = (dx * dx + dy * dy) / (k * k)
        acc += 1.5 * np.exp(-rr2 / (2.0 * b + 0.4)) + 0.3 * np.exp(-rr2 / (50 * b))
        img[ya:yb, xa:xb] = screen(img[ya:yb, xa:xb],
                                   np.array([240, 235, 255.]) * np.clip(acc * b, 0, 1)[..., None])

    if horizon:
        # Earth's night side over the bottom of the frame; it hides whatever
        # nebula and stars lie below the horizon
        earth_calm = out if lights_floor is None else np.maximum(out, lights_floor)
        img = earth.night(img, W, H, earth.geometry(W, H, horizon), sun_x, earth_calm)
    return img


def save(img, name):
    out_path = os.path.join(REPO, "images", f"{name}.webp")
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(
        out_path, "WEBP", quality=82, method=6)
    print("wrote", out_path, f"{os.path.getsize(out_path) // 1024} KB")


if __name__ == "__main__":
    for name, cfg in VARIANTS.items():
        save(render(name, **cfg), name)
