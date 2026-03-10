import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from sklearn.neighbors import NearestNeighbors


# Base dirs for data files
BASE_DIR = Path(__file__).resolve().parents[2]  # backend/
DATA_DIR = BASE_DIR / "app" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


CONFIG: Dict = {
    # macro coverage targets for sequential method (fallback)
    "fiber_coverage_ratio": 0.50,
    "protein_coverage_ratio": 0.55,

    # tolerance: 85-115% of target is acceptable
    "macro_tolerance_low": 0.85,
    "macro_tolerance_high": 1.15,

    # quantity bounds (grams)
    "qty_min": 30,
    "qty_max": 250,
    "side_qty_min": 50,
    "side_qty_max": 80,

    # history / repetition
    "repetition_penalty_weight": 0.30,
    "recent_days_limit": 3,
    "unique_food_reset_ratio": 0.50,
    "history_reset_days": 7,

    # health thresholds
    "high_hba1c": 6.5,
    "high_triglycerides": 150,
    "high_ldl": 130,
    "high_bp_sys": 140,
    "high_bp_dia": 90,
    "gi_low": 55,

    # KNN
    "knn_neighbors": 5,

    # history file (under backend/app/data/)
    "history_file": str(DATA_DIR / "recommendation_history.csv"),
}


class RecommendationHistory:
    def __init__(self) -> None:
        self.file = CONFIG["history_file"]
        if os.path.exists(self.file) and os.path.getsize(self.file) > 0:
            try:
                self.history = pd.read_csv(self.file)
            except pd.errors.EmptyDataError:
                self.history = pd.DataFrame(
                    columns=["user_id", "food_id", "date", "feedback"]
                )
        else:
            self.history = pd.DataFrame(
                columns=["user_id", "food_id", "date", "feedback"]
            )
            self.history.to_csv(self.file, index=False)

    def save(self) -> None:
        self.history.to_csv(self.file, index=False)

    def reset_if_needed(self, user_id: str, total_foods: int) -> None:
        user_history = self.history[self.history["user_id"] == user_id]
        if len(user_history) == 0:
            return

        user_history = user_history.copy()
        user_history["date"] = pd.to_datetime(user_history["date"])
        last_date = user_history["date"].max()

        if (datetime.now() - last_date).days >= CONFIG["history_reset_days"]:
            self.history = self.history[self.history["user_id"] != user_id]
            self.save()
            return

        unique_foods = user_history["food_id"].nunique()
        if unique_foods > total_foods * CONFIG["unique_food_reset_ratio"]:
            self.history = self.history[self.history["user_id"] != user_id]
            self.save()

    def add(self, user_id: str, food_id: int, feedback: str = "shown") -> None:
        new_row = pd.DataFrame(
            [
                {
                    "user_id": user_id,
                    "food_id": food_id,
                    "date": datetime.now(),
                    "feedback": feedback,
                }
            ]
        )
        self.history = pd.concat([self.history, new_row], ignore_index=True)
        self.save()

    def get_penalty(self, user_id: str, food_id: int) -> float:
        df = self.history[
            (self.history["user_id"] == user_id)
            & (self.history["food_id"] == food_id)
        ]
        if df.empty:
            return 0.0

        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        penalty = len(df) * CONFIG["repetition_penalty_weight"]

        last_date = df["date"].max()
        if (datetime.now() - last_date).days <= CONFIG["recent_days_limit"]:
            penalty += 0.5

        dislike_penalty = len(df[df["feedback"] == "dislike"]) * 2.0
        like_bonus = len(df[df["feedback"] == "like"]) * -0.3

        return float(penalty + dislike_penalty + like_bonus)


