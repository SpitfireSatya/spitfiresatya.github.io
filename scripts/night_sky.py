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

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPACE = np.array([6, 5, 15], float)          # keep in sync with --global-bg-color

VARIANTS = {
    # name: size, cloud lobes (x, y, sx, sy, angle, weight) in 0-1 units,
    # the box (0-1 units) where content sits, and the cloud strength there
    "night-sky": dict(
        size=(2400, 1350),
        lobes=[(0.93, 0.30, 0.16, 0.36, -0.35, 1.0),
               (0.88, 0.86, 0.14, 0.22, 0.4, 0.75),
               (0.02, 0.58, 0.07, 0.30, 0.2, 0.7),
               (0.10, 1.02, 0.18, 0.14, -0.3, 0.8),
               (0.50, 0.55, 0.45, 0.20, -0.15, 0.35)],
        content=(0.06, 0.07, 0.79, 1.0),
        inside=0.22,
        stars=2600,
    ),
    "night-sky-portrait": dict(
        size=(1080, 1920),
        lobes=[(0.95, 0.10, 0.30, 0.12, -0.5, 1.0),
               (0.05, 0.92, 0.32, 0.12, 0.4, 0.85),
               (0.55, 0.50, 0.50, 0.25, -0.6, 0.3)],
        content=(0.04, 0.0, 0.96, 1.0),
        inside=0.30,
        stars=1300,
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


def render(name, size, lobes, content, inside, stars):
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
    patch = np.clip((fbm(rng, W, H, 5, 6, 0.62) - 0.56) / 0.16, 0, 1) ** 1.5
    fil = (1 - np.abs(2 * fbm(rng, W, H, 3, 6, 0.65) - 1)) ** 4
    fil *= np.clip((fbm(rng, W, H, 4, 3) - 0.45) / 0.2, 0, 1)
    absorb = np.clip(0.85 * patch + 0.45 * fil, 0, 0.88) * np.clip(dens / 0.6, 0, 1)
    dens *= 1 - absorb
    core *= 1 - absorb

    # keep the content area calm: distance (in px) outside the content box
    x0, y0, x1, y1 = content
    ox = np.maximum(np.maximum(x0 - u, u - x1), 0) * W
    oy = np.maximum(np.maximum(y0 - v, v - y1), 0) * H
    # wide smoothstep falloff: a narrow one leaves a hard vertical edge
    out = np.clip(np.hypot(ox, oy) / (0.17 * W), 0, 1)
    out = out * out * (3 - 2 * out)
    scrim = inside + (1 - inside) * out
    dens *= scrim
    core *= scrim ** 3

    # emission (violet -> magenta) vs reflection (blue); blue wherever the
    # cloud reaches into the content area, so pale-rose headings stay distinct
    refl = np.clip((fbm(rng, W, H, 2, 3) - 0.42) / 0.3, 0, 1)
    refl = np.maximum(refl, 1 - out)
    violet = np.array([70, 22, 120], float)
    magenta = np.array([200, 55, 200], float)
    blue = np.array([70, 95, 255], float)
    lav = np.array([238, 222, 255], float)
    t = np.clip(dens / 0.9, 0, 1)[..., None]
    col = (violet * (1 - t) + magenta * t) * (1 - refl[..., None]) + blue * refl[..., None]

    img = np.zeros((H, W, 3)) + SPACE
    img = screen(img, col * np.clip(dens, 0, 1.0)[..., None] * 0.8)
    img = screen(img, lav * np.clip(core, 0, 1)[..., None] * 0.4)

    # starfield: warm/white/blue, power-law brightness, sparse behind content
    tints = [np.array(c, float) for c in
             ((255, 214, 170), (255, 245, 235), (205, 220, 255), (255, 190, 140))]
    for _ in range(stars):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        inside_box = x0 * W < x < x1 * W and y0 * H < y < y1 * H
        if inside_box and rng.uniform() > 0.4:
            continue
        b = min(rng.pareto(2.0) * 0.35 + 0.14, 1.0) * (0.45 if inside_box else 1.0)
        rad = 0.6 + 1.6 * b
        win = int(np.ceil(rad * 3 + 2))
        xa, xb = max(0, int(x) - win), min(W, int(x) + win + 1)
        ya, yb = max(0, int(y) - win), min(H, int(y) + win + 1)
        sy, sx = np.mgrid[ya:yb, xa:xb].astype(float)
        g = np.exp(-((sx - x) ** 2 + (sy - y) ** 2) / (rad * rad * 0.6))
        c = tints[rng.integers(len(tints))]
        img[ya:yb, xa:xb] = screen(img[ya:yb, xa:xb], c * np.clip(g * b * 1.6, 0, 1)[..., None])

    out_path = os.path.join(REPO, "images", f"{name}.webp")
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(
        out_path, "WEBP", quality=82, method=6)
    print("wrote", out_path, f"{os.path.getsize(out_path) // 1024} KB")


if __name__ == "__main__":
    for name, cfg in VARIANTS.items():
        render(name, **cfg)
