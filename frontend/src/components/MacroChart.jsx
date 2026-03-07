import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts";

const COLORS = ["#2563eb", "#10b981", "#f59e0b", "#ef4444"];

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
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Daily Macronutrient Composition</h2>
      </div>

      <div className="card-body h-80">
        <ResponsiveContainer width="100%" height="100%">
          {/* Reduced margin to 10 to maximize space while preventing cut-off */}
          <PieChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              outerRadius={90} // Balanced size to allow labels outside
              label={renderOutsideLabel}
              // cx="50%" cy="50%" ensures it stays centered
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => Math.round(value)} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function MealDistributionPieChart({ distribution }) {
  const data = distribution 
    ? Object.entries(distribution).map(([meal, value]) => ({
        name: meal,
        value: value || 0
      }))
    : [];

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Meal Distribution</h2>
      </div>

      <div className="card-body h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              outerRadius={90}
              label={renderOutsideLabel}
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => Math.round(value)} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}