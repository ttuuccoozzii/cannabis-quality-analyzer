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
import seed_diseases as seed_disease_db

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
Carefully inspect the image for any signs of disease, pest infestation, nutrient deficiency, or environmental stress.

Use these specific visual indicators to identify conditions:

FUNGAL:
- Powdery Mildew: white powdery/floury spots or circular patches on leaves or buds
- Botrytis (Bud Rot): gray/brown fuzzy mold inside buds, sudden leaf yellowing on large buds, dusty speckled interior, leaves turning purple near infection
- Leaf Septoria: round yellow/brown spots with darkened borders and dark speck at center on lower leaves
- Root Rot: wilting despite wet medium, yellowing not responsive to watering

NUTRIENT DEFICIENCIES:
- Nitrogen: older lower leaves yellowing from tips upward, pale overall foliage, top stays green
- Nitrogen Toxicity: dark shiny leaves, downward claw curl at leaf tips
- Phosphorus: dark/blue-gray lower leaves, bronze/purple spots, red stems, leaves thickening and curling
- Potassium: brown/burnt edges and tips on older leaves, yellowing margins, green inner veins
- Magnesium: interveinal chlorosis (yellow between veins, green veins) on lower leaves, crispy edges
- Calcium: brown/bronze spots on actively growing leaves, crinkling, purple tints under LED
- Iron: newest leaves bright yellow or white when emerging, yellowing on upper inner foliage
- Zinc: interveinal yellowing on younger leaves, banded appearance, tips dying, clustered new growth
- Nutrient Burn: crispy brown/yellow tips spreading inward, bronze spotting, overall dark green leaves

ENVIRONMENTAL:
- Heat Stress: leaves cupping upward into taco/canoe shape, foxtailing on buds, airy bud structure
- Light Burn: bleached white/yellow patches on top buds directly under lights, green inner veins
- Windburn: clawed leaf shapes, bronze spots confined to areas near fans
- Overwatering: firm downward-curling leaves, dark green color, drooping soon after watering
- Underwatering: papery thin limp wilting leaves that improve after watering

PESTS:
- Spider Mites: tiny yellow/white speckles (stippling), fine silk webbing on buds or leaves
- Broad Mites: twisted glossy blistered new growth with wet plastic appearance, curling leaf edges
- Hemp Russet Mites: beige/yellow mass at tops, dull brittle leaves, distorted new growth
- Aphids: soft-bodied insects on leaf undersides, honeydew causing black sooty mold
- Thrips: shiny silver/bronze irregular spots resembling dried spit or snail trails
- Fungus Gnats: tiny dark flies near soil, wilting mimicking nutrient issues
- Whiteflies: tiny white moth-like insects, white spots on upper leaves
- Mealybugs: white hairy fuzzy insects, white powdery patches, honeydew deposits
- Caterpillars: large irregular holes eaten from leaves, dark droppings on leaves below, cocoons on branches

FUNGAL (ADDITIONAL):
- Fusarium Wilt: sudden wilting not responsive to watering, brown/orange discoloration inside stem near soil
- Alternaria Leaf Spot: purple-brown spots with yellow borders and black spore masses at center
- Verticillium Wilt: wilting on one side of plant, brown vascular discoloration in stem cross-section

NUTRIENT & ENVIRONMENTAL (ADDITIONAL):
- Nutrient Lockout: multiple deficiency symptoms simultaneously despite feeding, white salt crust on soil surface
- Cold Stress: purple or dark blue discoloration on leaves/stems, slowed growth, dark green or purplish hue

GENETIC/REPRODUCTIVE:
- Hermaphrodite / Bananas: small yellow banana-shaped pollen sacs or round balls at bud sites, yellow pollen dust on surfaces
- Accidental Pollination: swollen seed-filled hard lumpy bracts in buds, visible seeds inside flowers, premature pistil die-back

From the following known conditions, list only those you can visually confirm or strongly suspect:
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


_SEED_DISEASE_NAMES = ", ".join(seed_disease_db.get_names())

