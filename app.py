import base64
import io
import os
import json
from flask import Flask, request, jsonify, render_template
from anthropic import Anthropic
from PIL import Image
from dotenv import load_dotenv
import strains as strain_db
import analytes as analyte_db
import diseases as disease_db

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Build reference lists for the prompt
_TERPENE_NAMES     = ", ".join(r["name"] for r in analyte_db.get_terpenes())
_CANNABINOID_NAMES = ", ".join(r["name"] for r in analyte_db.get_cannabinoids())
_DISEASE_NAMES     = ", ".join(disease_db.get_names())

ANALYSIS_PROMPT = f"""You are an expert cannabis quality analyst. Use the following evidence-based criteria (sourced from professional cannabis quality guides) to score this image.

── QUALITY SCORING ──
Score each criterion from 0–10 using these specific indicators:

1. COLOR & PISTILS (color)
   Good (8-10): Vivid, bright hues — greens, purples, or oranges. Prominent orange/red pistils standing out clearly.
   Average (5-7): Muted greens, fewer visible pistils, slight fading.
   Poor (0-4): Brown or dark buds (sign of age or bad curing), dull/flat coloring, absent pistils.

2. TRICHOME COVERAGE (trichomes)
   Good (8-10): Dense shiny trichomes visibly coating the flower surface — indicates high cannabinoid content and potency.
   Average (5-7): Some trichome coverage visible but sparse or uneven.
   Poor (0-4): Damaged, absent, or no visible trichomes — major quality downgrade.

3. BUD STRUCTURE & DENSITY (structure)
   Good (8-10): Dense, compact, well-formed buds with tight structure.
   Average (5-7): Moderately dense, some looseness.
   Poor (0-4): Airy, loose, or poorly formed buds.

4. MOISTURE & FRESHNESS (moisture)
   Good (8-10): Buds look properly cured — not bone dry and crumbly, not dark and wet. Should appear to have retained oils.
   Average (5-7): Slightly overdry or slightly moist.
   Poor (0-4): Visibly bone dry (old, lost oils and potency), or overly wet/dark (mold risk, poor cure). Very old cannabis looks brown and degraded.

5. OVERALL APPEARANCE & CONTAMINATION (appearance)
   Good (8-10): Clean trim, no visible seeds or stems, no signs of mold (white powdery patches, dark spots), no pest damage, uniform appealing look.
   Average (5-7): Minor trim issues, a stem or two visible.
   Poor (0-4): Visible seeds, excessive stems, signs of mold/mildew, pest damage, or heavily contaminated-looking material.

── STRAIN IDENTIFICATION ──
Based on visual characteristics (bud shape, leaf structure, color palette, density, pistil color):
- Estimate cannabis type: "Indica", "Sativa", or "Hybrid"
- List up to 5 likely effects (from: Relaxed, Happy, Euphoric, Uplifted, Creative, Energetic, Focused, Sleepy, Tingly, Hungry, Talkative)
- List up to 4 likely flavor/aroma profiles (from: Earthy, Sweet, Citrus, Pine, Woody, Diesel, Spicy, Berry, Floral, Tropical, Mint, Coffee, Skunk, Cheese, Grape, Blueberry, Mango, Vanilla, Pineapple, Lavender)

── ANALYTE PROFILE ──
Based on the visual characteristics and likely strain type, estimate:
- Up to 4 likely terpenes present (choose from: {_TERPENE_NAMES})
- Up to 3 likely dominant cannabinoids (choose from: {_CANNABINOID_NAMES})
- Estimated THC range as a string e.g. "18-22%", or null if uncertain
- Estimated CBD range as a string e.g. "0.1-0.5%", or null if uncertain

── DISEASE & HEALTH DETECTION ──
Carefully inspect the image for any signs of plant disease, pest infestation, nutrient deficiency, or environmental stress.
Look specifically for:
- Fungal signs: white powdery coating, gray fuzzy mold, dark spots, slimy or mushy areas
- Pest signs: webbing, stippling (tiny dots), unusual speckles, sticky residue
- Nutrient issues: yellowing, purple/red discoloration, brown edges, interveinal chlorosis
- Environmental stress: burned tips, bleached patches, twisted or clawing leaves, wilting

From the following known conditions, list only the ones you can visually confirm or strongly suspect:
{_DISEASE_NAMES}

For each detected condition provide: name, confidence (0.0–1.0), and the specific visual evidence you observed.
If the sample looks completely healthy, return an empty array.

Return ONLY a raw JSON object (no markdown fences):
{{
  "overall_score": <0-100 integer>,
  "grade": "<AAA | AA | A | B | C>",
  "criteria": {{
    "color":      {{ "score": <0-10>, "note": "<specific observation about color and pistils>" }},
    "trichomes":  {{ "score": <0-10>, "note": "<specific observation about trichome coverage and shine>" }},
    "structure":  {{ "score": <0-10>, "note": "<specific observation about bud density and form>" }},
    "moisture":   {{ "score": <0-10>, "note": "<specific observation about moisture, curing, oil retention>" }},
    "appearance": {{ "score": <0-10>, "note": "<specific observation about trim, seeds, mold, contamination>" }}
  }},
  "summary": "<2-3 sentence overall assessment using the quality indicators above>",
  "positives": ["<specific quality point>", "<specific quality point>"],
  "negatives": ["<specific quality concern>", "<specific quality concern>"],
  "strain_type": "<Indica | Sativa | Hybrid | Unknown>",
  "likely_effects": ["<effect>", ...],
  "likely_flavors": ["<flavor>", ...],
  "likely_terpenes": ["<terpene name>", ...],
  "likely_cannabinoids": ["<cannabinoid name>", ...],
  "thc_estimate": "<range string or null>",
  "cbd_estimate": "<range string or null>",
  "detected_diseases": [
    {{ "name": "<exact name from list above>", "confidence": <0.0-1.0>, "evidence": "<what you saw>" }}
  ],
  "is_cannabis": <true | false>
}}

If the image does NOT contain cannabis, set is_cannabis to false and all scores to 0.
"""


