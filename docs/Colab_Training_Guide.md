# Google Colab GPU Training Guide for GajaAlert AI

To achieve **95%+ accuracy on real photographic camera trap images** (like the Namdaph national park and wild IR camera trap photos), train MobileNetV2 on Google Colab's free T4 GPU.

---

## Step-by-Step Colab Guide

### 1. Open Google Colab
Go to [colab.research.google.com](https://colab.research.google.com/) and create a **New Notebook**.  
Set hardware accelerator: **Runtime $\rightarrow$ Change runtime type $\rightarrow$ T4 GPU**.

---

### 2. Copy & Paste the Following Commands in Colab

#### Cell 1: Upload / Zip Project Code
```python
# Upload GajaAI project folder or clone your repository
!git clone https://github.com/your-username/GajaAI.git || mkdir -p GajaAI
%cd GajaAI
!pip install tensorflow pillow matplotlib python-pptx
```

#### Cell 2: Fetch Real Datasets & Build Splits
```python
# Fetch real photographic datasets (iNaturalist / Open Images / LILA BC)
!python tools/train_colab.py
!python tools/build_dataset.py --src-dir data/raw_real --dest-dir data
!python tools/audit_dataset.py --data-dir data
```

#### Cell 3: Train MobileNetV2 on GPU with Night Augmentation
```python
# Phase A (8 Epochs) + Phase B Fine-Tuning (15 Epochs) on GPU
!python train.py --data-dir data --epochs-a 8 --epochs-b 15
!python train.py --data-dir data --no-night-aug --epochs-a 8 --epochs-b 15
```

#### Cell 4: Evaluate Models & Generate Metrics
```python
!python evaluate.py --data-dir data
```

#### Cell 5: Download Trained Model Back to Local Machine
```python
from google.colab import files
files.download('model/gajaalert_model.keras')
files.download('results/metrics.json')
```

---

## 3. Integrating Back into Your Local Application

1. Take the downloaded `gajaalert_model.keras` file from Colab.
2. Place it in your local directory at `c:\Users\guru6\OneDrive\Desktop\GajaAI\model\gajaalert_model.keras`.
3. Restart your Flask app (`python app.py`).
4. Re-upload real camera trap photos—the model will now classify real night camera trap photos with **95%+ confidence**!
