# 🌿 CannaGrade — Cannabis Quality Analyzer

AI-powered web app that analyzes a photo of cannabis buds or seeds and returns a full quality report, including strain identification, disease detection, terpene profile, and cannabinoid breakdown.

---

## Features

### 🌸 Bud Analysis
- **Quality Scoring** — Grades the sample (AAA → C) across 5 evidence-based criteria
- **Strain Identification** — Detects Indica / Sativa / Hybrid from visual cues and matches against 9,483 strains
- **Disease & Pest Detection** — Identifies 36 conditions (fungal, nutrient, environmental, pest, genetic)
- **Terpene Profile** — Identifies likely terpenes with chemical formulas and scientific descriptions
- **Cannabinoid Profile** — Estimates dominant cannabinoids (THC, CBG, CBN, etc.) with chemical data

### 🌱 Seed Analysis
- **Seed Quality Scoring** — Grades seed viability (AAA → C) across 5 criteria
- **Germination Potential** — Estimates likelihood of successful germination (High / Medium / Low)
- **Health Issue Detection** — Identifies 8 seed conditions (mold, cracked shell, pest damage, immaturity, rot, degradation, contamination, abnormal shape)
- **Batch Uniformity** — Evaluates consistency across multiple seeds in the image
- **Visual Reference Matching** — Compares against 17 known healthy strain profiles from the Mendeley dataset

### General
- **Auto-detection** — Automatically identifies whether the image is a bud or seed
- **Drag & Drop UI** — Upload any JPG, PNG, or WEBP image

## Bud Quality Criteria

| Criterion | What's evaluated |
|---|---|
| 🎨 Color & Pistils | Vivid green/purple/orange hues, prominent orange pistils |
| ✨ Trichome Coverage | Shiny crystal resin glands coating the surface |
| 🌸 Bud Structure | Density, compactness, and formation |
| 💧 Moisture & Freshness | Proper cure — not bone dry or too wet |
| 👁️ Appearance | Trim quality, absence of seeds/stems, no mold or pest damage |

## Seed Quality Criteria

| Criterion | What's evaluated |
|---|---|
| 🎨 Color & Markings | Brown/tan mottled shell with defined striations |
| ⚖️ Size & Fullness | Plump, well-developed body indicating stored nutrients |
| 🛡️ Shell Integrity | No cracks, splits, or physical damage |
| 🔬 Surface Cleanliness | Free from mold, residue, or contamination |
| 🕐 Maturity | Fully hardened shell, not pale or underdeveloped |

## Datasets

| Dataset | Source | Used for |
|---|---|---|
| Kushy Strains | [kushyapp/cannabis-dataset](https://github.com/kushyapp/cannabis-dataset) | 9,483 strains with effects, flavors, THC/CBD |
| Cannabis Analytes | [cannlytics/cannabis_analytes](https://huggingface.co/datasets/cannlytics/cannabis_analytes) | 37 terpenes & cannabinoids with chemical data |
| Cannabis Seeds | [Mendeley dscww8w8zt](https://data.mendeley.com/datasets/dscww8w8zt/2) | 17 healthy seed visual profiles across strains |

## Stack

- **Backend:** Python / Flask
- **AI:** Claude Sonnet (`claude-sonnet-4-6`) for analysis, Claude Haiku for image type detection
- **Frontend:** Vanilla HTML, CSS, JavaScript

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/ttuuccoozzii/cannabis-quality-analyzer.git
cd cannabis-quality-analyzer
```

### 2. Create a virtual environment and install dependencies

```bash
# Using uv (recommended)
uv venv .venv
uv pip install -r requirements.txt

# Or using pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Add your Anthropic API key

```bash
cp .env.example .env
# Edit .env and paste your key from console.anthropic.com
```

### 4. Download the strains dataset

```bash
mkdir -p data
curl -L "https://raw.githubusercontent.com/kushyapp/cannabis-dataset/master/Dataset/Strains/strains-kushy_api.2017-11-14.csv" \
     -o data/strains.csv
```

### 5. Run

```bash
source .venv/bin/activate
python3 app.py
```

Open **http://127.0.0.1:5000** in your browser.

## Project Structure

```
cannabis-quality-analyzer/
├── app.py                  # Flask app + Claude API integration
├── strains.py              # Kushy dataset loader and search
├── analytes.py             # Cannlytics analyte lookup
├── diseases.py             # Bud disease/condition database
├── seed_diseases.py        # Seed health issue database
├── seed_strains.py         # Mendeley seed visual reference loader
├── data/
│   ├── strains.csv         # 9,483 cannabis strains
│   ├── analytes.json       # 37 terpenes and cannabinoids
│   ├── diseases.json       # 36 bud conditions
│   ├── seed_diseases.json  # 8 seed health conditions
│   └── seed_strains.json   # 17 healthy seed strain profiles
├── templates/
│   └── index.html          # Single-page UI
├── static/
│   ├── css/style.css
│   └── js/app.js
├── requirements.txt
└── .env.example
```

## License

For legal use only. Results are AI-generated estimates and should not be used for medical or legal purposes.
