"""
evaluate.py - Quantitative Model Evaluator & Night Robustness Benchmarker.

Evaluates both baseline and night-augmented models on clean held-out test split
and simulated night test split. Generates confusion matrices, per-class metrics,
and saves results to results/metrics.json and PNG plots.
"""

import os
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from PIL import Image

from common import (
    CLASSES, MODEL_PATH, BASELINE_MODEL_PATH, RESULTS_DIR, METRICS_PATH
)

def simulate_night_image(img_arr):
    """
    Apply fixed deterministic simulated night filter:
    - Brightness scaling x0.30
    - Tint (0.85, 0.95, 1.10)
    - Fixed noise (seed=42, stddev=8.0)
    """
    img_float = img_arr.astype(np.float32)
    # Darken
    img_dark = img_float * 0.30
    # Tint
    tint = np.array([0.85, 0.95, 1.10], dtype=np.float32)
    img_tinted = img_dark * tint
    # Seeded noise
    np.random.seed(42)
    noise = np.random.normal(0, 8.0, img_tinted.shape)
    img_noisy = np.clip(img_tinted + noise, 0, 255).astype(np.uint8)
    return img_noisy

def load_test_dataset(test_dir='data/test'):
    """Load test images and ground truth labels directly."""
    images_clean = []
    images_night = []
    labels = []
    filepaths = []

    for idx, cls in enumerate(CLASSES):
        cls_dir = os.path.join(test_dir, cls)
        if not os.path.exists(cls_dir):
            continue

        for fname in os.listdir(cls_dir):
            fpath = os.path.join(cls_dir, fname)
            if not os.path.isfile(fpath) or fname.startswith('.'):
                continue

            try:
                with Image.open(fpath) as img:
                    img_rgb = img.convert('RGB').resize((224, 224))
                    arr_clean = np.array(img_rgb, dtype=np.uint8)
                    arr_night = simulate_night_image(arr_clean)

                    images_clean.append(arr_clean)
                    images_night.append(arr_night)
                    labels.append(idx)
                    filepaths.append(fpath)
            except Exception as e:
                print(f"[WARNING] Could not load {fpath}: {e}")

    return (
        np.array(images_clean),
        np.array(images_night),
        np.array(labels),
        filepaths
    )

def compute_metrics(y_true, y_pred_probs):
    """Compute confusion matrix, precision, recall, and F1 score per class."""
    y_pred = np.argmax(y_pred_probs, axis=1)
    num_classes = len(CLASSES)
    cm = np.zeros((num_classes, num_classes), dtype=int)

    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1

    per_class = {}
    for i, cls_name in enumerate(CLASSES):
        tp = cm[i, i]
        fp = np.sum(cm[:, i]) - tp
        fn = np.sum(cm[i, :]) - tp

        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        per_class[cls_name] = {
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'support': int(np.sum(cm[i, :]))
        }

    overall_acc = float(np.trace(cm) / np.sum(cm)) if np.sum(cm) > 0 else 0.0

    return {
        'overall_accuracy': round(overall_acc, 4),
        'confusion_matrix': cm.tolist(),
        'per_class': per_class,
        'elephant_precision': per_class['elephant']['precision'],
        'elephant_recall': per_class['elephant']['recall']
    }

def plot_confusion_matrix(cm, title, save_filename):
    """Plot and save confusion matrix heatmaps."""
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    cax = ax.matshow(cm, cmap='Blues', alpha=0.8)

    for i in range(len(CLASSES)):
        for j in range(len(CLASSES)):
            ax.text(j, i, str(cm[i][j]), ha='center', va='center', color='black', fontsize=12, fontweight='bold')

    fig.colorbar(cax)
    ax.set_xticks(range(len(CLASSES)))
    ax.set_yticks(range(len(CLASSES)))
    ax.set_xticklabels(CLASSES, rotation=15)
    ax.set_yticklabels(CLASSES)
    ax.set_xlabel('Predicted Label', fontweight='bold')
    ax.set_ylabel('True Label', fontweight='bold')
    ax.set_title(title, pad=15, fontweight='bold')

    plt.tight_layout()
    plot_path = os.path.join(RESULTS_DIR, save_filename)
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"[evaluate.py] Saved confusion matrix plot to {plot_path}")

def plot_pr_tradeoff(y_true, y_probs, save_filename='precision_recall_tradeoff.png'):
    """Plot Precision-Recall curve for elephant detection across confidence thresholds."""
    elephant_true = (y_true == 0).astype(int)
    elephant_probs = y_probs[:, 0]

    thresholds = np.linspace(0.0, 1.0, 101)
    precisions = []
    recalls = []

    for t in thresholds:
        preds = (elephant_probs >= t).astype(int)
        tp = np.sum((preds == 1) & (elephant_true == 1))
        fp = np.sum((preds == 1) & (elephant_true == 0))
        fn = np.sum((preds == 0) & (elephant_true == 1))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        precisions.append(prec)
        recalls.append(rec)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(recalls, precisions, color='#0284c7', linewidth=2.5, label='Elephant PR Curve')
    ax.scatter([recalls[60]], [precisions[60]], color='#dc2626', s=80, label='Default Threshold (0.60)', zorder=5)
    ax.scatter([recalls[85]], [precisions[85]], color='#059669', s=80, label='Medium Risk Threshold (0.85)', zorder=5)

    ax.set_title('Precision-Recall Tradeoff (Elephant Detection)', fontweight='bold')
    ax.set_xlabel('Recall (Sensitivity)', fontweight='bold')
    ax.set_ylabel('Precision', fontweight='bold')
    ax.legend(loc='lower left')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(RESULTS_DIR, save_filename)
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"[evaluate.py] Saved PR tradeoff plot to {plot_path}")

