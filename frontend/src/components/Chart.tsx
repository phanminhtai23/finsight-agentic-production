import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartSpec } from "../lib/types";

const COLORS = ["#6366f1", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#06b6d4"];
const axisProps = { stroke: "#9ca3af", fontSize: 12, tickLine: false };

type Row = Record<string, string | number>;

function firstStringKey(data: Row[]): string | undefined {
  return data.length ? Object.keys(data[0]).find((k) => typeof data[0][k] === "string") : undefined;
}

function numericSeries(data: Row[], exclude: (string | undefined)[]): { key: string; name?: string }[] {
  if (!data.length) return [];
  return Object.keys(data[0])
    .filter((k) => !exclude.includes(k) && typeof data[0][k] === "number")
    .map((k) => ({ key: k, name: k }));
}

export function Chart({ spec }: { spec: ChartSpec }) {
  const data = spec.data ?? [];
  // Be resilient to the model omitting x / series.
  const xKey = spec.x ?? firstStringKey(data);
  const series = spec.series?.length ? spec.series : numericSeries(data, [xKey]);
  const grid = <CartesianGrid strokeDasharray="3 3" stroke="#9ca3af33" vertical={false} />;
  const tooltip = (
    <Tooltip
      contentStyle={{
        borderRadius: 10,
        border: "1px solid #e5e7eb",
        fontSize: 12,
        background: "rgba(255,255,255,0.96)",
      }}
    />
  );

  let inner: React.ReactElement;
  if (spec.type === "pie") {
    inner = (
      <PieChart>
        <Pie
          data={data}
          dataKey={spec.valueKey ?? "value"}
          nameKey={spec.nameKey ?? "name"}
          outerRadius={88}
          innerRadius={48}
          paddingAngle={2}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        {tooltip}
        <Legend />
      </PieChart>
    );
  } else if (spec.type === "line" || spec.type === "area") {
    const Wrapper = spec.type === "area" ? AreaChart : LineChart;
    inner = (
      <Wrapper data={data}>
        {grid}
        <XAxis dataKey={xKey} {...axisProps} />
        <YAxis {...axisProps} />
        {tooltip}
        <Legend />
        {series.map((s, i) =>
          spec.type === "area" ? (
            <Area
              key={s.key}
              dataKey={s.key}
              name={s.name ?? s.key}
              stroke={COLORS[i % COLORS.length]}
              fill={COLORS[i % COLORS.length]}
              fillOpacity={0.18}
              strokeWidth={2}
            />
          ) : (
            <Line
              key={s.key}
              dataKey={s.key}
              name={s.name ?? s.key}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          ),
        )}
      </Wrapper>
    );
  } else {
    inner = (
      <BarChart data={data}>
        {grid}
        <XAxis dataKey={xKey} {...axisProps} />
        <YAxis {...axisProps} />
        {tooltip}
        <Legend />
        {series.map((s, i) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.name ?? s.key}
            fill={COLORS[i % COLORS.length]}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    );
  }

  return (
    <div className="mt-3 rounded-xl border border-neutral-200 bg-white p-3 dark:border-neutral-700 dark:bg-neutral-900">
      {spec.title && <div className="mb-2 text-sm font-medium">{spec.title}</div>}
      <ResponsiveContainer width="100%" height={250}>
        {inner}
      </ResponsiveContainer>
    </div>
  );
}