def compress_image(image_bytes: bytes, max_size: int = 1024) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def enrich_with_strains(result: dict) -> dict:
    strain_type    = result.get("strain_type")
    likely_effects = result.get("likely_effects", [])
    likely_flavors = result.get("likely_flavors", [])

    if strain_type == "Unknown":
        strain_type = None

    matches = strain_db.search(
        strain_type=strain_type,
        effects=likely_effects,
        flavors=likely_flavors,
        top_n=5,
    )

    result["matched_strains"] = [
        {
            "name":        m["name"],
            "type":        m["type"],
            "effects":     m["effects"][:5],
            "flavors":     m["flavors"][:4],
            "thc":         m["thc"],
            "cbd":         m["cbd"],
            "terpenes":    m["terpenes"][:4],
            "description": m["description"][:220] + ("…" if len(m["description"]) > 220 else ""),
        }
        for m in matches
    ]
    result["dataset_size"] = strain_db.total_strains()
    return result


def enrich_with_diseases(result: dict) -> dict:
    """Look up full disease records for anything Claude detected."""
    detected = result.get("detected_diseases", [])
    enriched = []
    for item in detected:
        rec = disease_db.lookup_by_name(item.get("name", ""))
        if rec:
            enriched.append({
                **disease_db.format_disease(rec),
                "confidence": item.get("confidence", 0),
                "evidence":   item.get("evidence", ""),
            })
        else:
            # Pass through unknown detections Claude found that aren't in our DB
            enriched.append({
                "id":               "unknown",
                "name":             item.get("name", "Unknown"),
                "category":         "unknown",
                "severity":         "medium",
                "causes":           "",
                "treatment":        "Consult a cannabis cultivation specialist.",
                "risk_to_consumer": "Unknown — exercise caution.",
                "visual_symptoms":  [],
                "confidence":       item.get("confidence", 0),
                "evidence":         item.get("evidence", ""),
            })

    # Sort by severity then confidence
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}
    enriched.sort(key=lambda x: (severity_order.get(x["severity"], 9), -x["confidence"]))

    result["detected_diseases"] = enriched
    result["disease_db_size"] = disease_db.total()
    return result


def enrich_with_analytes(result: dict) -> dict:
    """Look up terpene and cannabinoid details from the Cannlytics analytes dataset."""
    terpene_names     = result.get("likely_terpenes", [])
    cannabinoid_names = result.get("likely_cannabinoids", [])

    # Also pull terpenes from matched strains for richer coverage
    for s in result.get("matched_strains", []):
        for t in s.get("terpenes", []):
            if t and t not in terpene_names:
                terpene_names.append(t)

    terpene_records     = [analyte_db.format_analyte(r) for r in analyte_db.enrich_terpene_list(terpene_names)]
    cannabinoid_records = []
    seen = set()
    for name in cannabinoid_names:
        rec = analyte_db.lookup(name)
        if rec and rec["key"] not in seen:
            seen.add(rec["key"])
            cannabinoid_records.append(analyte_db.format_analyte(rec))

    result["analyte_terpenes"]     = terpene_records
    result["analyte_cannabinoids"] = cannabinoid_records
    return result


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    allowed = {"png", "jpg", "jpeg", "webp", "gif"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        return jsonify({"error": "Unsupported file type"}), 400

    raw = file.read()
    compressed = compress_image(raw)
    b64 = base64.standard_b64encode(compressed).decode("utf-8")

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1400,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": ANALYSIS_PROMPT},
                    ],
                }
            ],
        )

        raw_text = message.content[0].text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(raw_text)

        if result.get("is_cannabis"):
            result = enrich_with_strains(result)
            result = enrich_with_analytes(result)
            result = enrich_with_diseases(result)

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse analysis result", "raw": raw_text}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
