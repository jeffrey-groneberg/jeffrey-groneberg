#!/usr/bin/env python3
"""Generate a cyberpunk parallax city GIF with asteroid game revealing 'Jeffrey Groneberg'."""

import math
import random
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

random.seed(42)

# --- Canvas ---
WIDTH, HEIGHT = 840, 320

# --- Cyberpunk palette ---
DEEP_BG = (8, 5, 22)
NEON_CYAN = (0, 255, 255)
NEON_MAGENTA = (255, 0, 200)
NEON_PINK = (255, 50, 120)
NEON_GREEN = (0, 255, 80)
NEON_YELLOW = (255, 220, 0)
LASER_COLOR = NEON_PINK
LETTER_COLOR = NEON_CYAN
EXPLOSION_COLORS = [NEON_YELLOW, (255, 160, 30), NEON_PINK, NEON_MAGENTA]

# Building layer palettes
FAR_COLOR = (18, 12, 45)
FAR_OUTLINE = (28, 20, 60)
MID_COLOR = (25, 16, 50)
MID_OUTLINE = (40, 28, 70)
NEAR_COLOR = (14, 8, 32)
NEAR_OUTLINE = (30, 18, 50)
WINDOW_COLORS = [NEON_CYAN, NEON_MAGENTA, NEON_PINK, (255, 180, 0), (120, 80, 255)]

# Ship
SHIP_BODY = NEON_CYAN
SHIP_GLOW = (0, 150, 255)

# --- Fonts ---
font_path = "/System/Library/Fonts/Supplemental/Impact.ttf"
line1_font = ImageFont.truetype(font_path, 64)
line2_font = ImageFont.truetype(font_path, 64)
sub_font = ImageFont.truetype(font_path, 22)

# --- Text layout ---
LINE1 = "JEFFREY"
LINE2 = "GRONEBERG"
LINE1_Y = 70
LINE2_Y = 155

ASTEROID_R = 34


def compute_letter_positions(text, font, y):
    """Compute centered (x,y) for each letter of text."""
    # Measure each letter individually for precise placement
    widths = []
    for ch in text:
        bb = font.getbbox(ch)
        widths.append(bb[2] - bb[0])
    spacing = 12
    total = sum(widths) + spacing * (len(text) - 1)
    positions = []
    x = (WIDTH - total) // 2
    for i, ch in enumerate(text):
        cx = x + widths[i] // 2
        positions.append((cx, y))
        x += widths[i] + spacing
    return positions


L1_POS = compute_letter_positions(LINE1, line1_font, LINE1_Y)
L2_POS = compute_letter_positions(LINE2, line2_font, LINE2_Y)
ALL_LETTERS = list(LINE1) + list(LINE2)
ALL_POS = L1_POS + L2_POS
ALL_FONTS = [line1_font] * len(LINE1) + [line2_font] * len(LINE2)

# --- Timing ---
FPS = 18
FRAME_MS = int(1000 / FPS)
INTRO_FRAMES = 12
FRAMES_PER_LETTER = 6
TRANSITION_FRAMES = 5
OUTRO_FRAMES = 22
TOTAL_FRAMES = (INTRO_FRAMES
                + len(LINE1) * FRAMES_PER_LETTER
                + TRANSITION_FRAMES
                + len(LINE2) * FRAMES_PER_LETTER
                + OUTRO_FRAMES)

# --- Stars ---
stars_data = [(random.randint(0, WIDTH), random.randint(0, int(HEIGHT * 0.65)),
               random.uniform(0.2, 1.0), random.uniform(0.3, 1.5))
              for _ in range(90)]


# ===== PARALLAX CITY GENERATION =====

