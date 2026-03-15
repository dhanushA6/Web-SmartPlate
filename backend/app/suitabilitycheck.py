"""
=============================================================================
Rule-Based Food Suitability Engine for Type-2 Diabetes (T2D)
=============================================================================
Author  : Senior ML/Nutrition Engineer (40+ years combined domain experience)
Version : 2.0.0
Python  : 3.9+

Design Philosophy
-----------------
• Every rule is explicit and traceable — no black-box scoring.
• Missing nutrients are silently skipped; only present data drives decisions.
• Two evaluation layers:
    Layer 1 → Individual food safety (glycemic, cardiovascular, renal, etc.)
    Layer 2 → Meal-level macro comparison against patient targets.
• Scores are additive; each rule contributes +1 / 0 / -1.
• Final label thresholds are deliberately conservative for clinical safety.

References
----------
• American Diabetes Association (ADA) Standards of Medical Care 2024
• WHO Healthy Diet Guidelines
• ICMR-NIN Dietary Guidelines for Indians (2024)
• Indian Food Composition Tables (IFCT 2017)
=============================================================================
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ---------------------------------------------------------------------------
# 0.  ENUMERATIONS
# ---------------------------------------------------------------------------

class Suitability(str, Enum):
    SUITABLE     = "Suitable"
    MODERATE     = "Moderate"
    NOT_SUITABLE = "Not Suitable"


class PhysicalActivityLevel(str, Enum):
    SEDENTARY    = "Sedentary"
    LIGHT        = "Light"
    MODERATE     = "Moderate"
    ACTIVE       = "Active"
    VERY_ACTIVE  = "Very Active"


class PrimaryGoal(str, Enum):
    WEIGHT_LOSS      = "Weight loss"
    MAINTENANCE      = "Maintenance"
    GLYCEMIC_CONTROL = "Glycemic control"


class CKDStage(str, Enum):
    G1 = "G1"   # eGFR >= 90
    G2 = "G2"   # 60–89
    G3 = "G3"   # 30–59  ← protein restriction kicks in
    G4 = "G4"   # 15–29
    G5 = "G5"   # <15


# ---------------------------------------------------------------------------
# 1.  DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class FoodNutrients:
    """
    Nutrients expressed PER 100 g of food.
    Every field is Optional — missing values are skipped in rule evaluation.
    Field names mirror IFCT 2017 column headers for direct database mapping.
    """
    # ── Macronutrients ──────────────────────────────────────────────────────
    energy_kcal:    Optional[float] = None   # total energy
    carb_g:         Optional[float] = None   # total carbohydrates
    protein_g:      Optional[float] = None   # total protein
    fat_g:          Optional[float] = None   # total fat
    freesugar_g:    Optional[float] = None   # free / added sugars
    fibre_g:        Optional[float] = None   # dietary fibre

    # ── Fatty Acid Profile (mg per 100 g → converted to g internally) ───────
    sfa_mg:         Optional[float] = None   # saturated fatty acids
    mufa_mg:        Optional[float] = None   # mono-unsaturated FA
    pufa_mg:        Optional[float] = None   # poly-unsaturated FA
    cholesterol_mg: Optional[float] = None   # dietary cholesterol

    # ── Minerals ────────────────────────────────────────────────────────────
    calcium_mg:     Optional[float] = None
    phosphorus_mg:  Optional[float] = None
    magnesium_mg:   Optional[float] = None   # insulin sensitiser
    sodium_mg:      Optional[float] = None   # BP-critical
    potassium_mg:   Optional[float] = None   # BP + cardiac
    iron_mg:        Optional[float] = None
    copper_mg:      Optional[float] = None
    selenium_ug:    Optional[float] = None   # antioxidant (µg)
    chromium_mg:    Optional[float] = None   # glucose tolerance factor
    manganese_mg:   Optional[float] = None
    molybdenum_mg:  Optional[float] = None
    zinc_mg:        Optional[float] = None   # insulin synthesis

    # ── Vitamins ────────────────────────────────────────────────────────────
    vita_ug:        Optional[float] = None   # Vitamin A (RAE, µg)
    vite_mg:        Optional[float] = None   # Vitamin E
    vitd2_ug:       Optional[float] = None   # Ergocalciferol (µg)
    vitd3_ug:       Optional[float] = None   # Cholecalciferol (µg)
    vitk1_ug:       Optional[float] = None   # Phylloquinone
    vitk2_ug:       Optional[float] = None   # Menaquinone
    folate_ug:      Optional[float] = None   # Total folate (µg)
    vitb1_mg:       Optional[float] = None   # Thiamine
    vitb2_mg:       Optional[float] = None   # Riboflavin
    vitb3_mg:       Optional[float] = None   # Niacin
    vitb5_mg:       Optional[float] = None   # Pantothenic acid
    vitb6_mg:       Optional[float] = None   # Pyridoxine
    vitb7_ug:       Optional[float] = None   # Biotin (µg)
    vitb9_ug:       Optional[float] = None   # Folic acid (µg)
    vitc_mg:        Optional[float] = None   # Ascorbic acid
    carotenoids_ug: Optional[float] = None   # Total carotenoids (µg)


@dataclass
class FoodItem:
    """Single food entry submitted for evaluation."""
    food_name:          str
    portion_g:          float
    nutrients_per_100g: FoodNutrients


@dataclass
class PatientProfile:
    """
    Complete clinical profile of the T2D patient.
    All fields used to personalise rule thresholds.
    """
    # ── Demographics ────────────────────────────────────────────────────────
    age:                        int
    gender:                     str                  # "Male" / "Female" / "Other"
    height_cm:                  float
    weight_kg:                  float
    bmi:                        float
    bmi_class_label:            str                  # e.g. "Obese Class I"

    # ── Lifestyle ───────────────────────────────────────────────────────────
    physical_activity_level:    PhysicalActivityLevel
    steps_per_day:              int
    sleep_hours:                float

    # ── Glycaemic Status ────────────────────────────────────────────────────
    diabetes_duration_years:    int
    hba1c_percent:              float
    fasting_glucose_mg_dl:      float
    postprandial_glucose_mg_dl: float

    # ── Lipid Panel ─────────────────────────────────────────────────────────
    triglycerides_mg_dl:        float
    ldl_cholesterol_mg_dl:      float
    hdl_cholesterol_mg_dl:      float

    # ── Blood Pressure ──────────────────────────────────────────────────────
    systolic_bp_mmhg:           float
    diastolic_bp_mmhg:          float

    # ── Renal Function ──────────────────────────────────────────────────────
    egfr_ml_min_1_73m2:         float
    ckd_stage_label:            CKDStage

    # ── Habits ──────────────────────────────────────────────────────────────
    smoking_status:             int                  # 0 = No, 1 = Yes
    alcohol_use:                int                  # 0 = No, 1 = Yes

    # ── Goal ────────────────────────────────────────────────────────────────
    primary_goal:               PrimaryGoal

    def __post_init__(self) -> None:
        # Strictly keep binary habit flags for predictable downstream logic.
        if self.smoking_status not in (0, 1):
            raise ValueError("smoking_status must be 0 or 1")
        if self.alcohol_use not in (0, 1):
            raise ValueError("alcohol_use must be 0 or 1")


@dataclass
class MealMacroTargets:
    """
    Per-meal macro targets prescribed for the patient.
    Derived upstream from total daily requirements / number of meals.
    """
    calories_kcal:     float
    carbohydrates_g:   float
    protein_g:         float
    fat_g:             float
    fiber_g:           float


# ---------------------------------------------------------------------------
# 2.  RULE RESULT — ATOMIC UNIT OF EXPLANATION
# ---------------------------------------------------------------------------

@dataclass
class RuleResult:
    """
    One rule evaluation outcome.
    Carries the rule name, observed value, threshold used,
    suitability label, numeric score, and a human-readable reason.
    """
    rule_name:   str
    observed:    Any                  # actual measured value
    threshold:   str                  # threshold description
    label:       Suitability
    score:       int                  # +1, 0, or -1
    reason:      str
    skipped:     bool = False         # True when nutrient was absent


# ---------------------------------------------------------------------------
# 3.  PORTION NORMALISER
# ---------------------------------------------------------------------------

class FoodNormaliser:
    """
    Converts per-100 g nutrient values to actual portion-adjusted values.
    Returns a new FoodNutrients object with adjusted values.
    Missing fields remain None so downstream rules skip them cleanly.
    """

    @staticmethod
    def normalise(nutrients: FoodNutrients, portion_g: float) -> FoodNutrients:
        """
        Scale every non-None nutrient by (portion_g / 100).

        Parameters
        ----------
        nutrients : FoodNutrients  — per-100 g values
        portion_g : float          — actual consumed portion in grams

        Returns
        -------
        FoodNutrients — portion-adjusted values
        """
        factor = portion_g / 100.0
        adjusted = FoodNutrients()

        for fname in nutrients.__dataclass_fields__:
            raw = getattr(nutrients, fname)
            if raw is not None:
                setattr(adjusted, fname, round(raw * factor, 4))
            # else: leave as None → rule will skip

        return adjusted


# ---------------------------------------------------------------------------
# 4.  FOOD SAFETY RULES  (Layer 1 — per-food)
# ---------------------------------------------------------------------------

class FoodRules:
    """
    Stateless collection of rule evaluators.
    Each method receives the portion-adjusted FoodNutrients and returns
    a RuleResult.  If the required nutrient is None the result is marked
    skipped=True and contributes score=0 (neutral) so the overall scoring
    is not punished for missing data.
    """

    # ── 4.1  Glycaemic Safety ───────────────────────────────────────────────

    @staticmethod
    def rule_free_sugar(n: FoodNutrients) -> RuleResult:
        """
        Free sugar is the primary glycaemic spike driver.
        ADA recommends minimising added/free sugars for T2D.
        Threshold (per portion):
          0 g         → Suitable   (+1)
          0 < x ≤ 5 g → Moderate   ( 0)
          > 5 g       → Not Suitable (-1)
        """
        name = "Free Sugar"
        thresh = "0 g=Suitable | 0–5 g=Moderate | >5 g=Not Suitable"

        if n.freesugar_g is None:
            return RuleResult(name, None, thresh, Suitability.SUITABLE, 0,
                              "Free sugar data absent — rule skipped.", skipped=True)

        v = n.freesugar_g
        if v == 0:
            return RuleResult(name, v, thresh, Suitability.SUITABLE, 1,
                              f"No free sugar ({v} g) — glycaemically safe.")
        elif v <= 5:
            return RuleResult(name, v, thresh, Suitability.MODERATE, 0,
                              f"Moderate free sugar ({v:.1f} g) — monitor post-meal glucose.")
        else:
            return RuleResult(name, v, thresh, Suitability.NOT_SUITABLE, -1,
                              f"High free sugar ({v:.1f} g) — likely glycaemic spike risk.")

    @staticmethod
    def rule_fibre(n: FoodNutrients) -> RuleResult:
        """
        Dietary fibre slows glucose absorption and improves insulin sensitivity.
        Threshold (per portion):
          ≥ 3 g       → Suitable   (+1)
          1–3 g       → Moderate   ( 0)
          < 1 g       → Not Suitable (-1)
        """
        name = "Dietary Fibre"
        thresh = "≥3 g=Suitable | 1–3 g=Moderate | <1 g=Not Suitable"

        if n.fibre_g is None:
            return RuleResult(name, None, thresh, Suitability.SUITABLE, 0,
                              "Fibre data absent — rule skipped.", skipped=True)

        v = n.fibre_g
        if v >= 3:
            return RuleResult(name, v, thresh, Suitability.SUITABLE, 1,
                              f"Good fibre content ({v:.1f} g) — supports glycaemic control.")
        elif v >= 1:
            return RuleResult(name, v, thresh, Suitability.MODERATE, 0,
                              f"Moderate fibre ({v:.1f} g) — acceptable but not optimal.")
        else:
            return RuleResult(name, v, thresh, Suitability.NOT_SUITABLE, -1,
                              f"Low fibre ({v:.1f} g) — rapid glucose absorption possible.")

    # ── 4.2  Cardiovascular Safety ─────────────────────────────────────────

    @staticmethod
    def rule_saturated_fat(n: FoodNutrients) -> RuleResult:
        """
        Saturated fat raises LDL and increases CVD risk — already elevated in T2D.
        SFA is stored as mg in IFCT; convert to g first.
        Threshold (per portion):
          ≤ 1.5 g     → Suitable   (+1)
          1.5–5 g     → Moderate   ( 0)
          > 5 g       → Not Suitable (-1)
        """
        name = "Saturated Fat (SFA)"
        thresh = "≤1.5 g=Suitable | 1.5–5 g=Moderate | >5 g=Not Suitable"

        if n.sfa_mg is None:
            return RuleResult(name, None, thresh, Suitability.SUITABLE, 0,
                              "SFA data absent — rule skipped.", skipped=True)

        sfa_g = n.sfa_mg / 1000.0
        v = round(sfa_g, 3)
        if sfa_g <= 1.5:
            return RuleResult(name, v, thresh, Suitability.SUITABLE, 1,
                              f"Low SFA ({v} g) — cardiovascular safe.")
        elif sfa_g <= 5:
            return RuleResult(name, v, thresh, Suitability.MODERATE, 0,
                              f"Moderate SFA ({v} g) — within tolerable range; watch cumulative intake.")
        else:
            return RuleResult(name, v, thresh, Suitability.NOT_SUITABLE, -1,
                              f"High SFA ({v} g) — raises LDL; avoid or minimise.")

    @staticmethod
    def rule_cholesterol(n: FoodNutrients) -> RuleResult:
        """
        Dietary cholesterol has secondary impact on serum LDL; important for
        patients with dyslipidaemia co-morbid with T2D.
        Threshold (per portion):
          ≤ 20 mg     → Suitable   (+1)
          20–100 mg   → Moderate   ( 0)
          > 100 mg    → Not Suitable (-1)
        """
        name = "Dietary Cholesterol"
        thresh = "≤20 mg=Suitable | 20–100 mg=Moderate | >100 mg=Not Suitable"

        if n.cholesterol_mg is None:
            return RuleResult(name, None, thresh, Suitability.SUITABLE, 0,
                              "Cholesterol data absent — rule skipped.", skipped=True)

        v = n.cholesterol_mg
        if v <= 20:
            return RuleResult(name, v, thresh, Suitability.SUITABLE, 1,
                              f"Low cholesterol ({v:.1f} mg) — heart-safe.")
        elif v <= 100:
            return RuleResult(name, v, thresh, Suitability.MODERATE, 0,
                              f"Moderate cholesterol ({v:.1f} mg) — acceptable in context.")
        else:
            return RuleResult(name, v, thresh, Suitability.NOT_SUITABLE, -1,
                              f"High cholesterol ({v:.1f} mg) — limit frequency for CVD risk.")

    @staticmethod
    def rule_sodium(n: FoodNutrients) -> RuleResult:
        """
        High sodium is hypertensive; T2D patients have 2× higher hypertension prevalence.
        Threshold (per portion):
          ≤ 120 mg    → Suitable   (+1)
          120–400 mg  → Moderate   ( 0)
          > 400 mg    → Not Suitable (-1)
        """
        name = "Sodium"
        thresh = "≤120 mg=Suitable | 120–400 mg=Moderate | >400 mg=Not Suitable"

        if n.sodium_mg is None:
            return RuleResult(name, None, thresh, Suitability.SUITABLE, 0,
                              "Sodium data absent — rule skipped.", skipped=True)

        v = n.sodium_mg
        if v <= 120:
            return RuleResult(name, v, thresh, Suitability.SUITABLE, 1,
                              f"Low sodium ({v:.1f} mg) — BP-safe.")
        elif v <= 400:
            return RuleResult(name, v, thresh, Suitability.MODERATE, 0,
                              f"Moderate sodium ({v:.1f} mg) — acceptable, watch total daily intake.")
        else:
            return RuleResult(name, v, thresh, Suitability.NOT_SUITABLE, -1,
                              f"High sodium ({v:.1f} mg) — risk of BP elevation.")

    # ── 4.3  Energy Density ────────────────────────────────────────────────

    @staticmethod
    def rule_energy_density(n: FoodNutrients) -> RuleResult:
        """
        Energy density > 400 kcal/100 g promotes overconsumption and weight gain.
        NOTE: We evaluate the raw per-100 g value (not portion) because energy
        density is an intrinsic food property.
        """
        name = "Energy Density"
        thresh = "≤400 kcal/100 g=Suitable | >400 kcal/100 g=Not Suitable"

        if n.energy_kcal is None:
            return RuleResult(name, None, thresh, Suitability.SUITABLE, 0,
                              "Energy data absent — rule skipped.", skipped=True)

        # energy_kcal at this point is the portion-adjusted value.
        # We cannot reverse to per-100 g without portion_g, so this rule
        # is best evaluated in the engine before normalisation.  The engine
        # calls this with raw per-100 g value.  See FoodSuitabilityEngine._evaluate_food.
        v = n.energy_kcal
        if v <= 400:
            return RuleResult(name, v, thresh, Suitability.SUITABLE, 1,
                              f"Moderate energy density ({v:.1f} kcal/100 g).")
        else:
            return RuleResult(name, v, thresh, Suitability.NOT_SUITABLE, -1,
                              f"High energy density ({v:.1f} kcal/100 g) — risk of caloric overload.")


# ---------------------------------------------------------------------------
# 5.  MICRONUTRIENT BENEFIT RULES  (skip-safe)
# ---------------------------------------------------------------------------

class MicronutrientRules:
    """
    Awards +1 for each beneficial micronutrient that meets its threshold.
    Every check begins with a None guard — missing data → rule skipped (score 0).

    Clinical rationale per nutrient
    --------------------------------
    Magnesium   : Cofactor in >300 enzymatic reactions; improves insulin sensitivity.
                  Meta-analyses show inverse association with T2D incidence.
    Potassium   : Counter-regulatory to sodium; lowers BP; protective renal effect.
    Vitamin C   : Antioxidant; reduces oxidative stress markers common in T2D.
    Zinc        : Required for insulin crystallisation and secretion from β-cells.
    Chromium    : Potentiates insulin action via chromodulin; improves HbA1c slightly.
    Selenium    : Antioxidant via glutathione peroxidase; anti-inflammatory.
    Vitamin D   : Deficiency strongly correlated with insulin resistance in multiple cohorts.
    Vitamin B6  : Involved in glucose metabolism and peripheral neuropathy prevention.
    Folate      : Lowers homocysteine — elevated in T2D; reduces CVD risk.
    Vitamin B12 : Deficient in metformin users; critical for neuropathy prevention.
                  (Mapped from vitb9_ug as proxy — ideally a separate field.)
    Calcium     : Involved in insulin secretion cascades; bone health in T2D patients.
    Iron        : Anaemia co-morbidity is common; adequate iron supports haemoglobin A1c
                  measurement accuracy.
    Vitamin E   : Antioxidant; reduces lipid peroxidation in T2D.
    Vitamin A   : Retinol supports retinal health — critical given diabetic retinopathy risk.
    Carotenoids : Pro-vitamin A + antioxidant; anti-inflammatory.
    MUFA        : Oleic-acid-rich profile improves lipid panel; recommended over SFA.
    PUFA        : Omega-3/6 precursors; anti-inflammatory; HDL-raising.
    """

    # Thresholds per portion (except MUFA/PUFA which are per-portion in mg)
    THRESHOLDS: Dict[str, Tuple[str, float, str]] = {
        # field_name          : (display_name,           threshold_value, unit)
        "magnesium_mg"        : ("Magnesium",             50.0,  "mg"),
        "potassium_mg"        : ("Potassium",             300.0, "mg"),
        "vitc_mg"             : ("Vitamin C",             10.0,  "mg"),
        "zinc_mg"             : ("Zinc",                  2.0,   "mg"),
        "chromium_mg"         : ("Chromium",              0.02,  "mg"),
        "selenium_ug"         : ("Selenium",              10.0,  "µg"),
        "calcium_mg"          : ("Calcium",               80.0,  "mg"),
        "iron_mg"             : ("Iron",                  2.0,   "mg"),
        "vite_mg"             : ("Vitamin E",             2.0,   "mg"),
        "vita_ug"             : ("Vitamin A",             50.0,  "µg"),
        "carotenoids_ug"      : ("Carotenoids",           500.0, "µg"),
        "folate_ug"           : ("Folate",                50.0,  "µg"),
        "vitb6_mg"            : ("Vitamin B6",            0.3,   "mg"),
        "vitb9_ug"            : ("Vitamin B9 (Folic Acid)", 50.0, "µg"),
        "vitd2_ug"            : ("Vitamin D2",            1.0,   "µg"),
        "vitd3_ug"            : ("Vitamin D3",            1.0,   "µg"),
        "vitb1_mg"            : ("Vitamin B1 (Thiamine)", 0.2,   "mg"),
        "vitb2_mg"            : ("Vitamin B2 (Riboflavin)", 0.2, "mg"),
        "vitb3_mg"            : ("Vitamin B3 (Niacin)",   2.0,   "mg"),
        "vitb7_ug"            : ("Vitamin B7 (Biotin)",   5.0,   "µg"),
        "phosphorus_mg"       : ("Phosphorus",            80.0,  "mg"),
        "manganese_mg"        : ("Manganese",             0.5,   "mg"),
        "mufa_mg"             : ("MUFA (Heart-Healthy FA)", 500.0, "mg"),
        "pufa_mg"             : ("PUFA (Essential FA)",   300.0, "mg"),
    }

    @classmethod
    def evaluate_all(cls, n: FoodNutrients) -> List[RuleResult]:
        """
        Iterate over every micronutrient threshold.
        Skip if field is None.  Award +1 if value meets threshold.
        """
        results: List[RuleResult] = []

        for field_name, (display_name, threshold, unit) in cls.THRESHOLDS.items():
            value = getattr(n, field_name, None)

            if value is None:
                results.append(RuleResult(
                    rule_name = f"Micronutrient: {display_name}",
                    observed  = None,
                    threshold = f"≥{threshold} {unit}",
                    label     = Suitability.SUITABLE,
                    score     = 0,
                    reason    = f"{display_name} data absent — rule skipped.",
                    skipped   = True
                ))
                continue

            if value >= threshold:
                results.append(RuleResult(
                    rule_name = f"Micronutrient: {display_name}",
                    observed  = round(value, 3),
                    threshold = f"≥{threshold} {unit}",
                    label     = Suitability.SUITABLE,
                    score     = 1,
                    reason    = (
                        f"Good {display_name} ({round(value,2)} {unit} ≥ {threshold} {unit}) — "
                        f"beneficial for T2D management."
                    )
                ))
            else:
                results.append(RuleResult(
                    rule_name = f"Micronutrient: {display_name}",
                    observed  = round(value, 3),
                    threshold = f"≥{threshold} {unit}",
                    label     = Suitability.MODERATE,
                    score     = 0,
                    reason    = (
                        f"{display_name} below beneficial threshold "
                        f"({round(value,2)} {unit} < {threshold} {unit})."
                    )
                ))

        return results


# ---------------------------------------------------------------------------
# 6.  PATIENT CONDITION RULES  (contextual penalties / adjustments)
# ---------------------------------------------------------------------------

class PatientConditionRules:
    """
    Applies clinical-profile-specific adjustments to food scoring.
    Rules fire only when the relevant clinical parameter exceeds its threshold.
    """

    @staticmethod
    def rule_high_hba1c_carb(n: FoodNutrients, patient: PatientProfile) -> Optional[RuleResult]:
        """
        If HbA1c ≥ 8 % (poorly controlled), penalise foods with high carbohydrate
        load (> 30 g per portion).  ADA recommends <45 % energy from carbs
        for poorly controlled T2D.
        Returns None if HbA1c is well-controlled (no rule needed).
        """
        if patient.hba1c_percent < 8.0:
            return None
        if n.carb_g is None:
            return RuleResult(
                "High HbA1c — Carb Penalty", None,
                "carb >30 g penalised when HbA1c ≥8%",
                Suitability.SUITABLE, 0,
                "Carbohydrate data absent — condition rule skipped.", skipped=True
            )
        v = n.carb_g
        if v > 30:
            return RuleResult(
                "High HbA1c — Carb Penalty", round(v,2),
                "≤30 g carb when HbA1c ≥8%",
                Suitability.NOT_SUITABLE, -1,
                f"HbA1c={patient.hba1c_percent}% (poorly controlled). "
                f"Carbs={v:.1f} g exceed 30 g safe ceiling — glycaemic risk high."
            )
        return RuleResult(
            "High HbA1c — Carb Check", round(v,2),
            "≤30 g carb when HbA1c ≥8%",
            Suitability.SUITABLE, 1,
            f"HbA1c={patient.hba1c_percent}%. Carbs={v:.1f} g within acceptable range."
        )

    @staticmethod
    def rule_high_hba1c_sugar(n: FoodNutrients, patient: PatientProfile) -> Optional[RuleResult]:
        """Penalise free sugar when HbA1c ≥ 8 %."""
        if patient.hba1c_percent < 8.0:
            return None
        if n.freesugar_g is None:
            return RuleResult(
                "High HbA1c — Sugar Penalty", None,
                "sugar >2 g penalised when HbA1c ≥8%",
                Suitability.SUITABLE, 0,
                "Free sugar data absent — condition rule skipped.", skipped=True
            )
        v = n.freesugar_g
        if v > 2:
            return RuleResult(
                "High HbA1c — Sugar Penalty", round(v,2),
                "≤2 g sugar when HbA1c ≥8%",
                Suitability.NOT_SUITABLE, -1,
                f"HbA1c={patient.hba1c_percent}% + free sugar={v:.1f} g — "
                f"strictly restrict to prevent further HbA1c deterioration."
            )
        return RuleResult(
            "High HbA1c — Sugar Check", round(v,2),
            "≤2 g sugar when HbA1c ≥8%",
            Suitability.SUITABLE, 0,
            f"Free sugar={v:.1f} g is within tight limit for poorly controlled T2D."
        )

    @staticmethod
    def rule_hypertension_sodium(n: FoodNutrients, patient: PatientProfile) -> Optional[RuleResult]:
        """
        Stricter sodium limit when systolic BP ≥ 140 mmHg.
        AHA recommends < 1500 mg/day for hypertension → ~200 mg per meal maximum.
        """
        if patient.systolic_bp_mmhg < 140:
            return None
        if n.sodium_mg is None:
            return RuleResult(
                "Hypertension — Sodium Penalty", None,
                "sodium >200 mg penalised when SBP ≥140",
                Suitability.SUITABLE, 0,
                "Sodium data absent — hypertension rule skipped.", skipped=True
            )
        v = n.sodium_mg
        thresh_name = "Hypertension — Sodium Check"
        if v > 200:
            return RuleResult(
                thresh_name, round(v,2),
                "≤200 mg sodium when SBP ≥140 mmHg",
                Suitability.NOT_SUITABLE, -2,           # double penalty — BP-critical
                f"SBP={patient.systolic_bp_mmhg} mmHg (hypertensive). "
                f"Sodium={v:.1f} mg exceeds 200 mg safety limit. "
                f"Score penalised ×2 given active hypertension."
            )
        return RuleResult(
            thresh_name, round(v,2),
            "≤200 mg sodium when SBP ≥140 mmHg",
            Suitability.SUITABLE, 1,
            f"SBP={patient.systolic_bp_mmhg} mmHg. Sodium={v:.1f} mg — within hypertension limit."
        )

    @staticmethod
    def rule_ckd_protein(n: FoodNutrients, patient: PatientProfile) -> Optional[RuleResult]:
        """
        CKD G3+ requires protein restriction (0.6–0.8 g/kg/day).
        At meal level this translates to roughly ≤ 15 g per main meal.
        Penalise high-protein foods when CKD is ≥ G3.
        """
        ckd_restricted = patient.ckd_stage_label in (CKDStage.G3, CKDStage.G4, CKDStage.G5)
        if not ckd_restricted:
            return None
        if n.protein_g is None:
            return RuleResult(
                "CKD — Protein Restriction", None,
                "protein >15 g penalised when CKD ≥G3",
                Suitability.SUITABLE, 0,
                "Protein data absent — CKD rule skipped.", skipped=True
            )
        v = n.protein_g
        protein_limit_g = 0.6 * patient.weight_kg / 3   # rough per-meal estimate (3 meals)
        if v > protein_limit_g:
            return RuleResult(
                "CKD — Protein Restriction", round(v,2),
                f"≤{round(protein_limit_g,1)} g protein (CKD {patient.ckd_stage_label.value})",
                Suitability.NOT_SUITABLE, -1,
                f"CKD Stage {patient.ckd_stage_label.value}: protein={v:.1f} g "
                f"exceeds per-meal limit of {protein_limit_g:.1f} g. "
                f"Excess protein worsens renal decline."
            )
        return RuleResult(
            "CKD — Protein Restriction", round(v,2),
            f"≤{round(protein_limit_g,1)} g protein (CKD {patient.ckd_stage_label.value})",
            Suitability.SUITABLE, 1,
            f"CKD Stage {patient.ckd_stage_label.value}: protein={v:.1f} g within safe limit."
        )

    @classmethod
    def evaluate_all(cls, n: FoodNutrients, patient: PatientProfile) -> List[RuleResult]:
        """Run all condition rules; filter out None (non-applicable) entries."""
        candidates = [
            cls.rule_high_hba1c_carb(n, patient),
            cls.rule_high_hba1c_sugar(n, patient),
            cls.rule_hypertension_sodium(n, patient),
            cls.rule_ckd_protein(n, patient),
        ]
        return [r for r in candidates if r is not None]


# ---------------------------------------------------------------------------
# 7.  SCORING ENGINE
# ---------------------------------------------------------------------------

class ScoringEngine:
    """
    Aggregates a list of RuleResult objects into a final Suitability label.

    Scoring logic
    -------------
    • Each non-skipped rule contributes its score.
    • Critical rules (double-penalty flags) are already encoded in the score field.
    • Thresholds for final label (conservative clinical bias):
        score ≥ 3  → Suitable
        1 ≤ score ≤ 2 → Moderate
        score ≤ 0  → Not Suitable
    """

    SUITABLE_THRESHOLD     = 3
    NOT_SUITABLE_THRESHOLD = 1    # below this → Not Suitable

    @classmethod
    def compute(cls, rules: List[RuleResult]) -> Tuple[Suitability, int]:
        """
        Sum scores across all non-skipped rules.
        Returns (final_label, total_score).
        """
        total = sum(r.score for r in rules if not r.skipped)

        if total >= cls.SUITABLE_THRESHOLD:
            return Suitability.SUITABLE, total
        elif total >= cls.NOT_SUITABLE_THRESHOLD:
            return Suitability.MODERATE, total
        else:
            return Suitability.NOT_SUITABLE, total


# ---------------------------------------------------------------------------
# 8.  MEAL EVALUATOR  (Layer 2 — aggregate nutrients vs targets)
# ---------------------------------------------------------------------------

class MealEvaluator:
    """
    Aggregates portion-adjusted nutrients across all foods in a meal,
    then compares totals against the patient's MealMacroTargets.
    """

    @staticmethod
    def aggregate(foods_adjusted: List[FoodNutrients]) -> Dict[str, Optional[float]]:
        """
        Sum macro nutrients across all foods.
        If ALL foods are missing a field → sum stays None.
        If at least one food has a value → partial sum used.
        """
        totals = {
            "total_calories":     None,
            "total_carbs":        None,
            "total_protein":      None,
            "total_fat":          None,
            "total_fiber":        None,
            "total_freesugar":    None,
            "total_sodium":       None,
        }

        field_map = {
            "total_calories":   "energy_kcal",
            "total_carbs":      "carb_g",
            "total_protein":    "protein_g",
            "total_fat":        "fat_g",
            "total_fiber":      "fibre_g",
            "total_freesugar":  "freesugar_g",
            "total_sodium":     "sodium_mg",
        }

        for food_n in foods_adjusted:
            for total_key, field in field_map.items():
                val = getattr(food_n, field, None)
                if val is not None:
                    totals[total_key] = (totals[total_key] or 0.0) + val

        # Round for display
        return {k: (round(v, 2) if v is not None else None) for k, v in totals.items()}

    @staticmethod
    def evaluate(aggregated: Dict[str, Optional[float]],
                 targets: MealMacroTargets) -> List[RuleResult]:
        """
        Compare aggregated meal nutrients against targets.
        Skip comparison for any nutrient whose aggregated value is None.
        """
        results: List[RuleResult] = []

        # ── Carbohydrates ──────────────────────────────────────────────────
        if aggregated["total_carbs"] is not None:
            ratio = aggregated["total_carbs"] / targets.carbohydrates_g
            thresh = "ratio ≤1.0=Suitable | 1.0–1.3=Moderate | >1.3=Not Suitable"
            if ratio <= 1.0:
                results.append(RuleResult(
                    "Meal Carbs vs Target", round(aggregated["total_carbs"],1),
                    thresh, Suitability.SUITABLE, 1,
                    f"Meal carbs {aggregated['total_carbs']:.1f} g ≤ target {targets.carbohydrates_g} g "
                    f"(ratio={ratio:.2f})."
                ))
            elif ratio <= 1.3:
                results.append(RuleResult(
                    "Meal Carbs vs Target", round(aggregated["total_carbs"],1),
                    thresh, Suitability.MODERATE, 0,
                    f"Meal carbs {aggregated['total_carbs']:.1f} g slightly over target "
                    f"{targets.carbohydrates_g} g (ratio={ratio:.2f})."
                ))
            else:
                results.append(RuleResult(
                    "Meal Carbs vs Target", round(aggregated["total_carbs"],1),
                    thresh, Suitability.NOT_SUITABLE, -1,
                    f"Meal carbs {aggregated['total_carbs']:.1f} g significantly exceed target "
                    f"{targets.carbohydrates_g} g (ratio={ratio:.2f})."
                ))

        # ── Protein ────────────────────────────────────────────────────────
        if aggregated["total_protein"] is not None:
            ratio = aggregated["total_protein"] / targets.protein_g
            thresh = "ratio 0.6–1.4=Suitable | otherwise=Moderate"
            if 0.6 <= ratio <= 1.4:
                results.append(RuleResult(
                    "Meal Protein vs Target", round(aggregated["total_protein"],1),
                    thresh, Suitability.SUITABLE, 1,
                    f"Meal protein {aggregated['total_protein']:.1f} g within target range "
                    f"{targets.protein_g} g (ratio={ratio:.2f})."
                ))
            else:
                label_txt = "below" if ratio < 0.6 else "above"
                results.append(RuleResult(
                    "Meal Protein vs Target", round(aggregated["total_protein"],1),
                    thresh, Suitability.MODERATE, 0,
                    f"Meal protein {aggregated['total_protein']:.1f} g is {label_txt} optimal range "
                    f"(ratio={ratio:.2f})."
                ))

        # ── Fat ────────────────────────────────────────────────────────────
        if aggregated["total_fat"] is not None:
            ratio = aggregated["total_fat"] / targets.fat_g
            thresh = "ratio ≤1.2=Suitable | >1.2=Not Suitable"
            if ratio <= 1.2:
                results.append(RuleResult(
                    "Meal Fat vs Target", round(aggregated["total_fat"],1),
                    thresh, Suitability.SUITABLE, 1,
                    f"Meal fat {aggregated['total_fat']:.1f} g within limit "
                    f"(ratio={ratio:.2f})."
                ))
            else:
                results.append(RuleResult(
                    "Meal Fat vs Target", round(aggregated["total_fat"],1),
                    thresh, Suitability.NOT_SUITABLE, -1,
                    f"Meal fat {aggregated['total_fat']:.1f} g exceeds target {targets.fat_g} g "
                    f"(ratio={ratio:.2f})."
                ))

        # ── Fibre ──────────────────────────────────────────────────────────
        if aggregated["total_fiber"] is not None:
            thresh = f"≥{targets.fiber_g} g=Suitable"
            if aggregated["total_fiber"] >= targets.fiber_g:
                results.append(RuleResult(
                    "Meal Fibre vs Target", round(aggregated["total_fiber"],1),
                    thresh, Suitability.SUITABLE, 1,
                    f"Meal fibre {aggregated['total_fiber']:.1f} g meets target {targets.fiber_g} g."
                ))
            else:
                results.append(RuleResult(
                    "Meal Fibre vs Target", round(aggregated["total_fiber"],1),
                    thresh, Suitability.MODERATE, 0,
                    f"Meal fibre {aggregated['total_fiber']:.1f} g below target {targets.fiber_g} g — "
                    f"consider adding a fibre-rich side."
                ))

        # ── Calories ───────────────────────────────────────────────────────
        if aggregated["total_calories"] is not None:
            ratio = aggregated["total_calories"] / targets.calories_kcal
            thresh = "ratio ≤1.1=Suitable | 1.1–1.3=Moderate | >1.3=Not Suitable"
            if ratio <= 1.1:
                results.append(RuleResult(
                    "Meal Calories vs Target", round(aggregated["total_calories"],1),
                    thresh, Suitability.SUITABLE, 1,
                    f"Meal calories {aggregated['total_calories']:.1f} kcal within target "
                    f"{targets.calories_kcal} kcal (ratio={ratio:.2f})."
                ))
            elif ratio <= 1.3:
                results.append(RuleResult(
                    "Meal Calories vs Target", round(aggregated["total_calories"],1),
                    thresh, Suitability.MODERATE, 0,
                    f"Meal calories slightly over target (ratio={ratio:.2f})."
                ))
            else:
                results.append(RuleResult(
                    "Meal Calories vs Target", round(aggregated["total_calories"],1),
                    thresh, Suitability.NOT_SUITABLE, -1,
                    f"Meal calories significantly exceed target (ratio={ratio:.2f})."
                ))

        return results


# ---------------------------------------------------------------------------
# 9.  MAIN ENGINE
# ---------------------------------------------------------------------------

class FoodSuitabilityEngine:
    """
    Orchestrates the two-layer evaluation pipeline.

    Usage
    -----
    engine = FoodSuitabilityEngine(patient, meal_targets)
    result = engine.evaluate(foods)
    print(json.dumps(result, indent=2))
    """

    def __init__(self, patient: PatientProfile, meal_targets: MealMacroTargets):
        self.patient      = patient
        self.meal_targets = meal_targets
        self._normaliser  = FoodNormaliser()

    # ── Internal helpers ───────────────────────────────────────────────────

    def _evaluate_food(self, food: FoodItem) -> Dict:
        """
        Full Layer-1 evaluation for a single food item.
        Returns a dict with food_name, suitability, score, analysis.
        """
        raw  = food.nutrients_per_100g
        norm = self._normaliser.normalise(raw, food.portion_g)

        rules: List[RuleResult] = []

        # Basic food safety rules (use portion-adjusted nutrients for most rules)
        rules.append(FoodRules.rule_free_sugar(norm))
        rules.append(FoodRules.rule_fibre(norm))
        rules.append(FoodRules.rule_saturated_fat(norm))
        rules.append(FoodRules.rule_cholesterol(norm))
        rules.append(FoodRules.rule_sodium(norm))

        # Energy density — evaluated on raw per-100 g values (intrinsic property)
        energy_rule_input       = FoodNutrients()
        energy_rule_input.energy_kcal = raw.energy_kcal   # per 100 g, not portion-adjusted
        rules.append(FoodRules.rule_energy_density(energy_rule_input))

        # Micronutrient benefits — portion-adjusted values
        micro_results = MicronutrientRules.evaluate_all(norm)
        rules.extend(micro_results)

        # Patient condition rules — portion-adjusted values + profile
        condition_results = PatientConditionRules.evaluate_all(norm, self.patient)
        rules.extend(condition_results)

        final_label, total_score = ScoringEngine.compute(rules)

        compact_rules = self._serialise_rules(rules)
        reasons = [r["reason"] for r in compact_rules if not r["skipped"]]

        return {
            "food_name":   food.food_name,
            "portion_g":   food.portion_g,
            "suitability": final_label.value,
            "score":       total_score,
            "rules":       compact_rules,
            "reasons":     reasons,
        }

    @staticmethod
    def _serialise_rules(rules: List[RuleResult]) -> List[Dict]:
        """Convert RuleResult list to compact JSON-serialisable dicts."""
        out = []
        for r in rules:
            out.append({
                "rule":    r.rule_name,
                "label":   r.label.value,
                "score":   r.score,
                "reason":  r.reason,
                "skipped": r.skipped,
            })
        return out

    @staticmethod
    def _simple_reason_from_rules(rules: List[Dict], suitability: str) -> str:
        """
        Build a short, user-friendly 1-2 line reason from compact rule output.
        Priority is chosen by final suitability label.
        """
        active = [r for r in rules if not r.get("skipped", False)]
        if not active:
            return "Insufficient data to judge confidently; provide more nutrition details."

        if suitability == Suitability.NOT_SUITABLE.value:
            picks = [r["reason"] for r in active if r.get("score", 0) < 0]
            if not picks:
                picks = [r["reason"] for r in active if r.get("label") == Suitability.NOT_SUITABLE.value]
            if not picks:
                picks = [active[0]["reason"]]
            return " ".join(picks[:2])

        if suitability == Suitability.SUITABLE.value:
            picks = [r["reason"] for r in active if r.get("score", 0) > 0]
            if not picks:
                picks = [r["reason"] for r in active if r.get("label") == Suitability.SUITABLE.value]
            if not picks:
                picks = [active[0]["reason"]]
            return " ".join(picks[:2])

        # Moderate: surface one limiting factor plus one positive/neutral factor.
        caution = [r["reason"] for r in active if r.get("score", 0) < 0 or r.get("label") == Suitability.MODERATE.value]
        support = [r["reason"] for r in active if r.get("score", 0) > 0]

        parts: List[str] = []
        if caution:
            parts.append(caution[0])
        if support:
            parts.append(support[0])
        if not parts:
            parts.append(active[0]["reason"])
        return " ".join(parts[:2])

    def _build_user_friendly_response(
        self,
        foods: List[Dict],
        meal_rules: List[Dict],
        meal_suitability: str,
        meal_note: str,
    ) -> Dict:
        """Create concise, app-ready summary text for end users."""
        food_summaries = []
        for food in foods:
            food_summaries.append({
                "food_name": food["food_name"],
                "suitability": food["suitability"],
                "simple_reason": self._simple_reason_from_rules(
                    food["rules"],
                    food["suitability"],
                ),
            })

        meal_simple_reason = self._simple_reason_from_rules(meal_rules, meal_suitability)

        return {
            "foods": food_summaries,
            "overall_meal": {
                "suitability": meal_suitability,
                "simple_reason": meal_simple_reason,
                "note": meal_note,
            },
        }

    # ── Public interface ───────────────────────────────────────────────────

    def evaluate(self, foods: List[FoodItem]) -> Dict:
        """
        Main evaluation entry point.

        Parameters
        ----------
        foods : list of FoodItem

        Returns
        -------
                dict with compact structure:
        {
                    "foods": [...],
                    "meal_analysis": {...},
                    "overall_meal": {
                            "suitability": "...",
                            "score": 0,
                            "rules": [...],
                            "reasons": [...],
                            "note": "..."
                    }
        }
        """
        assert len(foods) >= 1, "At least one food item required."

        # Layer 1 — individual food evaluation
        food_results = []
        adjusted_nutrients = []

        for food in foods:
            result = self._evaluate_food(food)
            food_results.append(result)
            adjusted_nutrients.append(
                self._normaliser.normalise(food.nutrients_per_100g, food.portion_g)
            )

        # Layer 2 — meal level (only for multiple foods, or always for completeness)
        meal_agg  = MealEvaluator.aggregate(adjusted_nutrients)
        meal_rules = MealEvaluator.evaluate(meal_agg, self.meal_targets)
        meal_label, meal_score = ScoringEngine.compute(meal_rules)

        # Override: single food → food suitability IS meal suitability
        if len(foods) == 1:
            meal_label  = Suitability(food_results[0]["suitability"])
            meal_note   = "Single food — food suitability equals meal suitability."
        else:
            meal_note   = f"Multi-food meal — {len(foods)} items evaluated collectively."

        meal_rules_compact = self._serialise_rules(meal_rules)
        meal_reasons = [r["reason"] for r in meal_rules_compact if not r["skipped"]]
        user_friendly = self._build_user_friendly_response(
            foods=food_results,
            meal_rules=meal_rules_compact,
            meal_suitability=meal_label.value,
            meal_note=meal_note,
        )

        return {
            "foods":         food_results,
            "meal_analysis": meal_agg,
            "overall_meal": {
                "suitability": meal_label.value,
                "score":       meal_score,
                "rules":       meal_rules_compact,
                "reasons":     meal_reasons,
                "note":        meal_note,
            },
            "user_friendly_response": user_friendly,
        }


# ---------------------------------------------------------------------------
# 10.  EXAMPLE DRIVER
# ---------------------------------------------------------------------------

def build_sample_patient() -> PatientProfile:
    return PatientProfile(
        age                         = 52,
        gender                      = "Male",
        height_cm                   = 170,
        weight_kg                   = 72,
        bmi                         = 28.4,
        bmi_class_label             = "Overweight",
        physical_activity_level     = PhysicalActivityLevel.LIGHT,
        steps_per_day               = 4500,
        sleep_hours                 = 6.5,
        diabetes_duration_years     = 7,
        hba1c_percent               = 8.3,          # poorly controlled
        fasting_glucose_mg_dl       = 148,
        postprandial_glucose_mg_dl  = 210,
        triglycerides_mg_dl         = 195,
        ldl_cholesterol_mg_dl       = 130,
        hdl_cholesterol_mg_dl       = 38,
        systolic_bp_mmhg            = 145,           # hypertensive
        diastolic_bp_mmhg           = 92,
        egfr_ml_min_1_73m2          = 55,
        ckd_stage_label             = CKDStage.G3,  # protein restriction
        smoking_status              = 1,
        alcohol_use                 = 1,
        primary_goal                = PrimaryGoal.GLYCEMIC_CONTROL,
    )


def build_sample_targets() -> MealMacroTargets:
    """Typical breakfast targets for a ~1600 kcal/day T2D patient."""
    return MealMacroTargets(
        calories_kcal   = 400,
        carbohydrates_g = 55,
        protein_g       = 18,
        fat_g           = 12,
        fiber_g         = 6,
    )


def build_sample_foods() -> List[FoodItem]:
    """
    South Indian breakfast — Idli + Sambar + Coconut Chutney.
    Several micronutrients intentionally set to None to demonstrate skip logic.
    """
    idli = FoodItem(
        food_name  = "Idli (steamed rice-lentil cake)",
        portion_g  = 120,                            # 2 medium idlis
        nutrients_per_100g = FoodNutrients(
            energy_kcal    = 116,
            carb_g         = 22.5,
            protein_g      = 3.9,
            fat_g          = 0.4,
            freesugar_g    = 0.0,
            fibre_g        = 0.8,
            sfa_mg         = 80,
            mufa_mg        = 120,
            pufa_mg        = 90,
            cholesterol_mg = 0,
            calcium_mg     = 18,
            phosphorus_mg  = 55,
            magnesium_mg   = 14,
            sodium_mg      = 260,
            potassium_mg   = 65,
            iron_mg        = 0.6,
            copper_mg      = None,                   # missing
            selenium_ug    = None,                   # missing
            chromium_mg    = None,                   # missing
            manganese_mg   = 0.3,
            molybdenum_mg  = None,                   # missing
            zinc_mg        = 0.5,
            vita_ug        = None,                   # missing
            vite_mg        = 0.1,
            vitd2_ug       = None,                   # missing
            vitd3_ug       = None,                   # missing
            vitk1_ug       = None,                   # missing
            vitk2_ug       = None,                   # missing
            folate_ug      = 18,
            vitb1_mg       = 0.08,
            vitb2_mg       = 0.04,
            vitb3_mg       = 0.7,
            vitb5_mg       = None,                   # missing
            vitb6_mg       = 0.06,
            vitb7_ug       = None,                   # missing
            vitb9_ug       = 18,
            vitc_mg        = 0,
            carotenoids_ug = 0,
        )
    )

    sambar = FoodItem(
        food_name  = "Sambar (lentil vegetable stew)",
        portion_g  = 150,
        nutrients_per_100g = FoodNutrients(
            energy_kcal    = 62,
            carb_g         = 8.2,
            protein_g      = 4.1,
            fat_g          = 1.3,
            freesugar_g    = 0.5,
            fibre_g        = 2.5,
            sfa_mg         = 310,
            mufa_mg        = 480,
            pufa_mg        = 390,
            cholesterol_mg = 0,
            calcium_mg     = 42,
            phosphorus_mg  = 80,
            magnesium_mg   = 28,
            sodium_mg      = 180,
            potassium_mg   = 220,
            iron_mg        = 1.8,
            copper_mg      = 0.12,
            selenium_ug    = 3,
            chromium_mg    = None,                   # missing
            manganese_mg   = 0.4,
            molybdenum_mg  = None,                   # missing
            zinc_mg        = 0.7,
            vita_ug        = 38,
            vite_mg        = 0.5,
            vitd2_ug       = None,                   # missing
            vitd3_ug       = None,                   # missing
            vitk1_ug       = 12,
            vitk2_ug       = None,                   # missing
            folate_ug      = 42,
            vitb1_mg       = 0.1,
            vitb2_mg       = 0.05,
            vitb3_mg       = 0.9,
            vitb5_mg       = 0.2,
            vitb6_mg       = 0.12,
            vitb7_ug       = 2,
            vitb9_ug       = 42,
            vitc_mg        = 8,
            carotenoids_ug = 420,
        )
    )

    chutney = FoodItem(
        food_name  = "Chutney (coconut-based condiment)",
        portion_g  = 50,
        nutrients_per_100g = FoodNutrients(
            energy_kcal    = 230,
            carb_g         = 6.5,
            protein_g      = 2.1,
            fat_g          = 41.0,
            freesugar_g    = 0.8,
            fibre_g        = 5.4,
            sfa_mg         = 18000,                  # coconut is high SFA
            mufa_mg        = 950,
            pufa_mg        = 480,
            cholesterol_mg = 0,
            calcium_mg     = 14,
            phosphorus_mg  = 90,
            magnesium_mg   = 32,
            sodium_mg      = 95,
            potassium_mg   = 356,
            iron_mg        = 1.0,
            copper_mg      = 0.28,
            selenium_ug    = None,                   # missing
            chromium_mg    = None,                   # missing
            manganese_mg   = 1.5,
            molybdenum_mg  = None,                   # missing
            zinc_mg        = 0.6,
            vita_ug        = None,                   # missing
            vite_mg        = 0.2,
            vitd2_ug       = None,                   # missing
            vitd3_ug       = None,                   # missing
            vitk1_ug       = None,                   # missing
            vitk2_ug       = None,                   # missing
            folate_ug      = 26,
            vitb1_mg       = 0.06,
            vitb2_mg       = None,                   # missing
            vitb3_mg       = 0.5,
            vitb5_mg       = None,                   # missing
            vitb6_mg       = 0.05,
            vitb7_ug       = None,                   # missing
            vitb9_ug       = 26,
            vitc_mg        = 2,
            carotenoids_ug = 0,
        )
    )

    return [idli, sambar, chutney]


def print_summary(result: Dict) -> None:
    """Pretty-print a condensed human-readable summary to stdout."""
    sep = "=" * 70
    print(f"\n{sep}")
    print("  T2D FOOD SUITABILITY REPORT")
    print(sep)

    print(f"\n{'─'*70}")
    print("  INDIVIDUAL FOOD EVALUATION (Layer 1)")
    print(f"{'─'*70}")
    for f in result["foods"]:
        icon = {"Suitable": "✓", "Moderate": "~", "Not Suitable": "✗"}.get(f["suitability"], "?")
        print(f"\n  [{icon}] {f['food_name']}  |  {f['portion_g']} g  |  "
              f"Score: {f['score']}  |  {f['suitability']}")
        for rule in f["rules"]:
            if rule["skipped"]:
                continue     # don't clutter output with skipped rules
            sym = {"Suitable": "+", "Moderate": "·", "Not Suitable": "!"}.get(rule["label"], " ")
            print(f"       [{sym}] {rule['rule']}: {rule['reason']}")

    print(f"\n{'─'*70}")
    print("  MEAL AGGREGATE (Layer 2)")
    print(f"{'─'*70}")
    ma = result["meal_analysis"]
    print(f"  Calories : {ma.get('total_calories', 'N/A')} kcal")
    print(f"  Carbs    : {ma.get('total_carbs', 'N/A')} g")
    print(f"  Protein  : {ma.get('total_protein', 'N/A')} g")
    print(f"  Fat      : {ma.get('total_fat', 'N/A')} g")
    print(f"  Fibre    : {ma.get('total_fiber', 'N/A')} g")
    print(f"  Na       : {ma.get('total_sodium', 'N/A')} mg")

    print(f"\n  Meal Evaluation Rules:")
    for rule in result["overall_meal"]["rules"]:
        sym = {"Suitable": "+", "Moderate": "·", "Not Suitable": "!"}.get(rule["label"], " ")
        print(f"    [{sym}] {rule['rule']}: {rule['reason']}")

    final = result["overall_meal"]["suitability"]
    icon  = {"Suitable": "✓ SUITABLE", "Moderate": "~ MODERATE", "Not Suitable": "✗ NOT SUITABLE"}.get(final, final)
    print(f"\n  OVERALL MEAL VERDICT:  {icon}  (score={result['overall_meal']['score']})")
    print(f"  Note: {result['overall_meal']['note']}")
    print(f"\n{sep}\n")


# ---------------------------------------------------------------------------
# 11.  ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    patient  = build_sample_patient()
    targets  = build_sample_targets()
    foods    = build_sample_foods()

    engine   = FoodSuitabilityEngine(patient, targets)
    result   = engine.evaluate(foods)

    # ── Human-readable summary ─────────────────────────────────────────────
    print_summary(result)

    # ── Full structured JSON output ────────────────────────────────────────
    print("\n--- FULL JSON OUTPUT ---\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))