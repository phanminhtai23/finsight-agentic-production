import { Area, Bar, Column, Line, Pie } from "@ant-design/plots";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Card, Spinner } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { api, formatBytes } from "../lib/api";
import type { AdminStats, AdminUser } from "../lib/types";

const PALETTE = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

function StatCard({
  emoji,
  label,
  value,
  sub,
  ring,
}: {
  emoji: string;
  label: string;
  value: string;
  sub?: string;
  ring: string;
}) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
      <div className={`absolute -right-6 -top-6 h-20 w-20 rounded-full opacity-20 blur-xl ${ring}`} />
      <div className="mb-2 text-xl">{emoji}</div>
      <div className="text-2xl font-semibold tracking-tight tabular-nums">{value}</div>
      <div className="text-xs text-neutral-500">{label}</div>
      {sub && <div className="mt-1 text-xs text-neutral-400">{sub}</div>}
    </div>
  );
}

export default function AdminDashboard() {
  const { user } = useAuth();
  const { theme } = useTheme();
  const chartTheme = theme === "dark" ? "classicDark" : "academy";
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [s, u] = await Promise.all([
        api.get<AdminStats>("/admin/stats"),
        api.get<AdminUser[]>("/admin/users"),
      ]);
      setStats(s.data);
      setUsers(u.data);
      setError(null);
    } catch (e: any) {
      setError(e.response?.status === 403 ? "Admin access required." : "Failed to load admin data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function remove(u: AdminUser) {
    if (!confirm(`Delete ${u.email} and ALL their data (documents, chats)? This cannot be undone.`))
      return;
    setDeleting(u.id);
    try {
      await api.delete(`/admin/users/${u.id}`);
      await load();
    } catch (e: any) {
      alert(e.response?.data?.detail ?? "Delete failed");
    } finally {
      setDeleting(null);
    }
  }

  const base = useMemo(
    () => ({
      height: 240,
      autoFit: true,
      theme: chartTheme,
      scale: { color: { range: PALETTE } },
      style: { background: "transparent", viewFill: "transparent" },
    }),
    [chartTheme],
  );

  const growth = useMemo(() => {
    let total = 0;
    return (stats?.signups_by_day ?? []).map((d) => ({ date: d.date, total: (total += d.count) }));
  }, [stats]);

  const tierData = useMemo(
    () => Object.entries(stats?.tier_distribution ?? {}).map(([type, value]) => ({ type, value })),
    [stats],
  );
  const providerData = useMemo(
    () =>
      Object.entries(stats?.provider_distribution ?? {}).map(([type, value]) => ({ type, value })),
    [stats],
  );
  const verifyData = useMemo(
    () =>
      stats
        ? [
            { type: "Verified", value: stats.verified_users },
            { type: "Unverified", value: stats.unverified_users },
          ]
        : [],
    [stats],
  );
  const label = (u: AdminUser) => u.full_name || u.email.split("@")[0];
  const topRequests = useMemo(
    () =>
      [...users]
        .sort((a, b) => b.message_count - a.message_count)
        .slice(0, 8)
        .map((u) => ({ name: label(u), value: u.message_count })),
    [users],
  );
  const topStorage = useMemo(
    () =>
      [...users]
        .filter((u) => u.storage_used_bytes > 0)
        .sort((a, b) => b.storage_used_bytes - a.storage_used_bytes)
        .slice(0, 8)
        .map((u) => ({ name: label(u), value: +(u.storage_used_bytes / 1048576).toFixed(2) })),
    [users],
  );

  const filtered = useMemo(
    () =>
      users.filter(
        (u) =>
          !query ||
          u.email.toLowerCase().includes(query.toLowerCase()) ||
          (u.full_name ?? "").toLowerCase().includes(query.toLowerCase()),
      ),
    [users, query],
  );

  if (loading)
    return (
      <div className="grid h-screen place-items-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  if (error)
    return (
      <div className="grid h-screen place-items-center gap-3 text-center">
        <p className="text-red-500">{error}</p>
        <Link to="/app" className="text-indigo-600 hover:underline">
          ← Back to app
        </Link>
      </div>
    );

  const donut = (data: any[]) => ({
    ...base,
    data,
    angleField: "value",
    colorField: "type",
    innerRadius: 0.62,
    label: { text: "value", style: { fontWeight: 600 } },
    legend: { color: { position: "bottom" } },
  });

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <header className="sticky top-0 z-10 border-b border-neutral-200 bg-white/80 backdrop-blur dark:border-neutral-800 dark:bg-neutral-900/80">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <span className="text-lg font-semibold">🛡️ Admin Dashboard</span>
            <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300">
              {user?.email}
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <button onClick={load} className="text-neutral-500 hover:text-indigo-600">
              ↻ Refresh
            </button>
            <Link to="/app" className="text-indigo-600 hover:underline">
              ← Back to app
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-6 py-6">
        {/* Stat cards */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          <StatCard emoji="👥" label="Total users" value={String(stats?.total_users ?? 0)} sub={`${stats?.admin_users ?? 0} admin`} ring="bg-indigo-400" />
          <StatCard emoji="✅" label="Verified" value={String(stats?.verified_users ?? 0)} sub={`${stats?.unverified_users ?? 0} pending`} ring="bg-green-400" />
          <StatCard emoji="📄" label="Documents" value={String(stats?.total_documents ?? 0)} ring="bg-amber-400" />
          <StatCard emoji="💬" label="Requests" value={String(stats?.total_messages ?? 0)} sub={`${stats?.total_conversations ?? 0} chats`} ring="bg-cyan-400" />
          <StatCard emoji="💾" label="Storage used" value={formatBytes(stats?.total_storage_bytes ?? 0)} ring="bg-purple-400" />
          <StatCard emoji="⚡" label="Avg req/user" value={stats && stats.total_users ? (stats.total_messages / stats.total_users).toFixed(1) : "0"} ring="bg-rose-400" />
        </div>

        {/* Growth + activity */}
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="p-4">
            <h3 className="mb-3 text-sm font-medium text-neutral-600 dark:text-neutral-300">📈 Cumulative user growth</h3>
            <Area {...base} data={growth} xField="date" yField="total" shapeField="smooth" style={{ fillOpacity: 0.35, lineWidth: 2 }} axis={{ y: { title: false }, x: { title: false } }} />
          </Card>
          <Card className="p-4">
            <h3 className="mb-3 text-sm font-medium text-neutral-600 dark:text-neutral-300">💬 Requests per day</h3>
            <Line {...base} data={stats?.messages_by_day ?? []} xField="date" yField="count" shapeField="smooth" style={{ lineWidth: 2.5 }} point={{ sizeField: 3 }} axis={{ y: { title: false }, x: { title: false } }} />
          </Card>
        </div>

        {/* Distributions */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="p-4">
            <h3 className="mb-3 text-sm font-medium text-neutral-600 dark:text-neutral-300">🏷️ Users by tier</h3>
            <Pie {...donut(tierData)} />
          </Card>
          <Card className="p-4">
            <h3 className="mb-3 text-sm font-medium text-neutral-600 dark:text-neutral-300">✉️ Email verification</h3>
            <Pie {...donut(verifyData)} scale={{ color: { range: ["#10b981", "#f59e0b"] } }} />
          </Card>
          <Card className="p-4">
            <h3 className="mb-3 text-sm font-medium text-neutral-600 dark:text-neutral-300">🔐 Auth provider</h3>
            <Column {...base} data={providerData} xField="type" yField="value" colorField="type" legend={false} style={{ radiusTopLeft: 6, radiusTopRight: 6 }} axis={{ y: { title: false }, x: { title: false } }} />
          </Card>
        </div>

        {/* Leaderboards */}
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="p-4">
            <h3 className="mb-3 text-sm font-medium text-neutral-600 dark:text-neutral-300">🏆 Most active users (requests)</h3>
            {topRequests.length ? (
              <Bar {...base} data={topRequests} xField="name" yField="value" colorField="name" legend={false} style={{ radiusTopRight: 6, radiusBottomRight: 6 }} axis={{ y: { title: false }, x: { title: false } }} />
            ) : (
              <p className="py-10 text-center text-sm text-neutral-400">No activity yet.</p>
            )}
          </Card>
          <Card className="p-4">
            <h3 className="mb-3 text-sm font-medium text-neutral-600 dark:text-neutral-300">💾 Top storage users (MB)</h3>
            {topStorage.length ? (
              <Bar {...base} data={topStorage} xField="name" yField="value" colorField="name" legend={false} style={{ radiusTopRight: 6, radiusBottomRight: 6 }} axis={{ y: { title: false }, x: { title: false } }} />
            ) : (
              <p className="py-10 text-center text-sm text-neutral-400">No storage used yet.</p>
            )}
          </Card>
        </div>

        {/* Users table */}
        <Card className="overflow-hidden p-0">
          <div className="flex items-center justify-between gap-3 border-b border-neutral-200 px-5 py-3 dark:border-neutral-800">
            <span className="text-sm font-medium">Users ({filtered.length})</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search email or name…"
              className="w-64 rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-sm outline-none focus:border-indigo-500 dark:border-neutral-700 dark:bg-neutral-900"
            />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 text-left text-xs uppercase text-neutral-500 dark:bg-neutral-800/50">
                <tr>
                  <th className="px-5 py-2 font-medium">User</th>
                  <th className="px-3 py-2 font-medium">Tier</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 text-right font-medium">Storage</th>
                  <th className="px-3 py-2 text-right font-medium">Docs</th>
                  <th className="px-3 py-2 text-right font-medium">Requests</th>
                  <th className="px-3 py-2 font-medium">Joined</th>
                  <th className="px-3 py-2 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u) => (
                  <tr key={u.id} className="border-t border-neutral-100 dark:border-neutral-800/70">
                    <td className="px-5 py-2.5">
                      <div className="flex items-center gap-2">
                        {u.avatar_url ? (
                          <img src={u.avatar_url} alt="" className="h-7 w-7 rounded-full object-cover" />
                        ) : (
                          <div className="grid h-7 w-7 place-items-center rounded-full bg-indigo-100 text-xs font-medium text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
                            {(u.full_name || u.email)[0].toUpperCase()}
                          </div>
                        )}
                        <div>
                          <div className="font-medium">
                            {u.full_name || "—"}{" "}
                            {u.is_admin && (
                              <span className="ml-1 rounded bg-indigo-600 px-1.5 py-0.5 text-[10px] text-white">ADMIN</span>
                            )}
                          </div>
                          <div className="text-xs text-neutral-500">{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 capitalize">{u.tier}</td>
                    <td className="px-3 py-2.5">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${
                          u.is_verified
                            ? "bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400"
                            : "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400"
                        }`}
                      >
                        {u.is_verified ? "Verified" : "Pending"}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right tabular-nums">{formatBytes(u.storage_used_bytes)}</td>
                    <td className="px-3 py-2.5 text-right tabular-nums">{u.document_count}</td>
                    <td className="px-3 py-2.5 text-right tabular-nums">{u.message_count}</td>
                    <td className="px-3 py-2.5 text-xs text-neutral-500">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td className="px-3 py-2.5 text-right">
                      {u.id !== user?.id && (
                        <button
                          onClick={() => remove(u)}
                          disabled={deleting === u.id}
                          className="rounded-md px-2 py-1 text-xs text-red-600 hover:bg-red-50 disabled:opacity-50 dark:hover:bg-red-500/10"
                        >
                          {deleting === u.id ? "…" : "Delete"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </main>
    </div>
  );
}
