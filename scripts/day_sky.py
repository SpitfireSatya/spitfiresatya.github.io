#!/usr/bin/env python3
"""Generate the light-mode background: an orbital sunrise, the daytime
counterpart of the dark-mode nebula (scripts/night_sky.py).

Usage:  python3 scripts/day_sky.py
  Writes images/day-sky.webp (landscape) and images/day-sky-portrait.webp
  (phones). Needs Pillow (with WebP) and numpy.

Earth's limb comes from the same geometry as the night sky (scripts/earth.py
and the `horizon` / `sun_x` settings in night_sky.VARIANTS), so toggling the
theme keeps Earth in place: the night pass over the dark side becomes sunrise
over the same horizon. The sky runs from soft indigo with the last few stars on
the side away from the sun, warming to cream and gold where it rises.
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import earth  # noqa: E402
import night_sky as ns  # noqa: E402


def calm(W, H, boxes, levels, soft=0.12):
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    u, v = xx / (W - 1), yy / (H - 1)
    out = np.ones((H, W))
    for (x0, y0, x1, y1, _), inside in zip(boxes, levels):
        ox = np.maximum(np.maximum(x0 - u, u - x1), 0) * W
        oy = np.maximum(np.maximum(y0 - v, v - y1), 0) * H
        o = np.clip(np.hypot(ox, oy) / (soft * W), 0, 1)
        out = np.minimum(out, inside + (1 - inside) * o * o * (3 - 2 * o))
    return out


def mix(base, col, a):
    return base * (1 - a[..., None]) + np.asarray(col, float) * a[..., None]


def render(size, boxes, horizon, sun_x, seed=11, **_):
    W, H = size
    k = H / 1500.0
    rng = np.random.default_rng(seed)
    geo = earth.geometry(W, H, horizon)
    yy, xx, alt, _along = earth.fields(W, H, geo)
    u = xx / (W - 1)
    sx, sy = earth.limb_point(geo, sun_x * W)
    sd = np.hypot(xx - sx, yy - sy)
    calm_m = calm(W, H, boxes, [b[4] for b in boxes])
    # a wider falloff for the sky lift: the narrow one showed as vertical edges
    lift = 1 - calm(W, H, boxes, [b[4] for b in boxes], soft=0.30)

    # sky: indigo twilight away from the sun, cream near it; pale overall so
    # dark text keeps its contrast
    toward = np.clip(1 - sd / (1.05 * W), 0, 1) ** 1.3
    twilight = np.array([176, 188, 240.])
    day = np.array([238, 243, 255.])
    cream = np.array([255, 240, 218.])
    img = twilight * (1 - toward[..., None]) + day * toward[..., None]
    # lift the sky behind the content so dark text keeps its contrast
    img = mix(img, (246, 248, 255), np.clip(lift * 0.7, 0, 0.7))
    img = mix(img, cream, np.clip(np.exp(-sd / (620 * k)) * 0.9, 0, 0.9))
    # a soft band of lighter sky just above the horizon
    img = mix(img, (250, 251, 255), np.clip(np.exp(-np.clip(alt, 0, None) / (260 * k)) * 0.45, 0, 0.45))

    # the last stars, fading out toward the sun
    fade = (1 - toward) ** 2 * calm_m
    for _ in range(int(900 * W / 2400)):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if alt[int(y), int(x)] < 4 or rng.uniform() > fade[int(y), int(x)]:
            continue
        b = min(1.0, 0.35 + rng.pareto(2.5) * 0.35)
        r = (0.9 + 1.4 * b) * k
        xa, xb, ya, yb = int(x - 4), int(x + 5), int(y - 4), int(y + 5)
        xa, ya = max(xa, 0), max(ya, 0)
        gy, gx = np.mgrid[ya:min(yb, H), xa:min(xb, W)].astype(float)
        g = np.exp(-((gx - x) ** 2 + (gy - y) ** 2) / (r * r))
        img[ya:yb, xa:xb] = mix(img[ya:yb, xa:xb], (252, 253, 255), np.clip(g * b * 1.2, 0, 1))

    # sun rays: faint shafts fanning up from the sunrise point
    ang = np.arctan2(yy - sy, xx - sx)
    shafts = np.random.default_rng(seed + 1).random(720)
    idx = ((ang + np.pi) / (2 * np.pi) * 720).astype(int) % 720
    ray = shafts[idx] ** 4 * np.exp(-sd / (900 * k)) * (alt > 0) * calm_m
    img = mix(img, (255, 236, 196), np.clip(ray * 0.35, 0, 0.35))

    # Earth's day side and atmosphere, from the shared geometry
    img = earth.day(img, W, H, geo, sun_x, calm_m)

    # the sun breaking over the limb: bloom, six-point burst, flare streak
    bloom = np.exp(-sd / (60 * k)) + 0.45 * np.exp(-sd / (260 * k))
    spikes = sum(np.exp(-((np.angle(np.exp(1j * (ang - a0))) * sd) / (2.0 * k)) ** 2)
                 for a0 in np.radians([0, 60, 120, 180, 240, 300]))
    spikes *= np.exp(-sd / (480 * k)) * np.clip(alt / (6 * k) + 0.15, 0.15, 1)
    img = mix(img, (255, 250, 232), np.clip(bloom + 0.6 * spikes, 0, 1))
    # the light spreads along the atmosphere, hugging the curve
    along_glow = np.exp(-np.abs(alt) / (5 * k)) * np.exp(-sd / (900 * k))
    img = mix(img, (255, 247, 225), np.clip(along_glow * 0.9 * (0.4 + 0.6 * calm_m), 0, 0.9))
    return img


if __name__ == "__main__":
    for night_name, name in (("night-sky", "day-sky"), ("night-sky-portrait", "day-sky-portrait")):
        cfg = ns.VARIANTS[night_name]
        ns.save(render(**cfg), name)
