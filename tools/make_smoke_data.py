"""
tools/make_smoke_data.py - Synthetic dataset generator for pipeline verification.

Generates synthetic images for 'elephant', 'other_animal', and 'no_animal' classes
across day, dusk, and simulated night conditions to verify training and evaluation
pipelines without requiring external downloads.
"""

import os
import random
import argparse
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np

CLASSES = ['elephant', 'other_animal', 'no_animal']
TIME_MODES = ['day', 'dusk', 'night']

def generate_background(width=224, height=224, time_mode='day'):
    """Generate a realistic landscape background based on time mode."""
    # Base terrain colors (green/brown forest/field)
    if time_mode == 'day':
        sky_color = (random.randint(130, 180), random.randint(180, 220), random.randint(230, 255))
        ground_color = (random.randint(30, 80), random.randint(90, 140), random.randint(20, 60))
    elif time_mode == 'dusk':
        sky_color = (random.randint(200, 240), random.randint(100, 140), random.randint(50, 90))
        ground_color = (random.randint(40, 70), random.randint(50, 80), random.randint(20, 40))
    else: # night
        sky_color = (random.randint(5, 20), random.randint(10, 30), random.randint(20, 45))
        ground_color = (random.randint(10, 25), random.randint(15, 30), random.randint(10, 25))

    img = Image.new('RGB', (width, height), sky_color)
    draw = ImageDraw.Draw(img)

    # Draw ground horizon
    horizon = random.randint(height // 3, height // 2)
    draw.rectangle([0, horizon, width, height], fill=ground_color)

    # Add trees/bushes (greenish/dark blobs)
    for _ in range(random.randint(3, 8)):
        tx = random.randint(0, width)
        ty = random.randint(horizon - 30, horizon + 20)
        tr = random.randint(10, 30)
        leaf_color = (
            max(0, ground_color[0] + random.randint(-15, 15)),
            max(0, ground_color[1] + random.randint(-15, 15)),
            max(0, ground_color[2] + random.randint(-15, 15))
        )
        draw.ellipse([tx - tr, ty - tr, tx + tr, ty + tr], fill=leaf_color)

    return img

def draw_elephant(draw, time_mode):
    """Draw a characteristic elephant shape (large body, head, trunk, ears, legs)."""
    # Color: dark greyish
    if time_mode == 'day':
        color = (random.randint(70, 95), random.randint(70, 95), random.randint(75, 100))
    elif time_mode == 'dusk':
        color = (random.randint(40, 65), random.randint(40, 65), random.randint(45, 70))
    else:
        color = (random.randint(15, 30), random.randint(15, 30), random.randint(20, 35))

    cx = random.randint(80, 140)
    cy = random.randint(110, 160)

    # Body
    draw.ellipse([cx - 45, cy - 30, cx + 25, cy + 25], fill=color)
    # Head
    draw.ellipse([cx - 65, cy - 40, cx - 35, cy - 5], fill=color)
    # Large Ear
    draw.ellipse([cx - 55, cy - 42, cx - 35, cy - 10], fill=(color[0]+10, color[1]+10, color[2]+10))
    # Trunk
    draw.line([(cx - 60, cy - 15), (cx - 70, cy + 10), (cx - 65, cy + 25)], fill=color, width=8)
    # Tusks (white/cream)
    if random.random() > 0.3:
        tusk_color = (220, 220, 200) if time_mode != 'night' else (80, 80, 75)
        draw.line([(cx - 55, cy - 5), (cx - 68, cy + 5)], fill=tusk_color, width=3)
    # Legs
    draw.rectangle([cx - 40, cy + 15, cx - 28, cy + 45], fill=color)
    draw.rectangle([cx - 20, cy + 15, cx - 8, cy + 45], fill=color)
    draw.rectangle([cx + 2, cy + 15, cx + 14, cy + 45], fill=color)

def draw_other_animal(draw, time_mode):
    """Draw cattle/deer/gaur shape."""
    if time_mode == 'day':
        color = (random.randint(140, 190), random.randint(90, 120), random.randint(40, 70)) # reddish brown
    elif time_mode == 'dusk':
        color = (random.randint(80, 120), random.randint(50, 80), random.randint(25, 45))
    else:
        color = (random.randint(20, 35), random.randint(15, 30), random.randint(10, 20))

    cx = random.randint(80, 140)
    cy = random.randint(120, 160)

    # Smaller body
    draw.ellipse([cx - 30, cy - 20, cx + 20, cy + 15], fill=color)
    # Neck and small head
    draw.line([(cx - 25, cy - 10), (cx - 35, cy - 35)], fill=color, width=10)
    draw.ellipse([cx - 45, cy - 42, cx - 28, cy - 28], fill=color)
    # Legs (thinner)
    draw.line([(cx - 25, cy + 10), (cx - 25, cy + 40)], fill=color, width=4)
    draw.line([(cx - 10, cy + 10), (cx - 10, cy + 40)], fill=color, width=4)
    draw.line([(cx + 10, cy + 10), (cx + 10, cy + 40)], fill=color, width=4)

def draw_no_animal_clutter(draw, time_mode):
    """Draw rocks, fence posts, or stumps that might look like animal shapes."""
    rock_color = (random.randint(80, 110), random.randint(80, 110), random.randint(80, 110))
    if time_mode == 'night':
        rock_color = (random.randint(20, 35), random.randint(20, 35), random.randint(20, 35))

    cx = random.randint(60, 160)
    cy = random.randint(130, 170)
    # Rock / boulder
    draw.ellipse([cx - 25, cy - 15, cx + 25, cy + 15], fill=rock_color)
    # Fence post
    draw.rectangle([cx + 40, cy - 40, cx + 46, cy + 20], fill=(60, 40, 20) if time_mode != 'night' else (15, 12, 10))

def apply_night_effects(img):
    """Apply realistic camera-trap night filter (low light + blue-grey tint + noise)."""
    # Convert to numpy array
    arr = np.array(img, dtype=np.float32)
    # Darken
    arr *= random.uniform(0.2, 0.45)
    # Tint (slightly bluish/greyish camera trap IR feel)
    arr[:, :, 0] *= 0.85 # Red
    arr[:, :, 1] *= 0.95 # Green
    arr[:, :, 2] *= 1.10 # Blue
    # Add noise
    noise = np.random.normal(0, 8, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def make_smoke_data(output_dir='data/raw_smoke', num_per_class=100):
    """Generate synthetic smoke images organized by class."""
    os.makedirs(output_dir, exist_ok=True)
    count = 0
    for cls in CLASSES:
        cls_dir = os.path.join(output_dir, cls)
        os.makedirs(cls_dir, exist_ok=True)

        for i in range(num_per_class):
            time_mode = random.choice(TIME_MODES)
            img = generate_background(224, 224, time_mode)
            draw = ImageDraw.Draw(img)

            if cls == 'elephant':
                draw_elephant(draw, time_mode)
            elif cls == 'other_animal':
                draw_other_animal(draw, time_mode)
            else: # no_animal
                if random.random() > 0.4:
                    draw_no_animal_clutter(draw, time_mode)

            # Apply blur / texture
            img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.8)))

            if time_mode == 'night':
                img = apply_night_effects(img)

            filename = f"{cls}_{time_mode}_{i+1:04d}.jpg"
            img.save(os.path.join(cls_dir, filename), quality=90)
            count += 1

    print(f"[make_smoke_data] Successfully generated {count} synthetic images in {output_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate synthetic smoke dataset")
    parser.add_argument('--output-dir', default='data/raw_smoke', help='Output raw directory')
    parser.add_argument('--num-per-class', type=int, default=150, help='Number of images per class')
    args = parser.parse_args()

    make_smoke_data(args.output_dir, args.num_per_class)
