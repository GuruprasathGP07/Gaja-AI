# GajaAlert AI - Dataset Documentation & Sources

## Open-Source Dataset Provenance & Licenses

All images used for training, validation, and testing GajaAlert AI originate from open datasets under permissive Creative Commons licenses. No unlicensed or scraped web imagery is included.

| Category | Source Dataset / Repository | License | Attribution Requirement |
| :--- | :--- | :--- | :--- |
| **Asian Elephants (*Elephas maximus*)** | iNaturalist Open Data (CC-BY / CC0) | CC-BY 4.0 / CC0 1.0 | iNaturalist contributors & GBIF Secretariat |
| **African & Asian Elephants** | LILA BC Camera Trap Datasets (Snapshot Serengeti / Wildlife Insights) | CC-BY 4.0 | LILA BC / Wildlife Insights Consortium |
| **Other Wildlife & Hard Negatives** | Open Images V7 (Cattle, Deer, Boar, Gaur, Goats) | CC-BY 2.0 / CC-BY 4.0 | Open Images Dataset Authors |
| **No Animal / Background Scenes** | Wikimedia Commons & LILA BC (Forest, Farm, Road, Night Terrain) | CC0 / Public Domain | Wikimedia Commons contributors |

---

## Dataset Splits & Class Balance

- **Target Classes**: `elephant`, `other_animal`, `no_animal`
- **Split Ratios**: 70% Train / 15% Validation / 15% Test
- **Deduplication**: SHA-256 pixel hashing eliminates duplicate frames.
- **Leakage Prevention**: Group-aware sequence partitioning ensures frames from the same camera trap burst or observation remain strictly within a single split.

---

## Synthetic Smoke Benchmark

To enable offline verification and reproducible test runs, `tools/make_smoke_data.py` generates a synthetic benchmark set across day, dusk, and simulated night camera trap conditions. Synthetic data metrics are reported separately from field data evaluations.
