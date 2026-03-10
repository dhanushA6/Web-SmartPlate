import { useEffect, useMemo, useState } from "react";
import { getProfile } from "../api/apiClient";
import { getFoodRecommendation, sendFoodFeedback } from "../services/recommendationApi";

const MEAL_OPTIONS = [
  { value: "breakfast", label: "Breakfast" },
  { value: "lunch", label: "Lunch" },
  { value: "snacks", label: "Snacks" },
  { value: "dinner", label: "Dinner" },
];

export default function FoodRecommendation({ nutrition }) {
  const userId = localStorage.getItem("userId");

  const [mealType, setMealType] = useState("breakfast");
  const [vegOnly, setVegOnly] = useState(null);
  const [dietLabel, setDietLabel] = useState("");
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [foods, setFoods] = useState([]);
  const [feedbackStatus, setFeedbackStatus] = useState({});
  const [feedbackLoading, setFeedbackLoading] = useState({});

  useEffect(() => {
    const fetchProfile = async () => {
      if (!userId) return;
      try {
        const { data } = await getProfile(userId);
        setProfile(data);
        if (data.dietary_preference === "Non-Vegetarian") {
          setVegOnly(false);
          setDietLabel("Non-Vegetarian");
        } else if (data.dietary_preference === "Vegetarian") {
          setVegOnly(true);
          setDietLabel("Vegetarian");
        } else {
          setVegOnly(null);
          setDietLabel("");
        }
      } catch {
        // silent failure; user can still request with defaults
      }
    };
    fetchProfile();
  }, [userId]);

  const mealTargets = useMemo(() => {
    if (!nutrition || !nutrition.meal_splits) return null;
    const split = nutrition.meal_splits[mealType];
    if (!split) return null;
    return {
      carbs: split.daily_carbohydrates_g,
      protein: split.daily_protein_g,
      fat: split.daily_fat_g,
      fiber: split.daily_fiber_g,
      calories: split.daily_calories_kcal,
    };
  }, [nutrition, mealType]);

  const handleGenerate = async () => {
    if (!userId) {
      setError("You need to be logged in to generate a meal plan.");
      return;
    }

    setError("");
    setFoods([]);

    if (!mealTargets) {
      setError("Macro targets for this meal are not available. Please run nutrition prediction first.");
      return;
    }

    if (!profile) {
      setError("Profile data is not loaded. Please complete and save your medical profile.");
      return;
    }

    const payload = {
      user_id: userId,
      meal_type: mealType,
      veg_only: !!vegOnly,
      target_carbs_g: mealTargets.carbs,
      target_protein_g: mealTargets.protein,
      target_fiber_g: mealTargets.fiber,
      target_fat_g: mealTargets.fat,
      target_calories_kcal: mealTargets.calories,
      hba1c_percent: Number(profile.hba1c_percent) || 0,
      triglycerides_mg_dl: Number(profile.triglycerides_mg_dl) || 0,
      ldl_cholesterol_mg_dl: Number(profile.ldl_cholesterol_mg_dl) || 0,
      systolic_bp_mmHg: Number(profile.systolic_bp_mmHg) || 0,
      diastolic_bp_mmHg: Number(profile.diastolic_bp_mmHg) || 0,
    };

    setLoading(true);
    try {
      const { data } = await getFoodRecommendation(payload);
      setFoods(data.foods || []);
      setFeedbackStatus({});
      setFeedbackLoading({});
      if (!data.foods || data.foods.length === 0) {
        setError("No suitable foods found for the given criteria.");
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Failed to generate food recommendation. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (foodId, action) => {
    if (!userId) {
      setError("You need to be logged in to send feedback.");
      return;
    }
    if (feedbackStatus[foodId]) {
      return;
    }

    setFeedbackLoading((prev) => ({ ...prev, [foodId]: true }));
    setError("");
    try {
      await sendFoodFeedback({
        user_id: userId,
        food_id: foodId,
        action,
      });
      setFeedbackStatus((prev) => ({ ...prev, [foodId]: action }));
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Failed to send feedback. Please try again."
      );
    } finally {
      setFeedbackLoading((prev) => ({ ...prev, [foodId]: false }));
    }
  };

  if (!nutrition) {
    return null;
  }

  return (
    <section className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-xl font-semibold text-slate-900">Food Recommendation</h1>
        <p className="text-sm text-slate-500">
          Personalized diabetic-friendly meals based on your macro targets and medical profile.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1.2fr)]">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-4">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Meal plan controls
            </p>
            <p className="text-sm text-slate-600">
              Choose a meal and generate a tailored plate plan.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] items-end">
            <div className="space-y-1">
              <label className="label text-xs sm:text-sm">Meal</label>
              <select
                className="input-field"
                value={mealType}
                onChange={(e) => setMealType(e.target.value)}
              >
                {MEAL_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <p className="label text-xs sm:text-sm">Diet type</p>
              <div className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-700">
                <span className="mr-1 h-2 w-2 rounded-full bg-emerald-500" />
                {dietLabel || "Not specified in profile"}
              </div>
            </div>

            <button
              type="button"
              className="primary-btn text-xs sm:text-sm h-9 sm:h-10"
              onClick={handleGenerate}
              disabled={loading}
            >
              {loading ? "Generating Meal Plan..." : "Generate Meal Plan"}
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Target macros for this meal
          </p>
          {mealTargets ? (
            <div className="grid gap-3 text-xs text-slate-600 sm:grid-cols-5">
              <MacroBadge label="Calories" value={mealTargets.calories} unit="kcal" />
              <MacroBadge label="Carbs" value={mealTargets.carbs} unit="g" />
              <MacroBadge label="Protein" value={mealTargets.protein} unit="g" />
              <MacroBadge label="Fat" value={mealTargets.fat} unit="g" />
              <MacroBadge label="Fiber" value={mealTargets.fiber} unit="g" />
            </div>
          ) : (
            <p className="text-xs text-slate-500">
              Macro targets are not available. Please run nutrition prediction first on the Nutrition page.
            </p>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {error && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 border border-red-200">
            {error}
          </div>
        )}

        {foods.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {foods.map((food, idx) => (
              <FoodCard
                key={`${food.food_id}-${idx}`}
                food={food}
                status={feedbackStatus[food.food_id]}
                loading={!!feedbackLoading[food.food_id]}
                onFeedback={(action) => handleFeedback(food.food_id, action)}
              />
            ))}
          </div>
        )}

        {!loading && !error && foods.length === 0 && (
          <p className="text-sm text-slate-500">
            Select a meal and generate a plan to see recommended foods.
          </p>
        )}
      </div>
    </section>
  );
}

