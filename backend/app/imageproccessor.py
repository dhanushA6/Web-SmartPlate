from pathlib import Path
import sys
import google.generativeai as genai
from PIL import Image
import json
import io
import os

# =====================================
# CONFIG
# =====================================

try:
    from app.config import get_settings
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.config import get_settings

settings = get_settings()

if settings.GEMINI_API_KEY:
    GOOGLE_API_KEY = settings.GEMINI_API_KEY
else:
    raise Exception("GEMINI_API_KEY not set")

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


# =====================================
# JSON PARSER
# =====================================

def parse_json(text):

    try:

        text = text.strip()

        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()

        return json.loads(text)

    except Exception as e:

        print("JSON parsing error:", e)
        print(text)
        return None


# =====================================
# FOOD IMAGE ANALYSIS
# =====================================

def analyze_food_image(image_path):

    if not os.path.exists(image_path):
        return {"error": "Image not found"}

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    prompt = """
You are a professional nutrition analysis AI.

Analyze the given food image.

Tasks:

1. Detect ALL foods visible.
2. If the same food appears multiple times MERGE them.
3. Estimate realistic quantities.

UNIT RULES:

Every food must include grams.

If naturally counted foods exist include piece count:
(idly, dosa, chapati, egg, bread)

If container foods exist include bowl or cup.

If a unit is not applicable set it to 0.

Nutrition values must be provided PER 100g.

Also calculate TOTAL nutrition for the detected quantity.

NUTRIENTS REQUIRED:

energy_kcal
carb_g
protein_g
fat_g
fibre_g
freesugar_g
sodium_mg
potassium_mg
sfa_mg
cholesterol_mg

Return ONLY JSON.

FORMAT:

{
 "foods":[
  {
   "food_name":"string",

   "quantity":{
    "grams": number,
    "pieces": number,
    "bowl": number,
    "cup": number
   },

   "nutrition_per_100g":{
    "energy_kcal": number,
    "carb_g": number,
    "protein_g": number,
    "fat_g": number,
    "fibre_g": number,
    "freesugar_g": number,
    "sodium_mg": number,
    "potassium_mg": number,
    "sfa_mg": number,
    "cholesterol_mg": number
   }
  }
 ]
}

Do not explain anything.
Return only JSON.
"""

    try:

        response = model.generate_content([prompt, image])

        result = parse_json(response.text)

        if not result:
            return {"error": "Invalid model response"}

        return result

    except Exception as e:

        return {"error": str(e)}


# =====================================
# DRIVER FUNCTION
# =====================================

def test_food_detection():

    image_path = "./images.jpg"

    result = analyze_food_image(image_path)

    print("\nFood Detection Result\n")

    print(json.dumps(result, indent=2))


# =====================================
# MAIN
# =====================================

if __name__ == "__main__":

    print("\nAI MULTI FOOD + NUTRITION ANALYZER")

    test_food_detection()