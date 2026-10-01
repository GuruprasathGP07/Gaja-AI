"""
train.py - Keras MobileNetV2 transfer learning pipeline with custom night augmentation.

Phase A: Train dense classifier head with frozen MobileNetV2 backbone (Adam 1e-3).
Phase B: Unfreeze last 30 layers with BatchNorm layers kept frozen (Adam 1e-5).
Key Innovation: Custom tf.data night augmentation applied to ~40% of training frames.
"""

import os
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks

from common import (
    CLASSES, MODEL_DIR, MODEL_PATH, BASELINE_MODEL_PATH,
    LABELS_PATH, META_PATH, RESULTS_DIR
)

# Set random seeds for reproducibility
tf.random.set_seed(42)
np.random.seed(42)

IMG_SIZE = (224, 224)
BATCH_SIZE = 16

def apply_night_augmentation(image, label):
    """
    Apply camera-trap night simulation to ~40% of training images:
    - Darkening: multiply brightness by uniform random in [0.15, 0.60]
    - Tinting: RGB scaling factors (0.85, 0.95, 1.10)
    - Gaussian noise: sigma = 8.0
    - Clip to [0.0, 255.0]
    """
    # Randomly decide whether to apply night augmentation (40% probability)
    do_night = tf.random.uniform([]) < 0.40

    def night_fn():
        # Ensure image is float
        img = tf.cast(image, tf.float32)

        # 1. Darkening factor U(0.15, 0.60)
        darkness = tf.random.uniform([], minval=0.15, maxval=0.60)
        img = img * darkness

        # 2. Blue-grey tinting (R:0.85, G:0.95, B:1.10)
        tint = tf.constant([0.85, 0.95, 1.10], dtype=tf.float32)
        img = img * tint

        # 3. Gaussian noise (sigma = 8.0)
        noise = tf.random.normal(shape=tf.shape(img), mean=0.0, stddev=8.0)
        img = img + noise

        # 4. Clip to valid pixel range
        img = tf.clip_by_value(img, 0.0, 255.0)
        return img

    aug_image = tf.cond(do_night, night_fn, lambda: tf.cast(image, tf.float32))
    return aug_image, label

def build_model():
    """
    Build Keras functional model:
    Augmentation -> Rescaling -> MobileNetV2 -> GlobalAvgPool -> Dense(128) -> Dropout(0.3) -> Dense(3)
    """
    inputs = layers.Input(shape=(224, 224, 3))

    # Data augmentation pipeline (flips, slight rotation, slight zoom)
    x = layers.RandomFlip("horizontal")(inputs)
    x = layers.RandomRotation(0.08)(x)
    x = layers.RandomZoom(0.15)(x)

    # Rescaling input to MobileNetV2 range [-1, 1]
    x = layers.Rescaling(1.0 / 127.5, offset=-1.0)(x)

    # Base MobileNetV2 backbone
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False  # Initially frozen for Phase A

    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(128, activation='relu', name='dense_head')(x)
    x = layers.Dropout(0.3, name='dropout_head')(x)
    outputs = layers.Dense(3, activation='softmax', name='classifier')(x)

    model = models.Model(inputs, outputs, name='gajaalert_mobilenetv2')
    return model, base_model

def load_datasets(data_dir, use_night_aug=True):
    """Load train, val, and test datasets using image_dataset_from_directory."""
    train_dir = os.path.join(data_dir, 'train')
    val_dir = os.path.join(data_dir, 'val')
    test_dir = os.path.join(data_dir, 'test')

    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        labels='inferred',
        label_mode='categorical',
        class_names=CLASSES,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=True,
        seed=42
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        val_dir,
        labels='inferred',
        label_mode='categorical',
        class_names=CLASSES,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    if use_night_aug:
        print("[train.py] Applying Custom Night Augmentation to training pipeline (~40% of frames)...")
        train_ds = train_ds.map(apply_night_augmentation, num_parallel_calls=tf.data.AUTOTUNE)

    train_ds = train_ds.prefetch(buffer_size=tf.data.AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=tf.data.AUTOTUNE)

    return train_ds, val_ds

