import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid
} from "recharts";

const MACRO_COLORS = {
  carbs: "#F97316",
  protein: "#3B82F6",
  fat: "#A855F7",
  fiber: "#22C55E"
};

const COLORS = [MACRO_COLORS.carbs, MACRO_COLORS.protein, MACRO_COLORS.fat, MACRO_COLORS.fiber];

const toTitleCase = (value) =>
  value ? value.charAt(0).toUpperCase() + value.slice(1) : value;

/**
 * Custom label renderer for the outside of the pie
 * Shows only rounded whole numbers
 */
const renderOutsideLabel = ({ value }) => {
  return Math.round(value);
};

export function DailyMacroPieChart({ daily }) {
  const data = [
    { name: "Carbohydrates", value: daily?.daily_carbohydrates_g || 0 },
    { name: "Protein", value: daily?.daily_protein_g || 0 },
    { name: "Fat", value: daily?.daily_fat_g || 0 },
    { name: "Fiber", value: daily?.daily_fiber_g || 0 }
  ];

  return (
    <div className="card overflow-hidden">
      <div className="card-header bg-slate-50/50">
        <h2 className="card-title text-base">Daily Macronutrient Composition</h2>
      </div>

      <div className="card-body h-72 sm:h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
              label={renderOutsideLabel}
            >
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} stroke="white" strokeWidth={1} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => `${Math.round(value)} g`} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function MealDistributionPieChart({ distribution }) {
  const data = distribution 
    ? Object.entries(distribution).map(([meal, value]) => ({
        name: toTitleCase(meal),
        value: Number(
          ((Number(value) <= 1 ? Number(value) * 100 : Number(value)) || 0).toFixed(1)
        )
      }))
    : [];

  return (
    <div className="card overflow-hidden">
      <div className="card-header bg-slate-50/50">
        <h2 className="card-title text-base">Meal Distribution</h2>
      </div>

      <div className="card-body h-72 sm:h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
              label={({ value }) => `${Math.round(value)}%`}
            >
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} stroke="white" strokeWidth={1} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => `${Number(value).toFixed(1)}%`} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function MealMacroBarChart({ mealName, values }) {
  const data = [
    { name: 'Carbs', value: values?.daily_carbohydrates_g ?? 0, fill: MACRO_COLORS.carbs },
    { name: 'Protein', value: values?.daily_protein_g ?? 0, fill: MACRO_COLORS.protein },
    { name: 'Fat', value: values?.daily_fat_g ?? 0, fill: MACRO_COLORS.fat },
    { name: 'Fiber', value: values?.daily_fiber_g ?? 0, fill: MACRO_COLORS.fiber }
  ].filter((d) => d.value > 0);

  if (data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={120}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis type="number" tick={{ fontSize: 10 }} unit=" g" />
        <YAxis type="category" dataKey="name" width={52} tick={{ fontSize: 11 }} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} isAnimationActive={true}>
          {data.map((entry, index) => (
            <Cell key={entry.name} fill={entry.fill} />
          ))}
        </Bar>
        <Tooltip formatter={(v) => `${Number(v).toFixed(1)} g`} contentStyle={{ fontSize: '12px' }} />
      </BarChart>
    </ResponsiveContainer>
  );
}