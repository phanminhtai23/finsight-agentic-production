import { useEffect, useState } from "react";
import { api, formatBytes } from "../lib/api";
import type { Usage } from "../lib/types";

export function UsageBar({ refreshKey = 0 }: { refreshKey?: number }) {
  const [usage, setUsage] = useState<Usage | null>(null);

  useEffect(() => {
    api
      .get<Usage>("/auth/me/usage")
      .then((r) => setUsage(r.data))
      .catch(() => {});
  }, [refreshKey]);

  if (!usage) return null;
  const pct = Math.min(100, usage.percent);
  return (
    <div className="px-3 py-2 text-xs">
      <div className="mb-1 flex justify-between text-neutral-500">
        <span>Storage</span>
        <span>
          {formatBytes(usage.used_bytes)} / {usage.quota_mb} MB
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-800">
        <div
          className={pct > 90 ? "h-full bg-red-500" : "h-full bg-indigo-600"}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