def train(data_dir='data', epochs_phase_a=5, epochs_phase_b=8, use_night_aug=True):
    """Execute two-phase transfer learning training."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print(f"[train.py] Starting training with data from {data_dir} (Night Augmentation: {use_night_aug})")
    train_ds, val_ds = load_datasets(data_dir, use_night_aug=use_night_aug)

    model, base_model = build_model()
    model.summary()

    # Calculate class weights to address potential class imbalance
    class_weights = {0: 1.0, 1: 1.0, 2: 1.0}

    cb_list = [
        callbacks.EarlyStopping(monitor='val_loss', patience=4, restore_best_weights=True),
        callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, verbose=1)
    ]

    # --- Phase A: Train Classifier Head Only ---
    print("\n--- PHASE A: Training Classifier Head (Backbone Frozen) ---")
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-3),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    history_a = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs_phase_a,
        class_weight=class_weights,
        callbacks=cb_list
    )

    # --- Phase B: Fine-Tune Backbone ---
    print("\n--- PHASE B: Fine-Tuning Last 30 Backbone Layers (BatchNorm Frozen) ---")
    base_model.trainable = True
    # Freeze all layers except last 30
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    # CRITICAL: Keep BatchNormalization layers frozen in inference mode
    for layer in base_model.layers:
        if isinstance(layer, layers.BatchNormalization):
            layer.trainable = False

    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-5),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    history_b = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs_phase_b,
        class_weight=class_weights,
        callbacks=cb_list
    )

    # Save Model & Labels
    save_path = MODEL_PATH if use_night_aug else BASELINE_MODEL_PATH
    model.save(save_path)
    print(f"\n[train.py] Model successfully saved to {save_path}")

    # Save labels.json
    labels_dict = {i: cls for i, cls in enumerate(CLASSES)}
    with open(LABELS_PATH, 'w') as f:
        json.dump(labels_dict, f, indent=2)

    # Save metadata
    meta = {
        'model_name': 'GajaAlert MobileNetV2 Transfer Learning',
        'use_night_aug': use_night_aug,
        'classes': CLASSES,
        'input_shape': list(IMG_SIZE) + [3],
        'phase_a_epochs': len(history_a.history['loss']),
        'phase_b_epochs': len(history_b.history['loss']),
        'final_val_acc': float(history_b.history['val_accuracy'][-1]),
        'final_val_loss': float(history_b.history['val_loss'][-1])
    }
    meta_file = META_PATH if use_night_aug else os.path.join(MODEL_DIR, 'baseline_model.meta.json')
    with open(meta_file, 'w') as f:
        json.dump(meta, f, indent=2)

    # Plot & Save Training Curves
    plot_training_curves(history_a, history_b, use_night_aug=use_night_aug)

def plot_training_curves(history_a, history_b, use_night_aug=True):
    """Plot and save training/validation accuracy and loss curves across Phase A and B."""
    acc = history_a.history['accuracy'] + history_b.history['accuracy']
    val_acc = history_a.history['val_accuracy'] + history_b.history['val_accuracy']
    loss = history_a.history['loss'] + history_b.history['loss']
    val_loss = history_a.history['val_loss'] + history_b.history['val_loss']

    epochs_range = range(1, len(acc) + 1)
    phase_a_cutoff = len(history_a.history['accuracy'])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Accuracy Plot
    ax1.plot(epochs_range, acc, label='Train Accuracy', color='#2563eb', linewidth=2)
    ax1.plot(epochs_range, val_acc, label='Val Accuracy', color='#059669', linewidth=2)
    ax1.axvline(x=phase_a_cutoff + 0.5, color='#94a3b8', linestyle='--', label='Phase B Start')
    ax1.set_title('Model Accuracy Curves')
    ax1.set_xlabel('Epochs')
    ax1.set_ylabel('Accuracy')
    ax1.legend(loc='lower right')
    ax1.grid(True, alpha=0.3)

    # Loss Plot
    ax2.plot(epochs_range, loss, label='Train Loss', color='#dc2626', linewidth=2)
    ax2.plot(epochs_range, val_loss, label='Val Loss', color='#d97706', linewidth=2)
    ax2.axvline(x=phase_a_cutoff + 0.5, color='#94a3b8', linestyle='--', label='Phase B Start')
    ax2.set_title('Model Loss Curves')
    ax2.set_xlabel('Epochs')
    ax2.set_ylabel('Loss')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(RESULTS_DIR, 'training_curves.png' if use_night_aug else 'training_curves_baseline.png')
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"[train.py] Saved training curves to {plot_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train GajaAlert MobileNetV2 Model")
    parser.add_argument('--data-dir', default='data', help='Dataset root directory')
    parser.add_argument('--no-night-aug', action='store_true', help='Train baseline without night augmentation')
    parser.add_argument('--epochs-a', type=int, default=5, help='Phase A epochs')
    parser.add_argument('--epochs-b', type=int, default=8, help='Phase B epochs')
    args = parser.parse_args()

    train(
        data_dir=args.data_dir,
        epochs_phase_a=args.epochs_a,
        epochs_phase_b=args.epochs_b,
        use_night_aug=not args.no_night_aug
    )
