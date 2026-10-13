"""Earth from orbit, shared by both theme backgrounds.

The limb is one circle per image size, defined by three points it passes
through, so toggling the theme swaps the sky while Earth stays exactly where
it is: dark mode is a night pass (the nebula over Earth's night side, green
airglow on the limb, city lights), light mode the orbital sunrise a few
minutes later over the same horizon.

Used by scripts/night_sky.py and scripts/day_sky.py; not run directly.
"""
import numpy as np


def geometry(W, H, horizon):
    """Circle through three (x, y) points given in 0-1 units -> (cx, cy, R)."""
    (x1, y1), (x2, y2), (x3, y3) = [(x * W, y * H) for x, y in horizon]
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    a, b, c = x1 * x1 + y1 * y1, x2 * x2 + y2 * y2, x3 * x3 + y3 * y3
    cx = (a * (y2 - y3) + b * (y3 - y1) + c * (y1 - y2)) / d
    cy = (a * (x3 - x2) + b * (x1 - x3) + c * (x2 - x1)) / d
    return cx, cy, float(np.hypot(x1 - cx, y1 - cy))


def fields(W, H, geo):
    """Per-pixel height above the limb (px, negative below) and distance along it."""
    cx, cy, R = geo
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    d = np.hypot(xx - cx, yy - cy)
    along = np.arctan2(yy - cy, xx - cx) * R
    return yy, xx, d - R, along


def limb_point(geo, x):
    cx, cy, R = geo
    return x, cy - np.sqrt(R * R - (x - cx) ** 2)


def surface(rng, alt, along, cells, fbm, stretch=0.5, depth_k=22.0):
    """Sample a noise texture in the planet's frame, foreshortened toward the
    limb, so clouds and coastlines flatten into bands near the horizon."""
    Tw, Th = 4096, 900
    tex = fbm(rng, Tw, Th, cells, 6, 0.6)
    sx = ((along - along.min()) * stretch).astype(int) % Tw
    sy = np.clip(np.sqrt(np.clip(-alt, 0, None)) * depth_k, 0, Th - 1).astype(int)
    return tex[sy, sx]


def _mix(base, col, a):
    return base * (1 - a[..., None]) + np.asarray(col, float) * a[..., None]


def night(img, W, H, geo, sun_x, calm_m, seed=40):
    """Night side: near-black ground with faint moonlit cloud, city lights in
    the margins, the green airglow band and a first hint of dawn near sun_x."""
    from night_sky import fbm, screen
    rng = np.random.default_rng(seed)
    yy, xx, alt, along = fields(W, H, geo)
    k = H / 1500.0
    sx, sy = limb_point(geo, sun_x * W)
    near = np.exp(-np.hypot(xx - sx, yy - sy) / (520 * k))

    # atmosphere above the limb: a thin blue rim, a dark gap, then airglow
    a_ = np.clip(alt, 0, None)
    rim = np.exp(-a_ / (3.5 * k)) * (alt >= 0)
    glow = np.exp(-((alt - 17 * k) / (4.5 * k)) ** 2)
    glow *= 0.55 + 0.45 * fbm(rng, W, H, 30, 3, 0.5)          # it's patchy
    soft = 0.35 + 0.65 * calm_m
    img = screen(img, np.array([96, 165, 250.]) * (rim * 0.55 * soft)[..., None])
    img = screen(img, np.array([74, 222, 128.]) * (glow * 0.42 * soft)[..., None])
    # dawn: the limb starts to light up where the sun will rise
    dawn = np.exp(-a_ / (9 * k)) * (alt >= 0) * near
    img = screen(img, np.array([253, 186, 116.]) * (dawn * 0.9)[..., None])
    img = screen(img, np.array([125, 211, 252.]) * (np.exp(-a_ / (40 * k)) * (alt >= 0) * near * 0.35)[..., None])

    # the ground
    cloud = np.clip((surface(rng, alt, along, 12, fbm) - 0.4) / 0.35, 0, 1)
    land = surface(rng, alt, along, 5, fbm, stretch=0.35) > 0.52
    ground = np.zeros((H, W, 3)) + np.array([5, 6, 14.])
    ground = _mix(ground, (30, 36, 58), cloud * 0.55)
    ground = _mix(ground, (40, 30, 30), near * 0.25)
    # city lights: clusters of warm specks on land, squashed toward the limb
    # by foreshortening, fading in from the margins (none behind content)
    from PIL import Image, ImageFilter
    weight = land * (alt < -10 * k) * calm_m ** 3
    ys, xs = np.nonzero(weight > 0.05)
    lights = np.zeros((H, W))
    if len(ys):
        p = weight[ys, xs] / weight[ys, xs].sum()
        for i in rng.choice(len(ys), size=min(len(ys), 90), replace=False, p=p):
            y0, x0 = ys[i], xs[i]
            fore = np.clip(np.sqrt(-alt[y0, x0] / (700 * k)), 0.12, 1.0)
            n = int(np.clip(rng.pareto(1.5) * 12 + 6, 6, 90))
            spread = rng.uniform(6, 22) * k
            px = (x0 + rng.normal(0, spread, n)).astype(int)
            py = (y0 + rng.normal(0, spread * fore, n)).astype(int)
            ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
            px, py = px[ok], py[ok]
            ok = alt[py, px] < -3 * k
            b = rng.uniform(0.25, 0.9, ok.sum()) * calm_m[py[ok], px[ok]]
            np.maximum.at(lights, (py[ok], px[ok]), b)
    halo = np.asarray(Image.fromarray((lights * 255).astype(np.uint8), "L")
                      .filter(ImageFilter.GaussianBlur(2.2 * k)), float) / 255
    ground = screen(ground, np.array([255, 196, 120.]) * np.clip(lights * 0.9 + halo * 1.4, 0, 1)[..., None])

    a = np.clip(-alt / 1.5 + 0.5, 0, 1)                         # anti-aliased limb
    return img * (1 - a[..., None]) + ground * a[..., None]


