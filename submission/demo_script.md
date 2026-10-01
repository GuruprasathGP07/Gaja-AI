# GajaAlert AI - 2-Minute Hackathon Demo Script & Backup Plan

## Live Pitch & Presentation Script (2 Minutes)

### [0:00 - 0:30] Problem & Context (Slide 1)
> "Good morning evaluators. Between 2015 and July 2025, Tamil Nadu recorded 685 human deaths from wild animal attacks, and 522 of them—over 76%—were caused by wild elephants near forest fringes like Coimbatore. Existing solutions like manual SMS alert networks or costly camera towers rely heavily on delayed human reports. GajaAlert AI automates camera trap detection at low cost to broadcast immediate bilingual early warnings."

### [0:30 - 1:15] Technical Architecture & Live Demo (Slide 2 & Dashboard)
> "Here is our live system. On the left control panel, a camera trap frame is uploaded. When I click 'Analyze Image Frame', our Flask backend decodes the payload, passes it through a MobileNetV2 CNN transfer learning pipeline, and evaluates our deterministic safety rules.
>
> Look at the **Verdict Band**: it dynamically shifts color to RED for HIGH risk. The model detected an Asian Elephant with high confidence. Notice our key innovation: custom `tf.data` night augmentation makes the CNN robust under low-light camera trap conditions.
>
> We can toggle **Grad-CAM** heatmaps to visually verify that the neural network focuses on the elephant's trunk and body contour rather than background clutter. Below, bilingual warning alerts in English and natural Tamil are generated instantly with Web Speech TTS ('Read Aloud') and Leaflet geographic sensor mapping."

### [1:15 - 2:00] Quantitative Results & Evidence (Slide 3 & Evidence Page)
> "On our Model Evidence page, we compare our Night-Augmented model against a baseline trained without low-light augmentation. Under simulated night degradation ($\times 0.30$ brightness and noise), our custom augmentation preserves high classification accuracy with minimal performance drop, maintaining high elephant recall to eliminate dangerous false negatives.
>
> All camera feeds and sirens are simulated safely in code. Thank you!"

---

## Backup Test Image Guide (Keep Ready on Desktop)

1. **`elephant_day_001.jpg`**: Clear daytime Asian elephant frame near Maruthamalai foothills $\rightarrow$ Expected Verdict: `MEDIUM` (or `HIGH` if repeat).
2. **`elephant_night_002.jpg`**: Dark simulated night elephant frame near Madukkarai $\rightarrow$ Expected Verdict: `HIGH` (Night elevation $+1$).
3. **`gaur_other_003.jpg`**: Gaur / cattle hard negative frame $\rightarrow$ Expected Verdict: `NONE`.
4. **`forest_no_animal_004.jpg`**: Dense forest background with rocks $\rightarrow$ Expected Verdict: `NONE`.