SEED_PROMPT = f"""You are an expert cannabis seed analyst. Analyze this image of cannabis seeds and provide a full quality and health assessment.

── SEED QUALITY SCORING ──
Score each criterion from 0–10:

1. COLOR & MARKINGS (color)
   Good (8-10): Dark brown, grey-brown or black shell with distinct tiger stripes, mottled patterns or marbling. Rich color indicating full maturity.
   Average (5-7): Light brown, some markings but faded or inconsistent.
   Poor (0-4): Pale, green, or white seeds (immature). Yellowed or bleached (degraded). Uniform color with no markings.

2. SIZE & FULLNESS (fullness)
   Good (8-10): Plump, rounded, well-filled teardrop or oval shape. Feels heavy for size. No flat spots.
   Average (5-7): Moderately full, slight flatness on one side.
   Poor (0-4): Flat, thin, hollow-feeling, or unusually small. Shriveled or deformed.

3. SHELL INTEGRITY (shell)
   Good (8-10): Smooth, hard, uncracked shell with intact waxy coating. No chips, cracks, or holes.
   Average (5-7): Minor surface blemishes, very small hairline marks.
   Poor (0-4): Visible cracks, chips, holes, bore marks, or exposed interior.

4. SURFACE CLEANLINESS (surface)
   Good (8-10): Clean shell, no mold, residue, or contamination. Natural waxy sheen present.
   Average (5-7): Minor surface debris or slight discoloration in small areas.
   Poor (0-4): Mold, fungal coating, oily residue, pest damage evidence, or heavy discoloration.

5. MATURITY & VIABILITY (maturity)
   Good (8-10): All visual indicators of full maturity present. Strong germination potential estimated.
   Average (5-7): Mixed maturity signals — mostly ready but some concerns.
   Poor (0-4): Clear signs of immaturity, rot, degradation, or age beyond viability.

── SEED HEALTH DETECTION ──
Inspect carefully for these specific seed problems:

- Seed Mold/Fungal Infection: white/gray/black fuzzy coating, dark powdery patches, slimy areas
- Immature/Underdeveloped Seed: pale green/white color, flat shape, soft papery shell, no markings
- Cracked or Damaged Shell: visible cracks/splits, chipped edges, crushed shape, exposed interior
- Pest Damage: small holes or bore marks, tunnels, irregular pitting, frass debris on surface
- Rot/Internal Decay: dark brown/black spreading discoloration, sunken collapsed areas, hollow feel
- Old/Degraded Seed: bleached pale shell, dull matte finish, wrinkled surface, loss of markings
- Chemical Contamination: unusual patchy discoloration, oily waxy residue, abnormal unnatural sheen
- Abnormal Shape/Deformation: elongated flat or twisted shape, asymmetrical, fused seeds

Known conditions to detect from: {_SEED_DISEASE_NAMES}

For each detected issue: name, confidence (0.0–1.0), evidence (what you observed).
If seeds appear healthy, return empty array.

── BATCH ASSESSMENT ──
If multiple seeds are visible, assess the overall batch quality and note any variation between seeds.

Return ONLY a raw JSON object (no markdown fences):
{{
  "image_type": "seed",
  "overall_score": <0-100 integer>,
  "grade": "<AAA | AA | A | B | C>",
  "germination_potential": "<Excellent | Good | Fair | Poor | Very Poor>",
  "criteria": {{
    "color":    {{ "score": <0-10>, "note": "<specific observation>" }},
    "fullness": {{ "score": <0-10>, "note": "<specific observation>" }},
    "shell":    {{ "score": <0-10>, "note": "<specific observation>" }},
    "surface":  {{ "score": <0-10>, "note": "<specific observation>" }},
    "maturity": {{ "score": <0-10>, "note": "<specific observation>" }}
  }},
  "summary": "<2-3 sentence overall seed quality assessment>",
  "positives": ["<point>", "<point>"],
  "negatives": ["<point>", "<point>"],
  "seed_count_estimate": "<single | few (2-5) | batch (6+) | unknown>",
  "batch_uniformity": "<high | medium | low | n/a>",
  "detected_issues": [
    {{ "name": "<condition name>", "confidence": <0.0-1.0>, "evidence": "<what you saw>" }}
  ],
  "is_cannabis": <true | false>
}}

If the image does NOT contain cannabis seeds, set is_cannabis to false and all scores to 0.
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


def enrich_with_seed_issues(result: dict) -> dict:
    """Look up full seed disease records for detected issues."""
    detected = result.get("detected_issues", [])
    enriched = []
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}

    for item in detected:
        rec = seed_disease_db.lookup_by_name(item.get("name", ""))
        if rec:
            enriched.append({
                **seed_disease_db.format_disease(rec),
                "confidence": item.get("confidence", 0),
                "evidence":   item.get("evidence", ""),
            })
        else:
            enriched.append({
                "id":                 "unknown",
                "name":               item.get("name", "Unknown"),
                "category":           "unknown",
                "severity":           "medium",
                "visual_symptoms":    [],
                "causes":             "",
                "treatment":          "Consult a seed specialist.",
                "germination_impact": "Unknown.",
                "confidence":         item.get("confidence", 0),
                "evidence":           item.get("evidence", ""),
            })

    enriched.sort(key=lambda x: (severity_order.get(x["severity"], 9), -x["confidence"]))
    result["detected_issues"] = enriched
    return result


def _detect_image_type(b64: str) -> str:
    """Ask Claude whether the image contains buds/flower or seeds."""
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=20,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                {"type": "text", "text": "Does this image show cannabis seeds, or cannabis flower/buds? Reply with exactly one word: 'seeds' or 'buds' or 'other'."},
            ],
        }],
    )
    answer = msg.content[0].text.strip().lower()
    if "seed" in answer:
        return "seed"
    if "bud" in answer or "flower" in answer:
        return "bud"
    return "other"


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
        image_type = _detect_image_type(b64)
        prompt     = SEED_PROMPT if image_type == "seed" else ANALYSIS_PROMPT

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1400,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )

        raw_text = message.content[0].text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(raw_text)

        if result.get("is_cannabis"):
            if result.get("image_type") == "seed":
                result = enrich_with_seed_issues(result)
            else:
                result["image_type"] = "bud"
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