def day(img, W, H, geo, sun_x, calm_m, seed=41):
    """Day side at sunrise: a bright cloud deck (kept pale behind content),
    blue ocean in the margins, layered atmosphere warming toward the sun."""
    from night_sky import fbm
    rng = np.random.default_rng(seed)
    yy, xx, alt, along = fields(W, H, geo)
    k = H / 1500.0
    sx, sy = limb_point(geo, sun_x * W)
    near = np.exp(-np.hypot(xx - sx, yy - sy) / (650 * k))
    warm = np.exp(-np.hypot(xx - sx, yy - sy) / (1100 * k))   # how far sunrise colours reach

    # atmosphere: the layered band of an orbital sunrise. Near the sun it runs
    # red-orange at the surface, through gold and white, into deep blue; away
    # from the sun only the blue layers remain
    a_ = np.clip(alt, 0, None)
    up = (alt >= 0).astype(float)
    layers = [  # (height px, colour away from sun, colour at sun, strength)
        (170, (147, 180, 250), (186, 210, 255), 0.45),
        (60, (59, 110, 230), (125, 200, 255), 0.55),
        (26, (96, 165, 250), (253, 224, 150), 0.85),
        (9, (125, 211, 252), (249, 115, 22), 0.9),
    ]
    for h, far, at_sun, amt in layers:
        layer = np.exp(-a_ / (h * k)) * up * amt * (0.55 + 0.45 * calm_m)
        c = np.asarray(far, float) * (1 - warm[..., None]) + np.asarray(at_sun, float) * warm[..., None]
        img = img * (1 - layer[..., None]) + c * layer[..., None]
    img = _mix(img, (255, 255, 255), np.clip(np.exp(-np.abs(alt) / (2.5 * k)), 0, 0.95))

    cloud = np.clip((surface(rng, alt, along, 12, fbm) - 0.45) / 0.25, 0, 1)
    depth = np.clip(-alt / (300 * k), 0, 1)
    ocean = np.array([37, 99, 235.]) * (1 - depth[..., None] * 0.2) + np.array([14, 165, 233.]) * depth[..., None] * 0.2
    ground = np.zeros((H, W, 3)) + ocean
    ground = _mix(ground, (241, 246, 255), np.clip(cloud * 0.92, 0, 0.92))
    # behind the content the planet is a pale haze, so text stays readable
    ground = _mix(ground, (226, 236, 252), np.clip((1 - calm_m) * 0.85, 0, 0.85))
    ground = _mix(ground, (253, 232, 196), np.clip(near * 0.5, 0, 0.5))

    a = np.clip(-alt / 1.5 + 0.5, 0, 1)
    return img * (1 - a[..., None]) + ground * a[..., None]
