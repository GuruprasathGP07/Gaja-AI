"""
tools/audit_dataset.py - Dataset auditor and leakage validator.

Audits dataset splits: reports class counts, corrupt images, resolution bounds,
class imbalance, and checks for cross-split duplicate hashes.
Fails loudly if data leakage or severe corruptions are detected.
"""

import os
import sys
import hashlib
import argparse
from PIL import Image

CLASSES = ['elephant', 'other_animal', 'no_animal']
SPLITS = ['train', 'val', 'test']

def get_image_hash(filepath):
    """Compute SHA-256 hash of image content."""
    try:
        with Image.open(filepath) as img:
            img_gray = img.convert('L').resize((64, 64))
            return hashlib.sha256(img_gray.tobytes()).hexdigest()
    except Exception:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

def audit_dataset(data_dir='data'):
    """Audit the dataset directory and enforce strict data integrity rules."""
    print(f"=" * 60)
    print(f"GAJAALERT DATASET AUDIT REPORT: {os.path.abspath(data_dir)}")
    print(f"=" * 60)

    split_hashes = {}
    split_counts = {split: {cls: 0 for cls in CLASSES} for split in SPLITS}
    corrupt_files = []
    tiny_files = []
    total_images = 0

    for split in SPLITS:
        split_dir = os.path.join(data_dir, split)
        hashes = {}

        if not os.path.exists(split_dir):
            print(f"[ERROR] Split directory missing: {split_dir}")
            sys.exit(1)

        for cls in CLASSES:
            cls_dir = os.path.join(split_dir, cls)
            if not os.path.exists(cls_dir):
                print(f"[WARNING] Class directory missing: {cls_dir}")
                continue

            for fname in os.listdir(cls_dir):
                fpath = os.path.join(cls_dir, fname)
                if not os.path.isfile(fpath) or fname.startswith('.'):
                    continue

                total_images += 1
                try:
                    with Image.open(fpath) as img:
                        w, h = img.size
                        img.verify()
                        if w < 64 or h < 64:
                            tiny_files.append((fpath, w, h))
                except Exception as e:
                    corrupt_files.append((fpath, str(e)))
                    continue

                # Hash check
                hval = get_image_hash(fpath)
                hashes[fpath] = hval
                split_counts[split][cls] += 1

        split_hashes[split] = hashes

    # Display counts table
    print("\n[SUMMARY] Image Counts per Split & Class:")
    header = f"{'Class':<15} | {'Train':<8} | {'Val':<8} | {'Test':<8} | {'Total':<8}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    class_totals = {cls: 0 for cls in CLASSES}
    for cls in CLASSES:
        tr = split_counts['train'][cls]
        va = split_counts['val'][cls]
        te = split_counts['test'][cls]
        tot = tr + va + te
        class_totals[cls] = tot
        print(f"{cls:<15} | {tr:<8} | {va:<8} | {te:<8} | {tot:<8}")

    print("-" * len(header))

    # Check for corrupt or tiny files
    print(f"\n[CORRUPTION & QUALITY AUDIT]")
    print(f"  Total verified images: {total_images}")
    print(f"  Corrupt images: {len(corrupt_files)}")
    print(f"  Tiny images (<64x64): {len(tiny_files)}")

    if corrupt_files:
        print("\n  Corrupt Files Found:")
        for fp, err in corrupt_files[:5]:
            print(f"    - {fp}: {err}")

    # Check cross-split duplicate hashes (Data Leakage!)
    print(f"\n[DATA LEAKAGE AUDIT]")
    leakage_detected = False

    all_split_pairs = [('train', 'val'), ('train', 'test'), ('val', 'test')]
    for s1, s2 in all_split_pairs:
        h1 = set(split_hashes[s1].values())
        h2 = set(split_hashes[s2].values())
        common = h1.intersection(h2)
        if common:
            leakage_detected = True
            print(f"  [FAIL] LEAKAGE DETECTED between '{s1}' and '{s2}'! {len(common)} duplicate images found across splits!")

    if not leakage_detected:
        print("  [PASS] Zero cross-split duplicates detected across train, val, and test splits!")

    # Check class imbalance
    print(f"\n[CLASS BALANCE AUDIT]")
    tot_sum = sum(class_totals.values())
    if tot_sum > 0:
        for cls, count in class_totals.items():
            pct = (count / tot_sum) * 100
            print(f"  - {cls}: {count} ({pct:.1f}%)")

    print("\n" + "=" * 60)
    if leakage_detected or len(corrupt_files) > 0:
        print("[AUDIT RESULT] AUDIT FAILED! Address data leakage/corruption before proceeding.")
        sys.exit(1)
    else:
        print("[AUDIT RESULT] AUDIT PASSED! Dataset structure is clean and leak-free.")
        print("=" * 60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Audit dataset for leakage and quality")
    parser.add_argument('--data-dir', default='data', help='Data directory containing train/val/test')
    args = parser.parse_args()

    audit_dataset(args.data_dir)
