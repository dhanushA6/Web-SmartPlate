import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import FoodDetection from '../components/FoodDetection';
import NutritionHandler from '../components/NutritionHandler';
import { checkSuitability } from '../api/apiClient';

const MEAL_TYPES = ['Breakfast', 'Lunch', 'Snacks', 'Dinner'];
const MACRO_KEYS = ['energy_kcal', 'carb_g', 'protein_g', 'fat_g'];
const SUITABILITY_STORAGE_KEY = 'suitabilityCheckState:v1';

function loadSavedSuitabilityState() {
  try {
    const saved = localStorage.getItem(SUITABILITY_STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

function computeMacros(food) {
  const per100 = food.nutritionPer100g || {};
  const qty = Number(food.quantityGrams) || 0;
  const factor = qty / 100;
  const macros = {};
  MACRO_KEYS.forEach((key) => {
    const value = per100[key];
    macros[key] = value != null ? Number((value * factor).toFixed(2)) : null;
  });
  return macros;
}

export default function SuitabilityCheck() {
  const savedState = useMemo(() => loadSavedSuitabilityState(), []);

  const [activeTab, setActiveTab] = useState(savedState?.activeTab || 'image'); // 'image' | 'manual'

  const [imageFoods, setImageFoods] = useState(savedState?.imageFoods || []);
  const [selectedImageFoods, setSelectedImageFoods] = useState(savedState?.selectedImageFoods || []);

  const [manualFoods, setManualFoods] = useState(savedState?.manualFoods || []);
  const [selectedManualFoods, setSelectedManualFoods] = useState(savedState?.selectedManualFoods || []);

  const [mealType, setMealType] = useState(savedState?.mealType || '');
  const [result, setResult] = useState(savedState?.result || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(savedState?.error || null);

  const resultSectionRef = useRef(null);

  const currentSelectedFoods =
    activeTab === 'image' ? selectedImageFoods : selectedManualFoods;

  const foodsWithNutrition = useMemo(
    () =>
      currentSelectedFoods.map((food) => ({
        ...food,
        macros: computeMacros(food)
      })),
    [currentSelectedFoods]
  );

  const totals = useMemo(() => {
    const acc = { energy_kcal: 0, carb_g: 0, protein_g: 0, fat_g: 0 };
    foodsWithNutrition.forEach((food) => {
      MACRO_KEYS.forEach((key) => {
        const val = food.macros?.[key];
        if (val != null) acc[key] += val;
      });
    });
    return {
      energy_kcal: Number(acc.energy_kcal.toFixed(1)),
      carb_g: Number(acc.carb_g.toFixed(1)),
      protein_g: Number(acc.protein_g.toFixed(1)),
      fat_g: Number(acc.fat_g.toFixed(1))
    };
  }, [foodsWithNutrition]);

  useEffect(() => {
    const snapshot = {
      activeTab,
      imageFoods,
      selectedImageFoods,
      manualFoods,
      selectedManualFoods,
      mealType,
      result,
      error
    };
    localStorage.setItem(SUITABILITY_STORAGE_KEY, JSON.stringify(snapshot));
  }, [activeTab, imageFoods, selectedImageFoods, manualFoods, selectedManualFoods, mealType, result, error]);

  const handleFoodsDetected = useCallback((detectedFoods) => {
    setImageFoods(detectedFoods);
    setSelectedImageFoods([]);
    setResult(null);
  }, []);

  const handleImageFoodsChange = useCallback((updatedFoods) => {
    setImageFoods(updatedFoods);
    setResult(null);
  }, []);

  const handleCheckSuitability = async () => {
    const userId = localStorage.getItem('userId');
    if (!userId) {
      setError('User not logged in. Please log in again.');
      return;
    }
    if (!mealType) {
      setError('Please select a meal type.');
      return;
    }
    if (!foodsWithNutrition.length) {
      setError('Please add at least one food to the selection and run the check.');
      return;
    }

    const foodsPayload = foodsWithNutrition.map((food) => ({
      food_name: food.name,
      portion_g: Number(food.quantityGrams) || 0,
      nutrients_per_100g: food.nutritionPer100g || {}
    }));

    const payload = {
      user_id: userId,
      meal_type: mealType,
      foods: foodsPayload,
      macro_totals: totals
    };

    try {
      setLoading(true);
      setError(null);
      const response = await checkSuitability(payload);
      setResult(response.data || null);
      setTimeout(() => {
        resultSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (e) {
      setError('Failed to evaluate meal suitability. Please try again.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = () => {
    setImageFoods([]);
    setSelectedImageFoods([]);
    setManualFoods([]);
    setSelectedManualFoods([]);
    setMealType('');
    setResult(null);
    setError(null);
    localStorage.removeItem(SUITABILITY_STORAGE_KEY);
  };

  const renderUserFriendly = () => {
    if (!result?.user_friendly_response) return null;
    const uf = result.user_friendly_response;
    return (
      <div className="space-y-3">
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-slate-900">
            Overall Meal Suitability
          </h3>
          <p className="mt-1 text-sm text-slate-700">
            <span className="font-semibold text-brand-600">{uf.overall_meal.suitability}</span> –{' '}
            {uf.overall_meal.simple_reason}
          </p>
          {uf.overall_meal.note && (
            <p className="mt-1 text-xs text-slate-600">{uf.overall_meal.note}</p>
          )}
        </div>
        <div className="card p-4">
          <h4 className="text-sm font-semibold text-slate-900">Per-food view</h4>
          <ul className="mt-2 space-y-2 text-sm">
            {uf.foods.map((f) => (
              <li key={f.food_name} className="flex flex-col">
                <span className="font-medium text-slate-900">
                  {f.food_name} – {f.suitability}
                </span>
                <span className="text-slate-700">{f.simple_reason}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  const renderStructuredSummary = () => {
    if (!result) return null;
    const analysis = result.meal_analysis || {};
    const overall = result.overall_meal || {};
    return (
      <div className="space-y-3">
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-slate-900">Nutritional summary</h3>
          <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
            <div>
              <dt className="text-xs text-slate-500">Energy</dt>
              <dd className="text-slate-900">
                {analysis.total_calories != null ? `${analysis.total_calories} kcal` : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Carbs</dt>
              <dd className="text-slate-900">
                {analysis.total_carbs != null ? `${analysis.total_carbs} g` : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Protein</dt>
              <dd className="text-slate-900">
                {analysis.total_protein != null ? `${analysis.total_protein} g` : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Fat</dt>
              <dd className="text-slate-900">
                {analysis.total_fat != null ? `${analysis.total_fat} g` : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Fibre</dt>
              <dd className="text-slate-900">
                {analysis.total_fiber != null ? `${analysis.total_fiber} g` : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Sodium</dt>
              <dd className="text-slate-900">
                {analysis.total_sodium != null ? `${analysis.total_sodium} mg` : '—'}
              </dd>
            </div>
          </dl>
        </div>
        {overall.rules && overall.rules.length > 0 && (
          <div className="card p-4">
            <h3 className="text-sm font-semibold text-slate-900">Warnings & rules</h3>
            <ul className="mt-2 space-y-1 text-sm">
              {overall.rules.map((rule, idx) => (
                <li key={`${rule.rule}-${idx}`} className="text-slate-800">
                  <span className="font-medium">{rule.label}:</span> {rule.reason}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Suitability Check</h1>
        <p className="text-sm text-slate-600 mt-1">
          Upload a food image or enter foods manually, then run a suitability check for your selected meal.
        </p>
      </div>

      {/* Sub-tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-1" aria-label="Suitability check method">
          <button
            type="button"
            onClick={() => setActiveTab('image')}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
              activeTab === 'image'
                ? 'border-brand-600 text-brand-600 bg-white border-b-white -mb-px'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            Image Upload
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('manual')}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
              activeTab === 'manual'
                ? 'border-brand-600 text-brand-600 bg-white border-b-white -mb-px'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            Manual Entry
          </button>
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === 'image' && (
        <div className="space-y-6">
          <FoodDetection onFoodsDetected={handleFoodsDetected} />
          <NutritionHandler
            mode="image"
            imageFoods={imageFoods}
            onImageFoodsChange={handleImageFoodsChange}
            selectedFoods={selectedImageFoods}
            onSelectedFoodsChange={setSelectedImageFoods}
          />
        </div>
      )}

      {activeTab === 'manual' && (
        <div className="space-y-6">
          <NutritionHandler
            mode="manual"
            manualFoods={manualFoods}
            onManualFoodsChange={setManualFoods}
            selectedFoods={selectedManualFoods}
            onSelectedFoodsChange={setSelectedManualFoods}
          />
        </div>
      )}

      {/* Shared: meal type + check + result */}
      <section ref={resultSectionRef} className="space-y-4 scroll-mt-6">
        <div className="card p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-base font-semibold text-slate-900">Run suitability check</h3>
            <p className="text-xs text-slate-600">
              Select meal type and run the check for the foods you selected in the current tab.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex flex-wrap gap-2">
              {MEAL_TYPES.map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setMealType(type)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                    mealType === type
                      ? 'bg-brand-600 text-white border-brand-600'
                      : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={handleCheckSuitability}
              disabled={loading || !foodsWithNutrition.length}
              className="primary-btn text-xs sm:text-sm disabled:opacity-60 disabled:cursor-not-allowed inline-flex items-center gap-2"
            >
              {loading ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Checking…
                </>
              ) : (
                'Check Suitability'
              )}
            </button>
            <button
              type="button"
              onClick={handleClearAll}
              className="secondary-btn text-xs sm:text-sm"
            >
              Clear Result
            </button>
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {result && (
          <section className="space-y-4">
            {renderUserFriendly()}
            {renderStructuredSummary()}
          </section>
        )}
      </section>
    </main>
  );
}