class FoodRecommender:
    def __init__(self, food_df: pd.DataFrame) -> None:
        self.food_df = food_df
        self.history = RecommendationHistory()

    # =====================================================
    # HEALTH FILTERING
    # =====================================================

    def filter_foods(self, user: Dict) -> pd.DataFrame:
        df = self.food_df.copy()

        if user["veg_only"]:
            df = df[df["is_veg"] == 1]

        meal = user["meal_type"]
        # handle "snacks" -> column is "is_snack"
        col = f"is_{meal}" if f"is_{meal}" in df.columns else f"is_{meal.rstrip('s')}"
        if col in df.columns:
            df = df[df[col] == 1]

        if user["hba1c_percent"] >= CONFIG["high_hba1c"]:
            df = df[df["glycemic_index"] <= CONFIG["gi_low"]]

        if user["triglycerides_mg_dl"] >= CONFIG["high_triglycerides"]:
            df = df[df["is_high_saturated_fat"] == 0]

        if user["ldl_cholesterol_mg_dl"] >= CONFIG["high_ldl"]:
            df = df[df["is_high_saturated_fat"] == 0]

        if (
            user["systolic_bp_mmHg"] >= CONFIG["high_bp_sys"]
            or user["diastolic_bp_mmHg"] >= CONFIG["high_bp_dia"]
        ):
            df = df[df["is_high_sodium"] == 0]

        return df

    # =====================================================
    # KNN-BASED FOOD SELECTION
    # =====================================================

    def select_food_knn(
        self,
        df: pd.DataFrame,
        macro_type: str,
        user_id: str,
        ideal_vector: List[float],
    ):
        """
        Use KNN to find the food whose macro profile is closest
        to the ideal_vector = [carb, protein, fiber, fat] per 100g.
        Then apply history penalty to re-rank top-K candidates.
        """
        foods = df[df["macro_type"] == macro_type].copy()

        if len(foods) == 0:
            return None

        features = foods[["carb_g", "protein_g", "fiber_g", "fat_g"]].values

        k = min(CONFIG["knn_neighbors"], len(foods))
        knn = NearestNeighbors(n_neighbors=k, metric="euclidean")
        knn.fit(features)

        ideal = np.array(ideal_vector).reshape(1, -1)
        distances, indices = knn.kneighbors(ideal)

        candidates = foods.iloc[indices[0]].copy()
        candidates["knn_dist"] = distances[0]

        candidates["penalty"] = candidates["food_id"].apply(
            lambda fid: self.history.get_penalty(user_id, fid)
        )

        # combined score: lower is better
        candidates["score"] = candidates["knn_dist"] + candidates["penalty"] * 5.0
        candidates = candidates.sort_values("score")

        return candidates.iloc[0]

    # =====================================================
    # MACRO VECTOR PER GRAM
    # =====================================================

    def macro_per_gram(self, food: pd.Series) -> np.ndarray:
        return np.array(
            [
                food["carb_g"] / 100.0,
                food["protein_g"] / 100.0,
                food["fiber_g"] / 100.0,
                food["fat_g"] / 100.0,
            ]
        )

    # =====================================================
    # LINEAR PROGRAMMING QUANTITY OPTIMIZER
    # =====================================================

    def solve_quantities_lp(
        self, foods: List[pd.Series], targets: Dict[str, float]
    ) -> np.ndarray:
        """
        Minimize total macro error using Linear Programming.
        """
        n = len(foods)
        m = 4  # carb, protein, fiber, fat

        target_vec = np.array(
            [
                targets["carb"],
                targets["protein"],
                targets["fiber"],
                targets["fat"],
            ],
            dtype=float,
        )

        # build macro matrix: A[macro][food] = macro_per_gram
        A_macro = np.zeros((m, n))
        for j, food in enumerate(foods):
            A_macro[:, j] = self.macro_per_gram(food)

        # decision vars: [qty_0..qty_n-1, slack_pos_0..3, slack_neg_0..3]
        num_vars = n + 2 * m

        # objective: minimize sum of slack vars (weighted)
        weights = np.array([1.5, 1.5, 1.0, 1.0])
        c = np.zeros(num_vars)
        for i in range(m):
            c[n + i] = weights[i]  # slack_pos
            c[n + m + i] = weights[i]  # slack_neg

        # equality constraints: A_macro @ qty + slack_pos - slack_neg = target
        A_eq = np.zeros((m, num_vars))
        b_eq = np.zeros(m)

        for i in range(m):
            for j in range(n):
                A_eq[i, j] = A_macro[i, j]
            A_eq[i, n + i] = 1.0  # slack_pos
            A_eq[i, n + m + i] = -1.0  # slack_neg
            b_eq[i] = target_vec[i]

        # bounds
        bounds = []
        for _ in range(n):
            bounds.append((CONFIG["qty_min"], CONFIG["qty_max"]))
        for _ in range(2 * m):
            bounds.append((0, None))  # slacks >= 0

        try:
            result = linprog(
                c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs"
            )

            if result.success:
                quantities = result.x[:n]
                return np.clip(quantities, CONFIG["qty_min"], CONFIG["qty_max"])
        except Exception:
            pass

        # fallback to lstsq
        return self.solve_quantities_fallback(foods, targets)

    # =====================================================
    # FALLBACK: LEAST SQUARES SOLVER
    # =====================================================

    def solve_quantities_fallback(
        self, foods: List[pd.Series], targets: Dict[str, float]
    ) -> np.ndarray:
        A = np.array([self.macro_per_gram(f) for f in foods]).T

        b = np.array(
            [
                targets["carb"],
                targets["protein"],
                targets["fiber"],
                targets["fat"],
            ]
        )

        try:
            qty = np.linalg.lstsq(A, b, rcond=None)[0]
        except Exception:
            qty = np.ones(len(foods)) * 100.0

        return np.clip(qty, CONFIG["qty_min"], CONFIG["qty_max"])

    # =====================================================
    # SEQUENTIAL QUANTITY ESTIMATION (SAFETY CAPPED)
    # =====================================================

    def solve_quantities_sequential(
        self, foods: List[pd.Series], targets: Dict[str, float]
    ) -> np.ndarray:
        """
        Step-by-step quantity computation with macro subtraction
        and overflow protection. Used as a secondary fallback
        and to validate LP results.
        """
        remaining = {
            "carb": targets["carb"],
            "protein": targets["protein"],
            "fiber": targets["fiber"],
            "fat": targets["fat"],
        }

        quantities: List[float] = []
        macro_keys = ["carb", "protein", "fiber", "fat"]
        primary_macro = {
            "fiber": "fiber",
            "protein": "protein",
            "carb": "carb",
        }

        for food in foods:
            mtype = food.get("macro_type", "carb")
            pmacro = primary_macro.get(mtype, "carb")

            macro_col = f"{pmacro}_g"
            per100 = food[macro_col]

            if per100 <= 0:
                quantities.append(CONFIG["qty_min"])
                continue

            # compute quantity from primary macro
            target_val = remaining[pmacro]
            if mtype in ["fiber", "protein"]:
                target_val *= CONFIG.get(f"{pmacro}_coverage_ratio", 0.55)

            qty = (target_val / per100) * 100.0

            # check all macros don't overflow
            per_gram = self.macro_per_gram(food)
            for idx, key in enumerate(macro_keys):
                if per_gram[idx] > 0 and remaining[key] > 0:
                    max_qty = remaining[key] / per_gram[idx]
                    qty = min(qty, max_qty)

            qty = float(np.clip(qty, CONFIG["qty_min"], CONFIG["qty_max"]))
            quantities.append(qty)

            # subtract contributed macros
            for idx, key in enumerate(macro_keys):
                remaining[key] -= per_gram[idx] * qty
                remaining[key] = max(remaining[key], 0)

        return np.array(quantities)

    # =====================================================
    # VALIDATE QUANTITIES (overflow check)
    # =====================================================

    def validate_and_fix(
        self, foods: List[pd.Series], quantities: np.ndarray, targets: Dict[str, float]
    ) -> np.ndarray:
        """
        After computing quantities, verify no macro exceeds 115% of target.
        If it does, scale down proportionally.
        """
        target_vec = np.array(
            [
                targets["carb"],
                targets["protein"],
                targets["fiber"],
                targets["fat"],
            ]
        )

        # compute actual macros
        actual = np.zeros(4)
        for i, food in enumerate(foods):
            actual += self.macro_per_gram(food) * quantities[i]

        # check overflow
        for idx in range(4):
            if target_vec[idx] > 0:
                ratio = actual[idx] / target_vec[idx]
                if ratio > CONFIG["macro_tolerance_high"]:
                    # scale down ALL quantities proportionally
                    scale = CONFIG["macro_tolerance_high"] / ratio
                    quantities = quantities * scale

        quantities = np.clip(quantities, CONFIG["qty_min"], CONFIG["qty_max"])
        return quantities

    # =====================================================
    # SNACK RECOMMENDATION
    # =====================================================

    def recommend_snack(
        self, df: pd.DataFrame, user_id: str, targets: Dict[str, float]
    ) -> List[Tuple[str, float, str, int]]:
        target_vec = np.array(
            [
                targets["carb"],
                targets["protein"],
                targets["fiber"],
                targets["fat"],
            ]
        )

        # use KNN to find best snack food
        k = min(10, len(df))
        features = df[["carb_g", "protein_g", "fiber_g", "fat_g"]].values

        knn = NearestNeighbors(n_neighbors=k, metric="euclidean")
        knn.fit(features)

        # ideal snack profile = target macros scaled to per-100g assuming ~100g serving
        ideal = target_vec.reshape(1, -1)
        distances, indices = knn.kneighbors(ideal)

        candidates = df.iloc[indices[0]].copy()
        candidates["knn_dist"] = distances[0]
        candidates["penalty"] = candidates["food_id"].apply(
            lambda fid: self.history.get_penalty(user_id, fid)
        )
        candidates["score"] = candidates["knn_dist"] + candidates["penalty"] * 5.0
        candidates = candidates.sort_values("score")

        best_food = candidates.iloc[0]

        # compute optimal quantity
        macro = self.macro_per_gram(best_food)
        denom = float(np.dot(macro, macro))

        if denom > 0:
            qty = float(np.dot(target_vec, macro) / denom)
        else:
            qty = 100.0

        # cap each macro individually
        for idx, key in enumerate(["carb", "protein", "fiber", "fat"]):
            if macro[idx] > 0 and targets[key] > 0:
                max_qty = (targets[key] * CONFIG["macro_tolerance_high"]) / macro[idx]
                qty = min(qty, float(max_qty))

        qty = float(np.clip(qty, CONFIG["qty_min"], CONFIG["qty_max"]))

        return [
            (
                best_food["food_name"],
                round(qty, 1),
                best_food["serving_unit"],
                int(best_food["food_id"]),
            )
        ]

    # =====================================================
    # MAIN RECOMMEND
    # =====================================================

    def recommend(self, user_id: str, user: Dict) -> List[Tuple[str, float, str, int]]:
        df = self.filter_foods(user)

        if len(df) == 0:
            return []

        self.history.reset_if_needed(user_id, len(self.food_df))

        targets = {
            "carb": user["target_carbs_g"],
            "protein": user["target_protein_g"],
            "fiber": user["target_fiber_g"],
            "fat": user["target_fat_g"],
        }

        # ------ SNACK ------
        if user["meal_type"] in ["snack", "snacks"]:
            return self.recommend_snack(df, user_id, targets)

        # ------ IDEAL VECTORS FOR KNN (per 100g) ------
        fiber_ideal = [5, 3, 8, 2]  # low carb, low protein, high fiber, low fat
        protein_ideal = [5, 15, 3, 5]  # low carb, high protein, moderate fiber/fat
        carb_ideal = [25, 3, 2, 2]  # high carb, low protein, low fiber, low fat

        # ------ SELECT FOODS VIA KNN ------
        fiber_food = self.select_food_knn(df, "fiber", user_id, fiber_ideal)
        protein_food = self.select_food_knn(df, "protein", user_id, protein_ideal)
        carb_food = self.select_food_knn(df, "carb", user_id, carb_ideal)

        # side dish
        side_df = df[df["is_side"] == 1]
        side_food = None
        if len(side_df) > 0:
            side_df = side_df.copy()
            side_df["penalty"] = side_df["food_id"].apply(
                lambda fid: self.history.get_penalty(user_id, fid)
            )
            side_df = side_df.sort_values("penalty")
            side_food = side_df.iloc[0]

        foods: List[pd.Series] = []
        food_labels: List[str] = []

        if fiber_food is not None:
            foods.append(fiber_food)
            food_labels.append("fiber")
        if protein_food is not None:
            foods.append(protein_food)
            food_labels.append("protein")
        if carb_food is not None:
            foods.append(carb_food)
            food_labels.append("carb")

        if len(foods) == 0:
            return []

        # ------ SOLVE QUANTITIES (LP primary, sequential validation) ------
        quantities_lp = self.solve_quantities_lp(foods, targets)

        # validate and fix overflow
        quantities_lp = self.validate_and_fix(foods, quantities_lp, targets)

        # also compute sequential for comparison
        quantities_seq = self.solve_quantities_sequential(foods, targets)
        quantities_seq = self.validate_and_fix(foods, quantities_seq, targets)

        # pick the solution with lower total macro error
        def total_error(qtys: np.ndarray) -> float:
            actual = np.zeros(4)
            for i, food in enumerate(foods):
                actual += self.macro_per_gram(food) * qtys[i]
            target_arr = np.array(
                [
                    targets["carb"],
                    targets["protein"],
                    targets["fiber"],
                    targets["fat"],
                ]
            )
            # weighted error
            weights = np.array([1.5, 1.5, 1.0, 1.0])
            return float(np.sum(weights * np.abs(actual - target_arr)))

        err_lp = total_error(quantities_lp)
        err_seq = total_error(quantities_seq)

        quantities = quantities_lp if err_lp <= err_seq else quantities_seq

        # ------ BUILD RESULT ------
        result: List[Tuple[str, float, str, int]] = []
        actual_macros = np.zeros(4)

        for i, food in enumerate(foods):
            qty = float(round(float(quantities[i]), 1))
            result.append(
                (
                    food["food_name"],
                    qty,
                    food["serving_unit"],
                    int(food["food_id"]),
                )
            )
            actual_macros += self.macro_per_gram(food) * quantities[i]

        # ------ ADD SIDE DISH IF MACRO GAPS REMAIN ------
        if side_food is not None:
            target_arr = np.array(
                [
                    targets["carb"],
                    targets["protein"],
                    targets["fiber"],
                    targets["fat"],
                ]
            )
            gap = target_arr - actual_macros

            if np.any(gap > 1.0):  # at least 1g gap in some macro
                side_macro = self.macro_per_gram(side_food)
                denom = float(np.dot(side_macro, side_macro))

                if denom > 0:
                    side_qty = float(np.dot(gap, side_macro) / denom)
                else:
                    side_qty = 50.0

                # cap side dish so it doesn't overshoot
                for idx in range(4):
                    if side_macro[idx] > 0 and gap[idx] > 0:
                        max_side = gap[idx] / side_macro[idx]
                        side_qty = min(side_qty, float(max_side))

                side_qty = float(
                    np.clip(
                        side_qty,
                        CONFIG["side_qty_min"],
                        CONFIG["side_qty_max"],
                    )
                )

                result.append(
                    (
                        side_food["food_name"],
                        round(side_qty, 1),
                        side_food["serving_unit"],
                        int(side_food["food_id"]),
                    )
                )

        return result

    # =====================================================
    # FEEDBACK
    # =====================================================

    def feedback(self, user_id: str, food_id: int, action: str) -> None:
        action = action.lower()
        if action not in ["like", "dislike", "skip"]:
            return
        self.history.add(user_id, food_id, action)


