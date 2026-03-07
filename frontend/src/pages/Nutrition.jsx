import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { predictNutrition } from "../api/apiClient";
import { DailyMacroPieChart, MealDistributionPieChart } from "../components/MacroChart";

export default function Nutrition() {
  const navigate = useNavigate();
  const userId = localStorage.getItem("userId");

  const [nutrition, setNutrition] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!userId) {
      navigate("/login");
      return;
    }

    const saved = localStorage.getItem("nutritionPrediction");
    if (saved) {
      setNutrition(JSON.parse(saved));
    }
  }, [userId, navigate]);

  const handlePredict = async () => {
    if (!userId) return;

    setLoading(true);
    setError("");

    try {
      const { data } = await predictNutrition(userId);

      setNutrition(data);
      localStorage.setItem("nutritionPrediction", JSON.stringify(data));
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to predict nutrition");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setNutrition(null);
    localStorage.removeItem("nutritionPrediction");
  };

  return (
    <div className="layout-main space-y-6">

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">
            Nutrition Dashboard
          </h1>
          <p className="text-sm text-slate-500">
            Personalized daily macronutrient requirement prediction
          </p>
        </div>

        <div className="flex gap-3">
          <button
            className="secondary-btn"
            onClick={handleRefresh}
          >
            Clear
          </button>

          <button
            className="primary-btn"
            onClick={handlePredict}
            disabled={loading}
          >
            {loading ? "Predicting..." : "Predict Nutrition"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 border border-red-100">
          {error}
        </div>
      )}

      {nutrition && (
        <>
          <section className="grid gap-4 md:grid-cols-5">
            <StatCard label="Calories" value={nutrition.daily.daily_calories_kcal} unit="kcal" />
            <StatCard label="Carbohydrates" value={nutrition.daily.daily_carbohydrates_g} unit="g" />
            <StatCard label="Protein" value={nutrition.daily.daily_protein_g} unit="g" />
            <StatCard label="Fat" value={nutrition.daily.daily_fat_g} unit="g" />
            <StatCard label="Fiber" value={nutrition.daily.daily_fiber_g} unit="g" />
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <DailyMacroPieChart daily={nutrition.daily} />
            <MealDistributionPieChart distribution={nutrition.distribution} />
          </section>

          <section className="card">
            <div className="card-header">
              <h2 className="card-title">Meal-wise macro split</h2>
            </div>

            <div className="card-body overflow-x-auto">
              <table className="min-w-full text-sm">

                <thead className="bg-slate-50">
                  <tr>
                    <Th>Meal</Th>
                    <Th>Calories</Th>
                    <Th>Carbohydrates</Th>
                    <Th>Protein</Th>
                    <Th>Fat</Th>
                    <Th>Fiber</Th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100">
                  {Object.entries(nutrition.meal_splits).map(([meal, vals]) => (
                    <tr key={meal} className="hover:bg-slate-50">

                      <Td className="font-medium">
                        {meal.charAt(0).toUpperCase() + meal.slice(1)}
                      </Td>

                      <Td>{vals.daily_calories_kcal?.toFixed(1)}</Td>
                      <Td>{vals.daily_carbohydrates_g?.toFixed(1)}</Td>
                      <Td>{vals.daily_protein_g?.toFixed(1)}</Td>
                      <Td>{vals.daily_fat_g?.toFixed(1)}</Td>
                      <Td>{vals.daily_fiber_g?.toFixed(1)}</Td>

                    </tr>
                  ))}
                </tbody>

              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value, unit }) {
  return (
    <div className="card">
      <div className="card-body">
        <p className="text-xs text-slate-500">{label}</p>
        <p className="mt-1 text-lg font-semibold text-slate-900">
          {value ? value.toFixed(1) : "--"} {unit}
        </p>
      </div>
    </div>
  );
}

function Th({ children }) {
  return (
    <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
      {children}
    </th>
  );
}

function Td({ children, className = "" }) {
  return (
    <td className={`px-3 py-2 text-sm text-slate-800 ${className}`.trim()}>
      {children}
    </td>
  );
}