function MacroBadge({ label, value, unit }) {
  if (value == null) return null;
  return (
    <div className="inline-flex items-center justify-between rounded-full bg-slate-50 px-3 py-1 border border-slate-100">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-xs font-semibold text-slate-800">
        {value.toFixed ? value.toFixed(1) : value} {unit}
      </span>
    </div>
  );
}

function FoodCard({ food, status, loading, onFeedback }) {
  const { food_name, quantity_g, unit, nutrition } = food;
  const disabled = !!status || loading;

  const renderStatus = () => {
    if (!status) return null;
    if (status === "like") return "👍 Liked";
    if (status === "dislike") return "👎 Disliked";
    if (status === "skip") return "⏭ Skipped";
    return null;
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm flex flex-col h-full">
      <div>
        <h3 className="text-sm font-semibold text-slate-900">{food_name}</h3>
        <p className="mt-1 text-xs text-slate-600">
          {quantity_g?.toFixed ? quantity_g.toFixed(1) : quantity_g} g ({unit})
        </p>

        <div className="mt-3 grid gap-2 text-xs text-slate-700 sm:grid-cols-2">
          <p>
            <span className="font-semibold">Carbs:</span>{" "}
            {nutrition.carbs?.toFixed ? nutrition.carbs.toFixed(1) : nutrition.carbs} g
          </p>
          <p>
            <span className="font-semibold">Protein:</span>{" "}
            {nutrition.protein?.toFixed ? nutrition.protein.toFixed(1) : nutrition.protein} g
          </p>
          <p>
            <span className="font-semibold">Fiber:</span>{" "}
            {nutrition.fiber?.toFixed ? nutrition.fiber.toFixed(1) : nutrition.fiber} g
          </p>
          <p>
            <span className="font-semibold">Fat:</span>{" "}
            {nutrition.fat?.toFixed ? nutrition.fat.toFixed(1) : nutrition.fat} g
          </p>
          <p className="sm:col-span-2">
            <span className="font-semibold">Calories:</span>{" "}
            {nutrition.calories?.toFixed
              ? nutrition.calories.toFixed(1)
              : nutrition.calories}{" "}
            kcal
          </p>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-2">
        <div className="flex gap-2">
          <button
            type="button"
            className="px-3 py-1 rounded-full border border-slate-200 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={disabled}
            onClick={() => onFeedback("like")}
          >
            👍 Like
          </button>
          <button
            type="button"
            className="px-3 py-1 rounded-full border border-slate-200 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={disabled}
            onClick={() => onFeedback("dislike")}
          >
            👎 Dislike
          </button>
          <button
            type="button"
            className="px-3 py-1 rounded-full border border-slate-200 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={disabled}
            onClick={() => onFeedback("skip")}
          >
            ⏭ Skip
          </button>
        </div>
        {renderStatus() && (
          <span className="text-xs font-medium text-slate-600">
            {renderStatus()}
          </span>
        )}
      </div>
    </div>
  );
}