class BuildingLayer:
    def __init__(self, seed, count, min_w, max_w, min_h, max_h,
                 base_y, color, outline, speed, win_density=0.3):
        rng = random.Random(seed)
        self.speed = speed
        self.base_y = base_y
        self.color = color
        self.outline = outline
        self.buildings = []
        x = 0
        for _ in range(count):
            w = rng.randint(min_w, max_w)
            h = rng.randint(min_h, max_h)
            has_antenna = rng.random() < 0.3
            antenna_h = rng.randint(8, 25) if has_antenna else 0
            # Generate windows
            windows = []
            win_w, win_h = 4, 4
            cols = max(1, (w - 8) // 8)
            rows = max(1, (h - 10) // 8)
            for wr in range(rows):
                for wc in range(cols):
                    if rng.random() < win_density:
                        wx = 5 + wc * 8
                        wy = 6 + wr * 8
                        wcolor = rng.choice(WINDOW_COLORS)
                        # Dim most windows
                        dim = rng.uniform(0.15, 0.7)
                        wcolor = tuple(int(c * dim) for c in wcolor)
                        windows.append((wx, wy, win_w, win_h, wcolor))
            # Neon sign on some buildings
            neon_sign = None
            if rng.random() < 0.15 and w > 35:
                nc = rng.choice([NEON_CYAN, NEON_MAGENTA, NEON_PINK])
                neon_sign = (w // 2, 12, nc)
            self.buildings.append({
                'x': x, 'w': w, 'h': h,
                'antenna_h': antenna_h,
                'windows': windows,
                'neon_sign': neon_sign,
            })
            x += w + rng.randint(2, 6)
        self.total_width = x + 100  # extra buffer for seamless wrap

    def draw(self, draw_ctx, frame):
        offset = (frame * self.speed) % self.total_width
        for b in self.buildings:
            bx = b['x'] - offset
            # Wrap around
            if bx + b['w'] < -50:
                bx += self.total_width
            if bx > WIDTH + 50:
                bx -= self.total_width
            if bx + b['w'] < -10 or bx > WIDTH + 10:
                continue
            top = self.base_y - b['h']
            # Main building rect
            draw_ctx.rectangle([bx, top, bx + b['w'], self.base_y],
                               fill=self.color, outline=self.outline)
            # Antenna
            if b['antenna_h'] > 0:
                ax = bx + b['w'] // 2
                draw_ctx.line([(ax, top), (ax, top - b['antenna_h'])],
                              fill=self.outline, width=2)
                # Blinking light on antenna
                if (frame // 4) % 2 == 0:
                    draw_ctx.ellipse([ax - 2, top - b['antenna_h'] - 2,
                                      ax + 2, top - b['antenna_h'] + 2],
                                     fill=NEON_PINK)
            # Windows
            for wx, wy, ww, wh, wc in b['windows']:
                # Some windows flicker
                if random.Random(hash((bx, wy, frame // 6))).random() < 0.05:
                    continue
                draw_ctx.rectangle([bx + wx, top + wy,
                                    bx + wx + ww, top + wy + wh], fill=wc)
            # Neon sign
            if b['neon_sign']:
                nx, ny, nc = b['neon_sign']
                pulse = 0.6 + 0.4 * math.sin(frame * 0.15 + bx * 0.1)
                pc = tuple(int(c * pulse) for c in nc)
                draw_ctx.rectangle([bx + nx - 10, top + ny - 2,
                                    bx + nx + 10, top + ny + 4], fill=pc)


# Generate three parallax layers (far, mid, near)
far_layer = BuildingLayer(seed=100, count=25, min_w=25, max_w=55,
                          min_h=70, max_h=190, base_y=HEIGHT,
                          color=FAR_COLOR, outline=FAR_OUTLINE,
                          speed=0.4, win_density=0.2)

mid_layer = BuildingLayer(seed=200, count=20, min_w=30, max_w=50,
                          min_h=50, max_h=130, base_y=HEIGHT,
                          color=MID_COLOR, outline=MID_OUTLINE,
                          speed=0.9, win_density=0.35)

near_layer = BuildingLayer(seed=300, count=14, min_w=40, max_w=70,
                           min_h=30, max_h=80, base_y=HEIGHT,
                           color=NEAR_COLOR, outline=NEAR_OUTLINE,
                           speed=1.8, win_density=0.4)

# --- Rain particles ---
rain_drops = [(random.randint(0, WIDTH), random.randint(0, HEIGHT),
               random.uniform(3, 7), random.uniform(0.1, 0.4))
              for _ in range(60)]


# ===== DRAWING FUNCTIONS =====

def draw_sky_gradient(img):
    """Subtle gradient: deep purple at top → slightly lighter near horizon."""
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(8 + t * 12)
        g = int(5 + t * 8)
        b = int(22 + t * 18)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))


def draw_stars(draw, frame):
    for sx, sy, brightness, speed in stars_data:
        flicker = 0.6 + 0.4 * math.sin(frame * speed * 0.3 + sx)
        b = max(0, min(255, int(200 * brightness * flicker)))
        tint = random.Random(sx + sy).choice([(b, b, b), (b, int(b * 0.8), int(b * 1.1)),
                                                (int(b * 0.9), b, int(b * 1.1))])
        r = 1 if brightness < 0.5 else 2
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=tint)


def draw_rain(draw, frame):
    for rx, ry, speed, alpha in rain_drops:
        y_pos = (ry + frame * speed * 8) % HEIGHT
        x_pos = (rx - frame * speed * 1.5) % WIDTH
        length = int(speed * 3)
        c = int(60 * alpha)
        draw.line([(x_pos, y_pos), (x_pos - 1, y_pos + length)],
                  fill=(c, c, int(c * 1.5)), width=1)


def draw_ship(draw, x, y):
    s = 11
    # Engine flame
    flame_pts = [(x - s * 0.35, y + s), (x, y + s * 1.7), (x + s * 0.35, y + s)]
    draw.polygon(flame_pts, fill=(0, 100, 255))
    # Body
    pts = [(x, y - s * 1.5), (x - s, y + s), (x + s, y + s)]
    draw.polygon(pts, fill=SHIP_BODY, outline=(150, 255, 255))
    # Cockpit glow
    draw.ellipse([x - 2, y - 3, x + 2, y + 3], fill=(220, 255, 255))


def draw_asteroid(draw, cx, cy, radius, seed_val):
    rng = random.Random(seed_val)
    pts = []
    for i in range(10):
        angle = (2 * math.pi / 10) * i
        r = radius + rng.uniform(-radius * 0.3, radius * 0.3)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    # Dark asteroid with purple-ish tint
    draw.polygon(pts, fill=(50, 35, 65), outline=(80, 55, 95))
    for _ in range(3):
        cr = rng.uniform(2, 6)
        ca = rng.uniform(0, 2 * math.pi)
        cd = rng.uniform(2, radius * 0.4)
        crx = cx + cd * math.cos(ca)
        cry = cy + cd * math.sin(ca)
        draw.ellipse([crx - cr, cry - cr, crx + cr, cry + cr], fill=(35, 22, 50))


def draw_explosion(draw, cx, cy, progress, seed_val):
    rng = random.Random(seed_val + 777)
    for _ in range(18):
        angle = rng.uniform(0, 2 * math.pi)
        max_dist = rng.uniform(15, 55)
        dist = max_dist * progress
        size = max(1, int(4 * (1 - progress * 0.8)))
        px = cx + dist * math.cos(angle)
        py = cy + dist * math.sin(angle)
        ci = min(len(EXPLOSION_COLORS) - 1, int(progress * len(EXPLOSION_COLORS)))
        c = EXPLOSION_COLORS[ci]
        fade = max(0, 1 - progress * 1.2)
        c_f = tuple(max(0, min(255, int(v * fade))) for v in c)
        draw.ellipse([px - size, py - size, px + size, py + size], fill=c_f)


def draw_laser(draw, x1, y1, x2, y2, progress):
    tip_y = y1 - (y1 - y2) * min(1.0, progress * 2.2)
    tail_y = y1 - (y1 - y2) * max(0, progress * 2.2 - 0.6)
    if tip_y < tail_y:
        # Glow layers
        for w, c in [(5, (80, 0, 60)), (3, (200, 30, 120)), (1, (255, 150, 200))]:
            draw.line([(x1, tail_y), (x2, tip_y)], fill=c, width=w)


def draw_letter_glow(draw, letter, cx, cy, font, glow=1.0):
    bb = font.getbbox(letter)
    lw = bb[2] - bb[0]
    lh = bb[3] - bb[1]
    lx = cx - lw // 2
    ly = cy - lh // 2
    # Neon glow layers
    for offset in [4, 3, 2, 1]:
        g = int(25 * glow * (5 - offset) / 4)
        gc = (0, g, int(g * 1.1))
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                draw.text((lx + dx, ly + dy), letter, font=font, fill=gc)
    # Main letter in neon cyan
    alpha = min(1.0, glow)
    c = tuple(max(0, min(255, int(v * alpha))) for v in LETTER_COLOR)
    draw.text((lx, ly), letter, font=font, fill=c)
    # Hot white center for extra neon pop
    inner = tuple(max(0, min(255, int(v * alpha * 0.5 + 128 * alpha))) for v in LETTER_COLOR)
    draw.text((lx, ly), letter, font=font, fill=inner)


def apply_crt_effect(img, frame):
    """Apply CRT scanlines for retro feel (optimized for GIF compression)."""
    draw = ImageDraw.Draw(img)
    # Scanlines - semi-transparent dark lines every 3rd row
    for y in range(0, HEIGHT, 3):
        draw.line([(0, y), (WIDTH, y)], fill=(4, 2, 10), width=1)
    # Subtle vignette via corner overlays
    for i in range(30):
        alpha = max(0, int(18 - i * 0.6))
        c = (alpha, alpha // 2, alpha)
        draw.rectangle([i, i, WIDTH - i, HEIGHT - i], outline=c)
    return img


def ease_in_out(t):
    return t * t * (3 - 2 * t)


# ===== MAIN FRAME GENERATION =====

def generate_frames():
    frames = []

    # Ship state
    ship_y_line1 = HEIGHT - 45
    ship_y_line2 = HEIGHT - 45

    # State per letter
    num_total = len(ALL_LETTERS)
    revealed = [False] * num_total
    exploding = [0.0] * num_total

    for frame in range(TOTAL_FRAMES):
        img = Image.new("RGB", (WIDTH, HEIGHT), DEEP_BG)
        draw_sky_gradient(img)
        draw = ImageDraw.Draw(img)

        # Stars
        draw_stars(draw, frame)

        # Parallax city (back to front)
        far_layer.draw(draw, frame)
        mid_layer.draw(draw, frame)
        near_layer.draw(draw, frame)

        # Rain
        draw_rain(draw, frame)

        # Neon horizon line
        hl_y = HEIGHT - 5
        pulse = 0.4 + 0.3 * math.sin(frame * 0.12)
        hc = tuple(int(c * pulse) for c in NEON_MAGENTA)
        draw.line([(0, hl_y), (WIDTH, hl_y)], fill=hc, width=2)

        # === Determine animation phase ===
        ship_x, ship_y = -50, ship_y_line1
        show_ship = True

        # Phase boundaries
        p1_end = INTRO_FRAMES
        p2_end = p1_end + len(LINE1) * FRAMES_PER_LETTER
        p3_end = p2_end + TRANSITION_FRAMES
        p4_end = p3_end + len(LINE2) * FRAMES_PER_LETTER
        # p5 = outro

        if frame < p1_end:
            # INTRO: ship flies in from left toward first asteroid
            progress = frame / INTRO_FRAMES
            target = L1_POS[0][0]
            ship_x = -30 + (target - (-30)) * ease_in_out(progress)
            ship_y = ship_y_line1
            # All asteroids visible
            for i, (lx, ly) in enumerate(ALL_POS):
                draw_asteroid(draw, lx, ly, ASTEROID_R, i * 13)

        elif frame < p2_end:
            # SHOOTING LINE 1
            local = frame - p1_end
            idx = local // FRAMES_PER_LETTER
            sub = local % FRAMES_PER_LETTER

            # Ship position
            target = L1_POS[min(idx, len(L1_POS) - 1)][0]
            prev = L1_POS[max(0, idx - 1)][0] if idx > 0 else L1_POS[0][0]
            if sub <= 1:
                ship_x = prev + (target - prev) * ease_in_out(min(1.0, sub / 1.5))
            else:
                ship_x = target
            ship_y = ship_y_line1

            # Mark previous as done
            for i in range(idx):
                revealed[i] = True
                exploding[i] = 1.0

            # Current letter
            if idx < len(LINE1):
                if sub == 2:
                    lx, ly = L1_POS[idx]
                    draw_laser(draw, ship_x, ship_y - 16, lx, ly, 0.5)
                elif sub == 3:
                    lx, ly = L1_POS[idx]
                    draw_laser(draw, ship_x, ship_y - 16, lx, ly, 1.0)
                    exploding[idx] = 0.2
                elif sub >= 4:
                    exploding[idx] = (sub - 3) / 3.0
                    if sub >= 4:
                        revealed[idx] = True

            # Draw all asteroids/effects for ALL letters
            for i, (lx, ly) in enumerate(ALL_POS):
                if not revealed[i] and exploding[i] == 0:
                    draw_asteroid(draw, lx, ly, ASTEROID_R, i * 13)
                elif 0 < exploding[i] < 1.0:
                    draw_explosion(draw, lx, ly, exploding[i], i * 13)
                    if revealed[i]:
                        draw_letter_glow(draw, ALL_LETTERS[i], lx, ly, ALL_FONTS[i], exploding[i])
                elif revealed[i]:
                    draw_letter_glow(draw, ALL_LETTERS[i], lx, ly, ALL_FONTS[i], 1.0)

        elif frame < p3_end:
            # TRANSITION: ship moves from last L1 pos to first L2 pos
            local = frame - p2_end
            progress = local / TRANSITION_FRAMES
            # All line 1 revealed
            for i in range(len(LINE1)):
                revealed[i] = True
                exploding[i] = 1.0
            from_x = L1_POS[-1][0]
            to_x = L2_POS[0][0]
            ship_x = from_x + (to_x - from_x) * ease_in_out(progress)
            ship_y = ship_y_line2

            for i, (lx, ly) in enumerate(ALL_POS):
                if not revealed[i] and exploding[i] == 0:
                    draw_asteroid(draw, lx, ly, ASTEROID_R, i * 13)
                elif revealed[i]:
                    draw_letter_glow(draw, ALL_LETTERS[i], lx, ly, ALL_FONTS[i], 1.0)

        elif frame < p4_end:
            # SHOOTING LINE 2
            local = frame - p3_end
            idx = local // FRAMES_PER_LETTER
            sub = local % FRAMES_PER_LETTER
            global_idx = len(LINE1) + idx

            # All line 1 done
            for i in range(len(LINE1)):
                revealed[i] = True
                exploding[i] = 1.0

            # Ship position
            target = L2_POS[min(idx, len(L2_POS) - 1)][0]
            prev = L2_POS[max(0, idx - 1)][0] if idx > 0 else L2_POS[0][0]
            if sub <= 1:
                ship_x = prev + (target - prev) * ease_in_out(min(1.0, sub / 1.5))
            else:
                ship_x = target
            ship_y = ship_y_line2

            # Mark previous line2 letters
            for i in range(len(LINE1), len(LINE1) + idx):
                revealed[i] = True
                exploding[i] = 1.0

            if global_idx < num_total:
                if sub == 2:
                    lx, ly = ALL_POS[global_idx]
                    draw_laser(draw, ship_x, ship_y - 16, lx, ly, 0.5)
                elif sub == 3:
                    lx, ly = ALL_POS[global_idx]
                    draw_laser(draw, ship_x, ship_y - 16, lx, ly, 1.0)
                    exploding[global_idx] = 0.2
                elif sub >= 4:
                    exploding[global_idx] = (sub - 3) / 3.0
                    if sub >= 4:
                        revealed[global_idx] = True

            for i, (lx, ly) in enumerate(ALL_POS):
                if not revealed[i] and exploding[i] == 0:
                    draw_asteroid(draw, lx, ly, ASTEROID_R, i * 13)
                elif 0 < exploding[i] < 1.0:
                    draw_explosion(draw, lx, ly, exploding[i], i * 13)
                    if revealed[i]:
                        draw_letter_glow(draw, ALL_LETTERS[i], lx, ly, ALL_FONTS[i], exploding[i])
                elif revealed[i]:
                    draw_letter_glow(draw, ALL_LETTERS[i], lx, ly, ALL_FONTS[i], 1.0)

        else:
            # OUTRO: all revealed, ship flies away, text pulses
            local = frame - p4_end
            progress = local / OUTRO_FRAMES

            for i in range(num_total):
                revealed[i] = True
                exploding[i] = 1.0

            ship_x = L2_POS[-1][0] + progress * (WIDTH + 60 - L2_POS[-1][0])
            ship_y = ship_y_line2 - progress * 120
            if progress > 0.6:
                show_ship = False

            pulse = 0.85 + 0.15 * math.sin(local * 0.6)
            for i, (lx, ly) in enumerate(ALL_POS):
                draw_letter_glow(draw, ALL_LETTERS[i], lx, ly, ALL_FONTS[i], pulse)

            # Subtitle fades in
            if progress > 0.25:
                sub_a = min(1.0, (progress - 0.25) / 0.35)
                subtitle = "Senior Solution Engineer  •  Apps & AI  •  Microsoft"
                bb = sub_font.getbbox(subtitle)
                sw = bb[2] - bb[0]
                sx = (WIDTH - sw) // 2
                # Neon magenta subtitle
                sc = tuple(int(v * sub_a) for v in (255, 80, 180))
                draw.text((sx, 232), subtitle, font=sub_font, fill=sc)

        # Draw ship
        if show_ship and -50 < ship_x < WIDTH + 60:
            draw_ship(draw, ship_x, ship_y)

        # CRT effect
        img = apply_crt_effect(img, frame)

        frames.append(img)
        if frame % 20 == 0:
            print(f"  Frame {frame}/{TOTAL_FRAMES}")

    return frames


def main():
    print(f"Generating cyberpunk GIF ({TOTAL_FRAMES} frames)...")
    frames = generate_frames()

    # Hold final frame
    for _ in range(10):
        frames.append(frames[-1])

    output = "/Users/jeffreygroneberg/GitRepos/jeffreygroneberg/assets/header.gif"
    os.makedirs(os.path.dirname(output), exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:],
                   duration=FRAME_MS, loop=0, optimize=True)
    size_kb = os.path.getsize(output) / 1024
    print(f"Saved: {output} ({len(frames)} frames, {size_kb:.0f}KB)")


if __name__ == "__main__":
    main()

