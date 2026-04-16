#!/usr/bin/env python3
"""Generate an asteroid-game themed GIF that reveals 'JEFFREY'."""

import math
import random
from PIL import Image, ImageDraw, ImageFont

random.seed(42)

WIDTH, HEIGHT = 840, 320
BG_COLOR = (10, 10, 30)
STAR_COLOR = (200, 200, 255)
LASER_COLOR = (0, 255, 100)
SHIP_COLOR = (0, 200, 255)
ASTEROID_COLOR = (140, 120, 100)
ASTEROID_DARK = (90, 75, 60)
LETTER_COLOR = (0, 220, 255)
GLOW_COLOR = (0, 180, 255)
EXPLOSION_COLORS = [(255, 200, 50), (255, 140, 30), (255, 80, 20), (200, 60, 10)]
TEXT = "JEFFREY"
FPS = 18
FRAME_DURATION_MS = int(1000 / FPS)

font_path = "/System/Library/Fonts/Supplemental/Impact.ttf"
letter_font = ImageFont.truetype(font_path, 72)
small_font = ImageFont.truetype(font_path, 28)

# Pre-compute letter positions (centered horizontally)
LETTER_SPACING = 95
total_width = len(TEXT) * LETTER_SPACING
start_x = (WIDTH - total_width) // 2 + LETTER_SPACING // 2
letter_positions = [(start_x + i * LETTER_SPACING, 110) for i in range(len(TEXT))]

# Generate star field
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT),
          random.uniform(0.3, 1.0), random.uniform(0.5, 2.0)) for _ in range(120)]


def draw_stars(draw, frame):
    for sx, sy, brightness, speed in stars:
        flicker = 0.7 + 0.3 * math.sin(frame * speed * 0.3 + sx)
        b = int(255 * brightness * flicker)
        c = (b, b, min(255, b + 30))
        r = 1 if brightness < 0.6 else 2
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=c)


def draw_ship(draw, x, y, scale=1.0):
    s = 12 * scale
    # Main body
    pts = [(x, y - s * 1.5), (x - s, y + s), (x + s, y + s)]
    draw.polygon(pts, fill=SHIP_COLOR, outline=(100, 230, 255))
    # Engine glow
    glow_pts = [(x - s * 0.4, y + s), (x, y + s * 1.6), (x + s * 0.4, y + s)]
    draw.polygon(glow_pts, fill=(0, 150, 255, 180))
    # Cockpit
    draw.ellipse([x - 3, y - 4, x + 3, y + 4], fill=(200, 240, 255))


def draw_asteroid(draw, cx, cy, radius, seed_val):
    rng = random.Random(seed_val)
    num_pts = 10
    points = []
    for i in range(num_pts):
        angle = (2 * math.pi / num_pts) * i
        r = radius + rng.uniform(-radius * 0.3, radius * 0.3)
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        points.append((px, py))
    draw.polygon(points, fill=ASTEROID_COLOR, outline=ASTEROID_DARK)
    # Craters
    for _ in range(3):
        cr = rng.uniform(3, 8)
        ca = rng.uniform(0, 2 * math.pi)
        cd = rng.uniform(2, radius * 0.5)
        crx = cx + cd * math.cos(ca)
        cry = cy + cd * math.sin(ca)
        draw.ellipse([crx - cr, cry - cr, crx + cr, cry + cr], fill=ASTEROID_DARK)


def draw_explosion(draw, cx, cy, progress, seed_val):
    """progress: 0.0 to 1.0"""
    rng = random.Random(seed_val + 999)
    num_particles = 20
    for i in range(num_particles):
        angle = rng.uniform(0, 2 * math.pi)
        max_dist = rng.uniform(20, 60)
        dist = max_dist * progress
        size = max(1, int(5 * (1 - progress * 0.7)))
        px = cx + dist * math.cos(angle)
        py = cy + dist * math.sin(angle)
        color_idx = min(len(EXPLOSION_COLORS) - 1, int(progress * len(EXPLOSION_COLORS)))
        c = EXPLOSION_COLORS[color_idx]
        alpha = max(0, 1 - progress)
        c_faded = tuple(int(v * alpha) for v in c)
        draw.ellipse([px - size, py - size, px + size, py + size], fill=c_faded)


def draw_laser(draw, x_from, y_from, x_to, y_to, progress):
    """Draw a laser beam from ship to target."""
    tip_y = y_from - (y_from - y_to) * min(1.0, progress * 2)
    tail_y = y_from - (y_from - y_to) * max(0, progress * 2 - 0.5)
    if tip_y < tail_y:
        draw.line([(x_from, tail_y), (x_to, tip_y)], fill=LASER_COLOR, width=3)
        # Glow
        draw.line([(x_from - 1, tail_y), (x_to - 1, tip_y)], fill=(100, 255, 150, 128), width=1)
        draw.line([(x_from + 1, tail_y), (x_to + 1, tip_y)], fill=(100, 255, 150, 128), width=1)


def draw_letter_glow(draw, letter, cx, cy, glow_amount=1.0):
    """Draw a letter with glow effect."""
    bbox = letter_font.getbbox(letter)
    lw = bbox[2] - bbox[0]
    lh = bbox[3] - bbox[1]
    lx = cx - lw // 2
    ly = cy - lh // 2
    # Glow layers
    for offset in range(3, 0, -1):
        g = int(40 * glow_amount * (4 - offset) / 3)
        gc = (0, g, int(g * 1.2))
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                draw.text((lx + dx, ly + dy), letter, font=letter_font, fill=gc)
    # Main letter
    alpha = min(1.0, glow_amount)
    c = tuple(int(v * alpha) for v in LETTER_COLOR)
    draw.text((lx, ly), letter, font=letter_font, fill=c)