def compare_macros(
    recommended_foods: List[Tuple[str, float, str, int]],
    food_df: pd.DataFrame,
    user: Dict,
) -> Dict[str, Dict[str, float]]:
    """
    Utility used for debugging / analysis.
    Returns target vs actual macro comparison.
    """
    totals = {
        "carb": 0.0,
        "protein": 0.0,
        "fiber": 0.0,
        "fat": 0.0,
        "calories": 0.0,
    }

    for _, qty, _, food_id in recommended_foods:
        row = food_df[food_df["food_id"] == food_id].iloc[0]
        factor = qty / 100.0
        totals["carb"] += float(row["carb_g"] * factor)
        totals["protein"] += float(row["protein_g"] * factor)
        totals["fiber"] += float(row["fiber_g"] * factor)
        totals["fat"] += float(row["fat_g"] * factor)
        totals["calories"] += float(row["energy_kcal"] * factor)

    comparison = {
        "carb": {
            "target": float(user["target_carbs_g"]),
            "actual": totals["carb"],
        },
        "protein": {
            "target": float(user["target_protein_g"]),
            "actual": totals["protein"],
        },
        "fiber": {
            "target": float(user["target_fiber_g"]),
            "actual": totals["fiber"],
        },
        "fat": {
            "target": float(user["target_fat_g"]),
            "actual": totals["fat"],
        },
        "calories": {
            "target": float(user["target_calories_kcal"]),
            "actual": totals["calories"],
        },
    }

    return comparison

