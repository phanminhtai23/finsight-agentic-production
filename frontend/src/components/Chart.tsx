import { Area, Bar, Column, Funnel, Line, Pie, Radar, Rose, Scatter } from "@ant-design/plots";
import { useTheme } from "../context/ThemeContext";
import type { ChartSpec } from "../lib/types";

// A refined, brand-aligned palette (AntV applies it across series).
const PALETTE = [
  "#6366f1",
  "#06b6d4",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
];

type Row = Record<string, string | number>;

function firstStringKey(data: Row[]): string | undefined {
  return data.length ? Object.keys(data[0]).find((k) => typeof data[0][k] === "string") : undefined;
}

function numericKeys(data: Row[], exclude: (string | undefined)[]): string[] {
  if (!data.length) return [];
  return Object.keys(data[0]).filter(
    (k) => !exclude.includes(k) && typeof data[0][k] === "number",
  );
}

/** Wide rows ({period, revenue, profit}) → long records ({category, series, value}). */
function toLong(spec: ChartSpec) {
  const data = spec.data ?? [];
  const x = spec.x ?? firstStringKey(data) ?? "category";
  const series = spec.series?.length
    ? spec.series
    : numericKeys(data, [x]).map((k) => ({ key: k, name: k }));
  const rows: { category: string; series: string; value: number }[] = [];
  for (const row of data) {
    for (const s of series) {
      rows.push({
        category: String(row[x] ?? ""),
        series: s.name ?? s.key,
        value: Number(row[s.key]) || 0,
      });
    }
  }
  return { rows, multi: series.length > 1, x };
}

function pieData(spec: ChartSpec) {
  const nameKey = spec.nameKey ?? "name";
  const valueKey = spec.valueKey ?? "value";
  return (spec.data ?? []).map((r) => ({
    name: String(r[nameKey] ?? ""),
    value: Number(r[valueKey]) || 0,
  }));
}

export function Chart({ spec }: { spec: ChartSpec }) {
  const { theme } = useTheme();
  const dark = theme === "dark";
  const height = 280;
  const chartTheme = dark ? "classicDark" : "academy";
  const base: Record<string, unknown> = {
    height,
    autoFit: true,
    theme: chartTheme,
    scale: { color: { range: PALETTE } },
  };
  const transparent = { style: { background: "transparent", viewFill: "transparent" } };

  const { rows, multi } = toLong(spec);
  let node: React.ReactNode = null;

  switch (spec.type) {
    case "pie":
    case "donut": {
      const cfg: any = {
        ...base,
        ...transparent,
        data: pieData(spec),
        angleField: "value",
        colorField: "name",
        innerRadius: spec.type === "donut" ? 0.6 : 0,
        radius: 0.9,
        label: { text: "name", position: "outside" },
        legend: { color: { position: "right" } },
      };
      node = <Pie {...cfg} />;
      break;
    }
    case "rose": {
      const cfg: any = {
        ...base,
        ...transparent,
        data: pieData(spec),
        xField: "name",
        yField: "value",
        colorField: "name",
        radius: 0.9,
        label: { text: "value" },
        legend: { color: { position: "right" } },
      };
      node = <Rose {...cfg} />;
      break;
    }
    case "funnel": {
      const cfg: any = {
        ...base,
        ...transparent,
        data: pieData(spec),
        xField: "name",
        yField: "value",
        colorField: "name",
        label: { text: (d: any) => `${d.name}: ${d.value}` },
        legend: false,
      };
      node = <Funnel {...cfg} />;
      break;
    }
    case "radar": {
      const cfg: any = {
        ...base,
        ...transparent,
        data: rows,
        xField: "category",
        yField: "value",
        colorField: "series",
        area: { style: { fillOpacity: 0.2 } },
        scale: { ...((base as any).scale ?? {}), y: { domainMin: 0 } },
        legend: multi ? { color: { position: "top" } } : false,
      };
      node = <Radar {...cfg} />;
      break;
    }
    case "scatter": {
      const cfg: any = {
        ...base,
        ...transparent,
        data: rows,
        xField: "category",
        yField: "value",
        colorField: "series",
        size: 6,
        style: { fillOpacity: 0.75 },
        legend: multi ? { color: { position: "top" } } : false,
      };
      node = <Scatter {...cfg} />;
      break;
    }
    case "line": {
      const cfg: any = {
        ...base,
        ...transparent,
        data: rows,
        xField: "category",
        yField: "value",
        colorField: "series",
        shapeField: spec.smooth === false ? "line" : "smooth",
        style: { lineWidth: 2.5 },
        point: { sizeField: 3 },
        legend: multi ? { color: { position: "top" } } : false,
      };
      node = <Line {...cfg} />;
      break;
    }
    case "area": {
      const cfg: any = {
        ...base,
        ...transparent,
        data: rows,
        xField: "category",
        yField: "value",
        colorField: "series",
        shapeField: "smooth",
        stack: spec.stack ?? multi,
        style: { fillOpacity: 0.35, lineWidth: 2 },
        legend: multi ? { color: { position: "top" } } : false,
      };
      node = <Area {...cfg} />;
      break;
    }
    case "bar": {
      const cfg: any = {
        ...base,
        ...transparent,
        data: rows,
        xField: "category",
        yField: "value",
        colorField: "series",
        stack: spec.stack ?? false,
        group: multi && !spec.stack,
        legend: multi ? { color: { position: "top" } } : false,
      };
      node = <Bar {...cfg} />;
      break;
    }
    case "dualAxes":
    case "column":
    default: {
      const cfg: any = {
        ...base,
        ...transparent,
        data: rows,
        xField: "category",
        yField: "value",
        colorField: "series",
        stack: spec.stack ?? false,
        group: multi && !spec.stack,
        style: { radiusTopLeft: 5, radiusTopRight: 5 },
        legend: multi ? { color: { position: "top" } } : false,
      };
      node = <Column {...cfg} />;
      break;
    }
  }

  return (
    <div className="mt-3 overflow-hidden rounded-2xl border border-neutral-200/80 bg-gradient-to-b from-white to-neutral-50/50 p-4 shadow-sm dark:border-neutral-800 dark:from-neutral-900 dark:to-neutral-950/40">
      {spec.title && (
        <div className="mb-1 flex items-baseline gap-2">
          <span className="h-3.5 w-1 rounded-full bg-indigo-500" />
          <span className="text-sm font-semibold tracking-tight">{spec.title}</span>
        </div>
      )}
      {spec.subtitle && (
        <div className="mb-2 pl-3 text-xs text-neutral-500">{spec.subtitle}</div>
      )}
      <div style={{ height }}>{node}</div>
    </div>
  );
}
