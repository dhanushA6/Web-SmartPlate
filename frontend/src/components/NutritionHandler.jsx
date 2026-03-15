import { useMemo, useState } from 'react';
import { fetchFoodNutrition } from '../api/apiClient';

const MACRO_KEYS = ['energy_kcal', 'carb_g', 'protein_g', 'fat_g'];

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

export default function NutritionHandler({
  mode, // 'image' | 'manual'
  imageFoods = [],
  onImageFoodsChange,
  manualFoods = [],
  onManualFoodsChange,
  selectedFoods = [],
  onSelectedFoodsChange
}) {
  const [loadingManualAdd, setLoadingManualAdd] = useState(false);
  const [error, setError] = useState(null);
  const [manualName, setManualName] = useState('');
  const [manualQuantity, setManualQuantity] = useState('');

  const sourceFoods = mode === 'image' ? imageFoods : manualFoods;
  const setSourceFoods = mode === 'image' ? onImageFoodsChange : onManualFoodsChange;

  const sourceWithMacros = useMemo(
    () => sourceFoods.map((f) => ({ ...f, macros: computeMacros(f) })),
    [sourceFoods]
  );

  const selectedWithMacros = useMemo(
    () => selectedFoods.map((f) => ({ ...f, macros: computeMacros(f) })),
    [selectedFoods]
  );

  const totals = useMemo(() => {
    const acc = { energy_kcal: 0, carb_g: 0, protein_g: 0, fat_g: 0 };
    selectedWithMacros.forEach((food) => {
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
  }, [selectedWithMacros]);

  const isInSelection = (id) => selectedFoods.some((f) => f.sourceFoodId === id);

  const handleSourceQuantityChange = (id, value) => {
    const grams = value === '' ? '' : Number(value);
    const updated = sourceFoods.map((f) =>
      f.id === id ? { ...f, quantityGrams: grams } : f
    );
    setSourceFoods?.(updated);
    onSelectedFoodsChange?.(
      selectedFoods.map((f) =>
        f.sourceFoodId === id ? { ...f, quantityGrams: grams } : f
      )
    );
  };

  const handleSelectedQuantityChange = (selectedId, value) => {
    const grams = value === '' ? '' : Number(value);
    onSelectedFoodsChange?.(
      selectedFoods.map((f) =>
        f.id === selectedId ? { ...f, quantityGrams: grams } : f
      )
    );
  };

  const handleAddToSelection = (food) => {
    if (isInSelection(food.id)) return;
    onSelectedFoodsChange?.([
      ...selectedFoods,
      {
        id: `selected-${food.id}-${Date.now()}`,
        sourceFoodId: food.id,
        name: food.name,
        quantityGrams: food.quantityGrams,
        nutritionPer100g: food.nutritionPer100g
      }
    ]);
  };

  const handleRemoveFromSource = (id) => {
    setSourceFoods?.(sourceFoods.filter((f) => f.id !== id));
    onSelectedFoodsChange?.(selectedFoods.filter((f) => f.sourceFoodId !== id));
  };

  const handleRemoveFromSelection = (selectedId) => {
    onSelectedFoodsChange?.(selectedFoods.filter((f) => f.id !== selectedId));
  };

  const handleManualAdd = async (e) => {
    e.preventDefault();
    const name = manualName.trim();
    const qty = Number(manualQuantity);

    if (!name || !qty || qty <= 0) {
      setError('Please enter a valid food name and quantity in grams.');
      return;
    }

    try {
      setLoadingManualAdd(true);
      setError(null);
      const response = await fetchFoodNutrition(name);
      const per100g = response.data || {};
      if (Object.keys(per100g).length === 0 || per100g.error) {
        setError('Could not fetch nutrition for this food. Try another food name.');
        return;
      }
      const newFood = {
        id: `manual-${Date.now()}`,
        name,
        quantityGrams: qty,
        nutritionPer100g: per100g
      };
      onManualFoodsChange?.([...(manualFoods || []), newFood]);
      setManualName('');
      setManualQuantity('');
    } catch (err) {
      setError('Could not fetch nutrition for this food. Try another food name.');
    } finally {
      setLoadingManualAdd(false);
    }
  };

  const tableHeaders = (
    <>
      <th className="px-3 py-2 text-left font-medium text-slate-700">Food</th>
      <th className="px-3 py-2 text-left font-medium text-slate-700">Quantity (g)</th>
      <th className="px-3 py-2 text-right font-medium text-slate-700">Energy</th>
      <th className="px-3 py-2 text-right font-medium text-slate-700">Carbs</th>
      <th className="px-3 py-2 text-right font-medium text-slate-700">Protein</th>
      <th className="px-3 py-2 text-right font-medium text-slate-700">Fat</th>
      <th className="px-3 py-2 text-right font-medium text-slate-700">Actions</th>
    </>
  );

  return (
    <section className="space-y-6">
      {/* Image tab: only detected foods table */}
      {mode === 'image' && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900">Detected foods</h3>
          <p className="text-sm text-slate-600 mt-1">
            Add items to the selection below to include them in the suitability check.
          </p>
          <div className="overflow-x-auto mt-3">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>{tableHeaders}</tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sourceWithMacros.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-3 py-4 text-center text-slate-500">
                      No foods detected yet. Upload an image and click Detect Foods above.
                    </td>
                  </tr>
                ) : (
                  sourceWithMacros.map((food) => (
                    <tr key={food.id}>
                      <td className="px-3 py-2 text-slate-800">{food.name}</td>
                      <td className="px-3 py-2">
                        <input
                          type="number"
                          min="0"
                          className="w-24 rounded border border-slate-200 px-2 py-1 text-right text-sm"
                          value={food.quantityGrams === '' ? '' : food.quantityGrams}
                          onChange={(e) =>
                            handleSourceQuantityChange(food.id, e.target.value)
                          }
                        />
                      </td>
                      <td className="px-3 py-2 text-right text-slate-800">
                        {food.macros?.energy_kcal != null
                          ? `${food.macros.energy_kcal} kcal`
                          : '—'}
                      </td>
                      <td className="px-3 py-2 text-right text-slate-800">
                        {food.macros?.carb_g != null ? `${food.macros.carb_g} g` : '—'}
                      </td>
                      <td className="px-3 py-2 text-right text-slate-800">
                        {food.macros?.protein_g != null
                          ? `${food.macros.protein_g} g`
                          : '—'}
                      </td>
                      <td className="px-3 py-2 text-right text-slate-800">
                        {food.macros?.fat_g != null ? `${food.macros.fat_g} g` : '—'}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleAddToSelection(food)}
                            disabled={isInSelection(food.id)}
                            className="rounded-md border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {isInSelection(food.id) ? 'Added' : 'Add to Check'}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleRemoveFromSource(food.id)}
                            className="rounded-md border border-red-200 bg-red-50 px-2 py-1 text-xs font-medium text-red-700"
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Manual tab: add form + manual foods table */}
      {mode === 'manual' && (
        <>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-base font-semibold text-slate-900">Add food manually</h3>
            <p className="text-sm text-slate-600 mt-1">
              Enter food name and quantity. Nutrition will be fetched and the food added to the list.
            </p>
            <form
              onSubmit={handleManualAdd}
              className="mt-3 grid gap-3 sm:grid-cols-[1fr_140px_auto] sm:items-end"
            >
              <label className="block text-xs font-medium text-slate-700">
                Food name
                <input
                  type="text"
                  className="mt-1 w-full rounded border border-slate-200 bg-white px-2 py-2 text-sm"
                  placeholder="e.g., Idli, Dosa with sambar"
                  value={manualName}
                  onChange={(e) => setManualName(e.target.value)}
                />
              </label>
              <label className="block text-xs font-medium text-slate-700">
                Quantity (g)
                <input
                  type="number"
                  min="1"
                  className="mt-1 w-full rounded border border-slate-200 bg-white px-2 py-2 text-sm"
                  value={manualQuantity}
                  onChange={(e) => setManualQuantity(e.target.value)}
                />
              </label>
              <button
                type="submit"
                disabled={loadingManualAdd}
                className="primary-btn text-sm disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loadingManualAdd ? 'Fetching…' : 'Add Food'}
              </button>
            </form>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="text-base font-semibold text-slate-900">Foods you added</h3>
            <p className="text-sm text-slate-600 mt-1">
              Add items to the selection below to include them in the suitability check.
            </p>
            <div className="overflow-x-auto mt-3">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>{tableHeaders}</tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sourceWithMacros.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-3 py-4 text-center text-slate-500">
                        No foods yet. Add a food above.
                      </td>
                    </tr>
                  ) : (
                    sourceWithMacros.map((food) => (
                      <tr key={food.id}>
                        <td className="px-3 py-2 text-slate-800">{food.name}</td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            min="0"
                            className="w-24 rounded border border-slate-200 px-2 py-1 text-right text-sm"
                            value={food.quantityGrams === '' ? '' : food.quantityGrams}
                            onChange={(e) =>
                              handleSourceQuantityChange(food.id, e.target.value)
                            }
                          />
                        </td>
                        <td className="px-3 py-2 text-right text-slate-800">
                          {food.macros?.energy_kcal != null
                            ? `${food.macros.energy_kcal} kcal`
                            : '—'}
                        </td>
                        <td className="px-3 py-2 text-right text-slate-800">
                          {food.macros?.carb_g != null
                            ? `${food.macros.carb_g} g`
                            : '—'}
                        </td>
                        <td className="px-3 py-2 text-right text-slate-800">
                          {food.macros?.protein_g != null
                            ? `${food.macros.protein_g} g`
                            : '—'}
                        </td>
                        <td className="px-3 py-2 text-right text-slate-800">
                          {food.macros?.fat_g != null
                            ? `${food.macros.fat_g} g`
                            : '—'}
                        </td>
                        <td className="px-3 py-2 text-right">
                          <div className="flex justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => handleAddToSelection(food)}
                              disabled={isInSelection(food.id)}
                              className="rounded-md border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {isInSelection(food.id) ? 'Added' : 'Add to Check'}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleRemoveFromSource(food.id)}
                              className="rounded-md border border-red-200 bg-red-50 px-2 py-1 text-xs font-medium text-red-700"
                            >
                              Remove
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Selected for suitability check (same in both tabs) */}
      <div className="rounded-xl border-2 border-slate-300 bg-white p-4 shadow-sm">
        <h4 className="text-base font-semibold text-slate-900">
          Selected for suitability check
        </h4>
        <p className="text-sm text-slate-600 mt-1">
          {mode === 'image'
            ? 'Items you added from the detected foods list will be checked.'
            : 'Items you added from your manual list will be checked.'}
        </p>
        <div className="overflow-x-auto mt-3">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left font-medium text-slate-700">Food</th>
                <th className="px-3 py-2 text-left font-medium text-slate-700">Qty (g)</th>
                <th className="px-3 py-2 text-right font-medium text-slate-700">Energy</th>
                <th className="px-3 py-2 text-right font-medium text-slate-700">Carbs</th>
                <th className="px-3 py-2 text-right font-medium text-slate-700">Protein</th>
                <th className="px-3 py-2 text-right font-medium text-slate-700">Fat</th>
                <th className="px-3 py-2 text-right font-medium text-slate-700">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {selectedWithMacros.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-3 py-4 text-center text-slate-500">
                    No foods selected. Add foods from the table above to run the check.
                  </td>
                </tr>
              ) : (
                selectedWithMacros.map((food) => (
                  <tr key={food.id}>
                    <td className="px-3 py-2 text-slate-800">{food.name}</td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        min="0"
                        className="w-24 rounded border border-slate-200 px-2 py-1 text-right text-sm"
                        value={food.quantityGrams === '' ? '' : food.quantityGrams}
                        onChange={(e) =>
                          handleSelectedQuantityChange(food.id, e.target.value)
                        }
                      />
                    </td>
                    <td className="px-3 py-2 text-right text-slate-800">
                      {food.macros?.energy_kcal != null
                        ? `${food.macros.energy_kcal} kcal`
                        : '—'}
                    </td>
                    <td className="px-3 py-2 text-right text-slate-800">
                      {food.macros?.carb_g != null ? `${food.macros.carb_g} g` : '—'}
                    </td>
                    <td className="px-3 py-2 text-right text-slate-800">
                      {food.macros?.protein_g != null
                        ? `${food.macros.protein_g} g`
                        : '—'}
                    </td>
                    <td className="px-3 py-2 text-right text-slate-800">
                      {food.macros?.fat_g != null ? `${food.macros.fat_g} g` : '—'}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => handleRemoveFromSelection(food.id)}
                        className="rounded-md border border-red-200 bg-red-50 px-2 py-1 text-xs font-medium text-red-700"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            <tfoot className="bg-slate-50">
              <tr>
                <td className="px-3 py-2 font-medium text-slate-800">Total</td>
                <td className="px-3 py-2" />
                <td className="px-3 py-2 text-right font-medium text-slate-900">
                  {totals.energy_kcal} kcal
                </td>
                <td className="px-3 py-2 text-right font-medium text-slate-900">
                  {totals.carb_g} g
                </td>
                <td className="px-3 py-2 text-right font-medium text-slate-900">
                  {totals.protein_g} g
                </td>
                <td className="px-3 py-2 text-right font-medium text-slate-900">
                  {totals.fat_g} g
                </td>
                <td className="px-3 py-2" />
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </section>
  );
}
