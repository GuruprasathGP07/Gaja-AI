"""
tools/build_dataset.py - Dataset splitter with group-aware deduplication and split creation.

Arranges downloaded or generated raw dataset images into data/train, data/val, data/test (70/15/15).
Groups images by observation/prefix to prevent data leakage across splits.
Removes exact duplicate images via SHA-256 hashing.
"""

import os
import shutil
import hashlib
import random
import argparse
from collections import defaultdict
from PIL import Image

CLASSES = ['elephant', 'other_animal', 'no_animal']

def get_image_hash(filepath):
    """Compute SHA-256 hash of image pixels to detect exact duplicates."""
    try:
        with Image.open(filepath) as img:
            # Convert to uniform mode & size for perceptual/pixel hashing comparison
            img_gray = img.convert('L').resize((64, 64))
            return hashlib.sha256(img_gray.tobytes()).hexdigest()
    except Exception:
        # Fall back to raw file hash
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

def extract_group_id(filename):
    """
    Extract group ID from filename to prevent data leakage.
    If sequence tag present, group by sequence; otherwise use item index to ensure
    balanced splits across train, val, and test.
    """
    stem = os.path.splitext(filename)[0]
    parts = stem.split('_')
    if 'seq' in stem.lower() and len(parts) >= 2:
        return "_".join(parts[:2])
    # Group by individual file stem for synthetic/independent image samples
    return stem

def build_dataset(src_dir='data/raw_smoke', dest_dir='data', train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=42):
    """Build structured dataset splits from raw directory."""
    random.seed(seed)
    assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Ratios must sum to 1.0"

    print(f"[build_dataset] Ingesting from {src_dir} into {dest_dir}...")

    # Clear destination train, val, test directories if they exist
    for split in ['train', 'val', 'test']:
        split_dir = os.path.join(dest_dir, split)
        if os.path.exists(split_dir):
            shutil.rmtree(split_dir)
        for cls in CLASSES:
            os.makedirs(os.path.join(split_dir, cls), exist_ok=True)

    seen_hashes = set()
    total_raw = 0
    duplicates_removed = 0
    corrupt_skipped = 0

    for cls in CLASSES:
        cls_src_dir = os.path.join(src_dir, cls)
        if not os.path.exists(cls_src_dir):
            print(f"[WARNING] Source directory {cls_src_dir} does not exist. Skipping.")
            continue

        # Collect unique valid files grouped by group_id
        groups = defaultdict(list)
        files = os.listdir(cls_src_dir)

        for fname in files:
            fpath = os.path.join(cls_src_dir, fname)
            if not os.path.isfile(fpath) or not fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue

            total_raw += 1
            # Check validity
            try:
                with Image.open(fpath) as img:
                    img.verify()
            except Exception:
                corrupt_skipped += 1
                continue

            # Check duplicate hash
            img_hash = get_image_hash(fpath)
            if img_hash in seen_hashes:
                duplicates_removed += 1
                continue
            seen_hashes.add(img_hash)

            gid = extract_group_id(fname)
            groups[gid].append((fname, fpath))

        # Split groups into train / val / test
        group_keys = list(groups.keys())
        random.shuffle(group_keys)

        num_groups = len(group_keys)
        n_train = int(num_groups * train_ratio)
        n_val = int(num_groups * val_ratio)

        train_groups = set(group_keys[:n_train])
        val_groups = set(group_keys[n_train:n_train + n_val])
        test_groups = set(group_keys[n_train + n_val:])

        counts = {'train': 0, 'val': 0, 'test': 0}

        for gid, item_list in groups.items():
            if gid in train_groups:
                target_split = 'train'
            elif gid in val_groups:
                target_split = 'val'
            else:
                target_split = 'test'

            for fname, fpath in item_list:
                dest_fpath = os.path.join(dest_dir, target_split, cls, fname)
                shutil.copy2(fpath, dest_fpath)
                counts[target_split] += 1

        print(f"  Class '{cls}': train={counts['train']}, val={counts['val']}, test={counts['test']} (Groups: {len(groups)})")

    print(f"\n[build_dataset] Complete! Total raw: {total_raw}, Duplicates removed: {duplicates_removed}, Corrupt skipped: {corrupt_skipped}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Build train/val/test splits")
    parser.add_argument('--src-dir', default='data/raw_smoke', help='Source raw data directory')
    parser.add_argument('--dest-dir', default='data', help='Destination data directory')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    build_dataset(args.src_dir, args.dest_dir, seed=args.seed)