def evaluate(data_dir='data'):
    """Main evaluation pipeline."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    test_dir = os.path.join(data_dir, 'test')

    print(f"[evaluate.py] Loading test images from {test_dir}...")
    imgs_clean, imgs_night, y_true, fpaths = load_test_dataset(test_dir)

    if len(y_true) == 0:
        print("[ERROR] No test images found. Run build_dataset.py first.")
        return

    print(f"[evaluate.py] Loaded {len(y_true)} clean & night test samples.")

    # Load Night-Augmented Model
    model = None
    if os.path.exists(MODEL_PATH):
        print(f"[evaluate.py] Loading main model: {MODEL_PATH}")
        model = tf.keras.models.load_model(MODEL_PATH)
    else:
        print(f"[WARNING] Main model not found at {MODEL_PATH}. Skipping model load.")

    # Load Baseline Model (if trained)
    baseline_model = None
    if os.path.exists(BASELINE_MODEL_PATH):
        print(f"[evaluate.py] Loading baseline model: {BASELINE_MODEL_PATH}")
        baseline_model = tf.keras.models.load_model(BASELINE_MODEL_PATH)

    results_data = {
        'total_test_samples': len(y_true),
        'night_augmented_model': {},
        'baseline_model': {}
    }

    if model is not None:
        # Predict on clean
        clean_probs = model.predict(imgs_clean, batch_size=16)
        clean_metrics = compute_metrics(y_true, clean_probs)

        # Predict on night
        night_probs = model.predict(imgs_night, batch_size=16)
        night_metrics = compute_metrics(y_true, night_probs)

        night_drop = round(clean_metrics['overall_accuracy'] - night_metrics['overall_accuracy'], 4)

        results_data['night_augmented_model'] = {
            'clean_test': clean_metrics,
            'simulated_night_test': night_metrics,
            'night_accuracy_drop': night_drop
        }

        # Plot confusion matrices & PR curves
        plot_confusion_matrix(clean_metrics['confusion_matrix'], 'Confusion Matrix (Clean Test)', 'confusion_matrix_normal.png')
        plot_confusion_matrix(night_metrics['confusion_matrix'], 'Confusion Matrix (Simulated Night Test)', 'confusion_matrix_night.png')
        plot_pr_tradeoff(y_true, clean_probs)

        print("\n" + "=" * 60)
        print("GAJAALERT MODEL EVALUATION SUMMARY (Night-Augmented Model)")
        print("=" * 60)
        print(f"Clean Test Accuracy:            {clean_metrics['overall_accuracy']*100:.2f}%")
        print(f"Simulated Night Test Accuracy:  {night_metrics['overall_accuracy']*100:.2f}%")
        print(f"Night Accuracy Drop:            {night_drop*100:.2f}%")
        print(f"Elephant Precision (Clean):     {clean_metrics['elephant_precision']*100:.2f}%")
        print(f"Elephant Recall (Clean):        {clean_metrics['elephant_recall']*100:.2f}%")
        print("=" * 60)

    if baseline_model is not None:
        b_clean_probs = baseline_model.predict(imgs_clean, batch_size=16)
        b_clean_metrics = compute_metrics(y_true, b_clean_probs)

        b_night_probs = baseline_model.predict(imgs_night, batch_size=16)
        b_night_metrics = compute_metrics(y_true, b_night_probs)

        b_night_drop = round(b_clean_metrics['overall_accuracy'] - b_night_metrics['overall_accuracy'], 4)

        results_data['baseline_model'] = {
            'clean_test': b_clean_metrics,
            'simulated_night_test': b_night_metrics,
            'night_accuracy_drop': b_night_drop
        }

        print("\nBASELINE MODEL EVALUATION SUMMARY (No Night Aug)")
        print(f"Baseline Clean Accuracy:        {b_clean_metrics['overall_accuracy']*100:.2f}%")
        print(f"Baseline Simulated Night Acc:   {b_night_metrics['overall_accuracy']*100:.2f}%")
        print(f"Baseline Night Accuracy Drop:   {b_night_drop*100:.2f}%")

    # Save metrics JSON
    with open(METRICS_PATH, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"\n[evaluate.py] Full evaluation metrics saved to {METRICS_PATH}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate GajaAlert model")
    parser.add_argument('--data-dir', default='data', help='Data directory')
    args = parser.parse_args()

    evaluate(data_dir=args.data_dir)