def generate_frames():
    frames = []

    # --- Timeline ---
    # Phase 0: Intro with ship flying in (frames 0-14)
    # Phase 1: Shooting each asteroid (frames 15-77, ~9 frames per letter)
    # Phase 2: Reveal & glow (frames 78-100)

    INTRO_FRAMES = 12
    FRAMES_PER_LETTER = 9
    OUTRO_FRAMES = 18
    TOTAL = INTRO_FRAMES + len(TEXT) * FRAMES_PER_LETTER + OUTRO_FRAMES

    # Ship animation
    ship_start_x = -30
    ship_start_y = HEIGHT - 40

    # Track state
    revealed = [False] * len(TEXT)
    exploding = [0.0] * len(TEXT)  # explosion progress per letter

    for frame in range(TOTAL):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Stars
        draw_stars(draw, frame)

        # Determine which phase
        if frame < INTRO_FRAMES:
            # Intro: ship flies in from left
            progress = frame / INTRO_FRAMES
            ship_x = ship_start_x + (letter_positions[0][0] - ship_start_x) * ease_in_out(progress)
            ship_y = ship_start_y

            # Draw all asteroids
            for i, (lx, ly) in enumerate(letter_positions):
                draw_asteroid(draw, lx, ly, 38, i * 7)

        elif frame < INTRO_FRAMES + len(TEXT) * FRAMES_PER_LETTER:
            # Shooting phase
            local_frame = frame - INTRO_FRAMES
            letter_idx = local_frame // FRAMES_PER_LETTER
            sub_frame = local_frame % FRAMES_PER_LETTER

            # Ship position: lerp between current and next letter
            if letter_idx < len(TEXT):
                target_x = letter_positions[letter_idx][0]
            else:
                target_x = letter_positions[-1][0]

            if letter_idx > 0:
                prev_x = letter_positions[letter_idx - 1][0]
            else:
                prev_x = letter_positions[0][0]

            # Ship moves to target in first 2 frames, then stays
            if sub_frame <= 2:
                move_progress = min(1.0, sub_frame / 2.0)
                ship_x = prev_x + (target_x - prev_x) * ease_in_out(move_progress)
            else:
                ship_x = target_x
            ship_y = ship_start_y

            # Mark previous letters as revealed
            for i in range(letter_idx):
                revealed[i] = True
                exploding[i] = 1.0

            # Current letter: shooting at frames 3-4, exploding at 5-8
            if letter_idx < len(TEXT):
                if sub_frame == 3 or sub_frame == 4:
                    # Laser firing
                    lx, ly = letter_positions[letter_idx]
                    laser_progress = (sub_frame - 3) / 2.0
                    draw_laser(draw, ship_x, ship_y - 18, lx, ly, laser_progress)
                elif sub_frame >= 5:
                    # Explosion
                    exploding[letter_idx] = (sub_frame - 5) / 4.0
                    if sub_frame >= 7:
                        revealed[letter_idx] = True

            # Draw asteroids and effects
            for i, (lx, ly) in enumerate(letter_positions):
                if not revealed[i] and exploding[i] == 0:
                    draw_asteroid(draw, lx, ly, 38, i * 7)
                elif exploding[i] > 0 and exploding[i] < 1.0:
                    draw_explosion(draw, lx, ly, exploding[i], i * 7)
                    if revealed[i]:
                        draw_letter_glow(draw, TEXT[i], lx, ly, exploding[i])
                elif revealed[i]:
                    draw_letter_glow(draw, TEXT[i], lx, ly, 1.0)

        else:
            # Outro: all revealed, ship flies away, letters pulse
            outro_frame = frame - (INTRO_FRAMES + len(TEXT) * FRAMES_PER_LETTER)
            progress = outro_frame / OUTRO_FRAMES

            ship_x = letter_positions[-1][0] + progress * (WIDTH + 50 - letter_positions[-1][0])
            ship_y = ship_start_y - progress * 100

            # Draw all letters with pulsing glow
            pulse = 0.85 + 0.15 * math.sin(outro_frame * 0.8)
            for i, (lx, ly) in enumerate(letter_positions):
                draw_letter_glow(draw, TEXT[i], lx, ly, pulse)

            # Subtitle fades in
            if progress > 0.3:
                sub_alpha = min(1.0, (progress - 0.3) / 0.4)
                subtitle = "Senior Solution Engineer • Apps & AI • Microsoft"
                bbox = small_font.getbbox(subtitle)
                sw = bbox[2] - bbox[0]
                sx = (WIDTH - sw) // 2
                sc = tuple(int(v * sub_alpha) for v in (180, 200, 220))
                draw.text((sx, 195), subtitle, font=small_font, fill=sc)

        # Draw ship (unless out of frame in outro)
        if ship_x < WIDTH + 50 and ship_y > -50:
            draw_ship(draw, ship_x, ship_y)

        # Scanline overlay for retro feel
        for y in range(0, HEIGHT, 4):
            draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, 10), width=1)

        frames.append(img)

    return frames


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def main():
    print("Generating asteroid game GIF...")
    frames = generate_frames()

    # Duplicate last few frames for a pause
    for _ in range(8):
        frames.append(frames[-1])

    output_path = "/Users/jeffreygroneberg/GitRepos/jeffreygroneberg/assets/header.gif"
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True,
    )
    print(f"Saved to {output_path} ({len(frames)} frames, {len(frames) * FRAME_DURATION_MS}ms)")


if __name__ == "__main__":
    main()
