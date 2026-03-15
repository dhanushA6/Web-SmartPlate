"""
===========================================================
INDIAN FOOD NUTRITION RETRIEVAL SYSTEM
===========================================================

Workflow
--------
1. User provides food name
2. System searches local INDB dataset
3. If found -> return exact nutrient values
4. If not found -> query Gemini 2.5 Flash
5. Gemini returns structured nutrient profile
6. Output returned as dictionary / dataframe


"""

import pandas as pd
import json
import difflib
from pathlib import Path
import sys

import google.generativeai as genai

try:
    from app.config import get_settings
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.config import get_settings

# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

# Prefer local dataset; fall back to backend app/data copy.
INDB_FILE = BASE_DIR / "Anuvaad_INDB_2024.11.xlsx"
if not INDB_FILE.exists():
    INDB_FILE = BASE_DIR.parent / "app" / "data" / "Anuvaad_INDB_2024.11.xlsx"

settings = get_settings()

if settings.GEMINI_API_KEY:
    GOOGLE_API_KEY = settings.GEMINI_API_KEY
else:
    raise Exception("GEMINI_API_KEY not set in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


# =========================================================
# LOAD DATASET
# =========================================================

def load_food_database():

    df = pd.read_excel(INDB_FILE)

    df['food_name_lower'] = df['food_name'].str.lower()

    return df


food_db = load_food_database()


# =========================================================
# SEARCH FOOD IN LOCAL DATABASE
# =========================================================

def search_local_food(food_name):

    food_name = food_name.lower()

    # exact match
    result = food_db[food_db['food_name_lower'] == food_name]

    if len(result) > 0:
        return result.iloc[0].to_dict()

    # fuzzy match
    names = food_db['food_name_lower'].tolist()

    match = difflib.get_close_matches(food_name, names, n=1, cutoff=0.85)

    if match:
        result = food_db[food_db['food_name_lower'] == match[0]]
        return result.iloc[0].to_dict()

    return None


# =========================================================
# GEMINI PROMPT
# =========================================================

def build_gemini_prompt(food_name):

    prompt = f"""
You are a nutrition scientist.

Provide the **most accurate nutrient composition per 100g**
for the South Indian or Indian food: "{food_name}"

Use reliable references such as:
IFCT 2017
USDA
NIN
peer reviewed nutrition databases

Return ONLY valid JSON with these fields:

food_name
energy_kj
energy_kcal
carb_g
protein_g
fat_g
freesugar_g
fibre_g
sfa_mg
cholesterol_mg
calcium_mg
phosphorus_mg
magnesium_mg
sodium_mg
potassium_mg

Rules:
- values must be per 100g edible portion
- use realistic values
- output JSON only
"""

    return prompt


# =========================================================
# GEMINI CALL
# =========================================================

def query_gemini(food_name):

    prompt = build_gemini_prompt(food_name)

    response = model.generate_content(prompt)

    text = response.text.strip()

    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()

    try:
        nutrition = json.loads(text)
    except Exception:
        nutrition = {"error": "Gemini response not valid JSON", "raw": text}

    return nutrition


# =========================================================
# MAIN FUNCTION
# =========================================================

def get_food_nutrition(food_name):

    print("Searching local dataset...")

    local = search_local_food(food_name)

    if local:
        print("Food found in INDB dataset")
        return local

    print("Food not found locally → querying Gemini")

    gemini_data = query_gemini(food_name)

    return gemini_data


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    food = input("Enter food name: ")

    result = get_food_nutrition(food)

    print("\nNutrition Data:\n")

    print(json.dumps(result, indent=4))







""""
food_name
energy_kj
energy_kcal
carb_g
protein_g
fat_g
freesugar_g
fibre_g
sfa_mg
mufa_mg
pufa_mg
cholesterol_mg
calcium_mg
phosphorus_mg
magnesium_mg
sodium_mg
potassium_mg
iron_mg
copper_mg
selenium_ug
chromium_mg
manganese_mg
molybdenum_mg
zinc_mg
vita_ug
vite_mg
vitd2_ug
vitd3_ug
vitk1_ug
vitk2_ug
folate_ug
vitb1_mg
vitb2_mg
vitb3_mg
vitb5_mg
vitb6_mg
vitb7_ug
vitb9_ug
vitc_mg
carotenoids_ug """