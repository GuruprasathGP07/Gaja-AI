# GajaAlert AI - Comprehensive Project Explainer & Viva Q&A

## Part 1: File-by-File Plain Language Guide

- **`app.py`**: The Flask REST API web server. Receives image frame uploads, decodes images securely with Pillow, caps payloads at 8 MB, invokes model predictions, computes Grad-CAM heatmaps, applies deterministic risk rules, logs events to SQLite, and serves the web frontend.
- **`alerts.py`**: The risk rule engine and bilingual alert generator. Translates top predicted classes, confidence scores, time of day (18:00 - 06:00), and 30-minute repeat sightings into risk levels (`NONE`, `LOW`, `MEDIUM`, `HIGH`) and formats English & Tamil warning text.
- **`db.py`**: SQLite database interface (`gajaalert.db`). Manages detection logs, queries 30-minute repeat sighting windows, computes 24-hour histogram stats, and supports reset functions.
- **`common.py`**: Shared system constants, 5 Coimbatore virtual camera site definitions with geographic coordinates, class name dictionaries, and file path configurations.
- **`train.py`**: Model training script. Implements MobileNetV2 transfer learning in two phases (Phase A frozen backbone, Phase B fine-tuning last 30 layers with BatchNorm kept frozen) and custom `tf.data` night augmentation.
- **`evaluate.py`**: Empirical evaluator. Evaluates baseline and night-augmented models on clean and simulated night test splits, outputs confusion matrices, PR curves, and `results/metrics.json`.
- **`gradcam.py`**: Visual explainability module. Computes gradient-weighted class activation heatmaps targeting MobileNetV2's final conv layer (`out_relu`) and encodes overlays to Base64 PNG.
- **`tools/make_smoke_data.py`**: Synthetic dataset generator for pipeline verification across day, dusk, and night conditions.
- **`tools/build_dataset.py`**: Dataset splitter. Groups images to prevent data leakage and eliminates duplicate images using SHA-256 hashing.
- **`tools/audit_dataset.py`**: Data integrity auditor. Checks resolution, corrupt files, class balance, and verifies zero cross-split duplicates.
- **`templates/`**:
  - `base.html`: Main HTML5 semantic template with local vendored imports and navigation.
  - `index.html`: Operational dashboard featuring the verdict band, control panel, probability bars, alert cards, Leaflet map, Chart.js graph, and event table.
  - `evidence.html`: Academic metrics & model comparison evidence portal.
- **`static/`**:
  - `style.css`: Custom responsive dark-theme stylesheet.
  - `app.js`: Vanilla JS logic handling file uploads, API requests, verdict updates, Web Audio sirens, Web Speech TTS, Leaflet maps, and Chart.js integration.
  - `vendor/`: Vendored offline Leaflet, Chart.js, and font assets.
- **`submission/`**:
  - `excel_row.txt`: Registration summary text.
  - `711524BCS049_GURU PRASATH C.pptx`: 3-slide hackathon presentation.
  - `demo_script.md`: 2-minute live demo script and backup image guide.

---

## Part 2: Top 25 Faculty Evaluation Questions & Answers

### 1. What problem does GajaAlert AI solve?
It provides low-cost automated early warning detection for wild elephant intrusions near human settlements in Tamil Nadu, bridging the delay between camera detection and warning broadcast.

### 2. Why prioritize Asian elephants over African elephants?
Asian elephants (*Elephas maximus*) are native to the Western Ghats and Coimbatore forest fringes. Their smaller ears and distinct forehead shapes differ from African elephants, making localized evaluation essential.

### 3. What is the source of your animal attack mortality statistics?
Tamil Nadu Forest Department statistics record 685 human deaths from wild animal attacks between 2015 and July 2025, with 522 (76.2%) caused by elephants.

### 4. How does your system differ from existing solutions like Valparai SMS?
Valparai SMS relies on human informants and manual mapping. GajaAlert AI automates camera trap detection via CNNs, producing real-time risk levels and bilingual alerts instantly.

### 5. Are your camera feeds and SMS delivery real or simulated?
Camera feeds, SMS broadcasts, and sirens are simulated in the software interface for demonstration safety, as stated in the UI and documentation.

### 6. What neural network architecture is used?
MobileNetV2 pre-trained on ImageNet, fine-tuned with a custom Dense classifier head (128 units, ReLU, 0.3 Dropout, 3-class Softmax).

