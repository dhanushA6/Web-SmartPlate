import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { predictNutrition } from "../api/apiClient";
import { DailyMacroPieChart, MealDistributionPieChart, MealMacroBarChart } from "../components/MacroChart";

export default function Nutrition() {
  const navigate = useNavigate();
  const userId = localStorage.getItem("userId");
  const storageKey = userId ? `nutritionPrediction:${userId}` : "nutritionPrediction";

  const [nutrition, setNutrition] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!userId) {
      navigate("/login");
      return;
    }

    const saved = localStorage.getItem(storageKey);
    if (saved) {
      setNutrition(JSON.parse(saved));
    }
  }, [userId, navigate, storageKey]);

  const handlePredict = async () => {
    if (!userId) return;

    setLoading(true);
    setError("");

    try {
      const { data } = await predictNutrition(userId);

      setNutrition(data);
      localStorage.setItem(storageKey, JSON.stringify(data));
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to predict nutrition");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setNutrition(null);
    localStorage.removeItem(storageKey);
  };

  return (
    <div className="layout-main space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-slate-900">
            Nutrition
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Personalized daily macronutrient requirement prediction
          </p>
        </div>

        <div className="flex gap-3 flex-shrink-0">
          <button
            className="secondary-btn"
            onClick={handleRefresh}
          >
            Clear
          </button>
          <button
            className="primary-btn min-w-[140px]"
            onClick={handlePredict}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Predicting...
              </>
            ) : (
              "Predict Nutrition"
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 border border-red-100">
          {error}
        </div>
      )}

      {nutrition && (
        <>
          <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
            <StatCard label="Calories" value={nutrition.daily.daily_calories_kcal} unit="kcal" />
            <StatCard label="Carbohydrates" value={nutrition.daily.daily_carbohydrates_g} unit="g" color="text-nutrition-carbs" />
            <StatCard label="Protein" value={nutrition.daily.daily_protein_g} unit="g" color="text-nutrition-protein" />
            <StatCard label="Fat" value={nutrition.daily.daily_fat_g} unit="g" color="text-nutrition-fat" />
            <StatCard label="Fiber" value={nutrition.daily.daily_fiber_g} unit="g" color="text-nutrition-fiber" />
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <DailyMacroPieChart daily={nutrition.daily} />
            <MealDistributionPieChart distribution={nutrition.distribution} />
          </section>

          <section>
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Meal-wise macro split</h2>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {Object.entries(nutrition.meal_splits).map(([meal, vals]) => (
                <div
                  key={meal}
                  className="card p-4 flex flex-col"
                >
                  <h3 className="text-sm font-semibold text-slate-800 capitalize mb-3 pb-2 border-b border-slate-100">
                    {meal}
                  </h3>
                  <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-slate-600 mb-3">
                    <span>Calories</span>
                    <span className="font-semibold text-slate-900 text-right">{vals.daily_calories_kcal?.toFixed(0) ?? "—"} kcal</span>
                    <span className="text-[#F97316]">Carbs</span>
                    <span className="font-semibold text-slate-900 text-right">{vals.daily_carbohydrates_g?.toFixed(1) ?? "—"} g</span>
                    <span className="text-[#3B82F6]">Protein</span>
                    <span className="font-semibold text-slate-900 text-right">{vals.daily_protein_g?.toFixed(1) ?? "—"} g</span>
                    <span className="text-[#A855F7]">Fat</span>
                    <span className="font-semibold text-slate-900 text-right">{vals.daily_fat_g?.toFixed(1) ?? "—"} g</span>
                    <span className="text-[#22C55E]">Fiber</span>
                    <span className="font-semibold text-slate-900 text-right">{vals.daily_fiber_g?.toFixed(1) ?? "—"} g</span>
                  </div>
                  <div className="mt-auto min-h-[120px]">
                    <MealMacroBarChart mealName={meal} values={vals} />
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value, unit, color = "text-slate-900" }) {
  return (
    <div className="card p-4">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
      <p className={`mt-1 text-lg sm:text-xl font-semibold ${color}`}>
        {value != null ? Number(value).toFixed(1) : "—"} {unit}
      </p>
    </div>
  );
}