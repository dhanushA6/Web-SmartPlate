import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { detectFoodsFromImage } from '../api/apiClient';

export default function FoodDetection({ onFoodsDetected }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError(null);
  };

  const handleDetectFoods = async () => {
    if (!selectedFile) {
      setError('Please upload a food image first.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await detectFoodsFromImage(selectedFile);
      const data = response.data || {};

      if (!data.foods || !Array.isArray(data.foods)) {
        setError('Unexpected response from detection service.');
        return;
      }

      const foods = data.foods.map((item, index) => {
        const quantity = item.quantity || {};
        return {
          id: `${item.food_name || 'food'}-${index}`,
          name: item.food_name,
          quantityGrams: quantity.grams ?? 0,
          quantityUnits: {
            pieces: quantity.pieces ?? 0,
            bowl: quantity.bowl ?? 0,
            cup: quantity.cup ?? 0
          },
          nutritionPer100g: item.nutrition_per_100g || null
        };
      });

      onFoodsDetected?.(foods);
    } catch (e) {
      setError('Failed to detect foods from image. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-900">Upload food image</h2>
      <p className="text-sm text-slate-600">
        Upload a meal photo to automatically detect foods and estimate quantities.
      </p>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <label className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 cursor-pointer transition-colors">
          <span className="font-medium">Choose image</span>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
          />
        </label>
        <button
          type="button"
          onClick={handleDetectFoods}
          disabled={loading || !selectedFile}
          className="primary-btn text-sm disabled:opacity-60 disabled:cursor-not-allowed inline-flex items-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Analyzing…
            </>
          ) : (
            'Detect Foods'
          )}
        </button>
      </div>

      {previewUrl && (
        <div className="relative rounded-xl border border-slate-200 bg-slate-50 overflow-hidden inline-block max-w-full">
          <img
            src={previewUrl}
            alt="Uploaded meal"
            className="max-h-72 sm:max-h-80 w-auto object-contain block"
          />
          {loading && (
            <div
              className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900/60 text-white transition-opacity"
              aria-live="polite"
            >
              <Loader2 size={40} className="animate-spin mb-3" />
              <span className="text-sm font-medium">Analyzing food…</span>
              <span className="text-xs opacity-90 mt-1">Detecting items and nutrition</span>
            </div>
          )}
        </div>
      )}

      {error && (
        <p className="text-sm text-red-600 rounded-lg bg-red-50 px-3 py-2 border border-red-100">
          {error}
        </p>
      )}
    </section>
  );
}

