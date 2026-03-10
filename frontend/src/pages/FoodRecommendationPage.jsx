import { useEffect, useState } from "react";
import FoodRecommendation from "../components/FoodRecommendation";

export default function FoodRecommendationPage() {
  const [nutrition, setNutrition] = useState(null);

  useEffect(() => {
    const saved = localStorage.getItem("nutritionPrediction");
    if (saved) {
      setNutrition(JSON.parse(saved));
    }
  }, []);

  return (
    <main className="layout-main space-y-6">
      {!nutrition && (
        <div className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800 border border-amber-200">
          To get meal-level food plans, first run a nutrition prediction from the Nutrition page.
        </div>
      )}
      <FoodRecommendation nutrition={nutrition} />
    </main>
  );
}