### 7. Why choose MobileNetV2 over ResNet or Vision Transformers?
MobileNetV2 uses depthwise separable convolutions, offering high accuracy with low memory footprint (~14MB), making it ideal for low-cost edge nodes.

### 8. How do you address night-time detection in camera traps?
We apply a custom `tf.data` night augmentation during training (~40% probability): brightness scaling $U(0.15, 0.60)$, blue-grey IR tinting, and Gaussian noise ($\sigma=8$).

### 9. Why train both a baseline and night-augmented model?
To empirically benchmark and prove the accuracy gain of custom night augmentation under low-light conditions.

### 10. What is data leakage and how do you prevent it?
Data leakage occurs when identical or sequential frames appear in both train and test splits. `build_dataset.py` groups burst frames by observation ID and removes pixel-hash duplicates via SHA-256.

### 11. What is the purpose of `audit_dataset.py`?
It validates dataset integrity, checks resolution bounds, reports class balance, and fails loudly if cross-split duplicate hashes exist.

### 12. How is Grad-CAM implemented?
`gradcam.py` computes gradients of the target class score w.r.t. MobileNetV2's last conv layer (`out_relu`), producing spatial heatmaps that explain model focus.

### 13. Is the risk assessment logic neural-network-based or rule-based?
It is deterministic rule-based domain logic (`alerts.py`), ensuring predictable safety rules distinct from the probabilistic CNN output.

### 14. What are the base risk thresholds for elephant detection?
Top class `elephant` with confidence $\ge 0.85$ sets base risk `MEDIUM`; confidence $< 0.85$ sets base risk `LOW`. Non-elephant returns `NONE`.

### 15. What context factors elevate the risk level?
Night time (18:00 - 06:00) elevates risk by $+1$ level; a repeat sighting at the same site within 30 minutes elevates risk by $+1$ level (capped at `HIGH`).

### 16. When is `review_needed` set to True?
When an elephant is detected with confidence $< 0.60$, flagging low-certainty frames for human supervisor verification.

### 17. How are bilingual alerts generated?
`alerts.py` formats site-specific English and natural Tamil warning messages dynamically populated with time and confidence metrics.

### 18. Why is elephant recall more critical than precision?
A false alarm (low precision) causes minor inconvenience, whereas a missed intrusion (low recall) poses a threat to human life.

### 19. How does the frontend function offline?
All core JavaScript libraries (Leaflet, Chart.js), CSS stylesheets, and font definitions are vendored locally in `static/vendor/`.

### 20. How is the audio warning siren produced without external MP3 files?
Using the Web Audio API to synthesize wailing sawtooth oscillator sound waves directly in the browser.

### 21. How does the Web Speech API work in GajaAlert AI?
It uses browser native `SpeechSynthesisUtterance` to vocalize English (`en-US`) and Tamil (`ta-IN`) warning text when "Read Aloud" is clicked.

### 22. What database is used for event logging?
SQLite (`db.py`), storing timestamps, site IDs, confidence scores, risk levels, and JSON probability distributions.

### 23. What security measures are enforced on file uploads?
Pillow decodes and verifies image headers, file sizes are capped at 8 MB, files are saved under UUID filenames, and debug mode is OFF by default.

### 24. What does the `GAJA_MOCK=1` flag do?
It enables stub classification for frontend testing without requiring loaded TensorFlow weights, displaying a visible banner on screen.

### 25. What are the key limitations of the current system?
Simulated camera feeds, synthetic night degradation approximation, reliance on public dataset compositions, and edge hardware deployment requirements.

### 26. How does GajaAlert AI align with real-world deployments like the IFS AI camera system reported in July 2026?
The July 2026 deployment reported by IFS Officer Parveen Kaswan (where an AI camera detected an elephant herd at 12:32 AM and dispatched a Rapid Response Team within 15 minutes) provides **direct real-world proof of concept and market validation** for our problem statement. 

GajaAlert AI complements existing government tower infrastructure by providing a **low-cost, edge-optimized software pipeline (MobileNetV2, 14MB footprint)** suitable for localized farm/village boundaries, coupled with **Grad-CAM visual explainability** (so rangers/officers can visually verify detections to prevent false-alarm fatigue) and **instant bilingual (English/Tamil) voice & audio sirens** at the edge.

