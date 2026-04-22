# 🌿 CannaGrade — Cannabis Quality Analyzer

AI-powered web app that analyzes a photo of cannabis and returns a full quality report, strain identification, terpene profile, and cannabinoid breakdown.

---

## Features

- **Quality Scoring** — Grades the sample (AAA → C) across 5 evidence-based criteria
- **Strain Identification** — Detects Indica / Sativa / Hybrid from visual cues and matches against 9,483 strains
- **Terpene Profile** — Identifies likely terpenes with chemical formulas and scientific descriptions
- **Cannabinoid Profile** — Estimates dominant cannabinoids (THC, CBG, CBN, etc.) with chemical data
- **Drag & Drop UI** — Upload any JPG, PNG, or WEBP image

## Quality Criteria

Based on indicators from cannabis quality guides:

| Criterion | What's evaluated |
|---|---|
| 🎨 Color & Pistils | Vivid green/purple/orange hues, prominent orange pistils |
| ✨ Trichome Coverage | Shiny crystal resin glands coating the surface |
| 🌸 Bud Structure | Density, compactness, and formation |
| 💧 Moisture & Freshness | Proper cure — not bone dry (lost oils) or too wet (mold risk) |
| 👁️ Appearance | Trim quality, absence of seeds/stems, no mold or pest damage |

## Datasets

| Dataset | Source | Used for |
|---|---|---|
| Kushy Strains | [kushyapp/cannabis-dataset](https://github.com/kushyapp/cannabis-dataset) | 9,483 strains with effects, flavors, THC/CBD |
| Cannabis Analytes | [cannlytics/cannabis_analytes](https://huggingface.co/datasets/cannlytics/cannabis_analytes) | 37 terpenes & cannabinoids with chemical data |

## Stack

- **Backend:** Python / Flask
- **AI:** Claude Sonnet (`claude-sonnet-4-6`) via Anthropic API
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
├── app.py              # Flask app + Claude API integration
├── strains.py          # Kushy dataset loader and search
├── analytes.py         # Cannlytics analyte lookup
├── data/
│   ├── strains.csv     # 9,483 cannabis strains
│   └── analytes.json   # 37 terpenes and cannabinoids
├── templates/
│   └── index.html      # Single-page UI
├── static/
│   ├── css/style.css
│   └── js/app.js
├── requirements.txt
└── .env.example
```

## License

For legal use only. Results are AI-generated estimates and should not be used for medical or legal purposes.
