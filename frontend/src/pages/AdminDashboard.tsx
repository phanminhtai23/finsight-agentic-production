import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
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
import { Card, Spinner } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { api, formatBytes } from "../lib/api";
import type { AdminStats, AdminUser } from "../lib/types";

const PIE = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4", "#a855f7"];

function StatCard({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent: string }) {
  return (
    <div className={`rounded-2xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-900`}>
      <div className={`mb-2 inline-flex h-9 w-9 items-center justify-center rounded-xl text-lg ${accent}`}>
        {label.split(" ")[0]}
      </div>
      <div className="text-2xl font-semibold tracking-tight">{value}</div>
      <div className="text-xs text-neutral-500">{label.replace(/^\S+\s/, "")}</div>
      {sub && <div className="mt-1 text-xs text-neutral-400">{sub}</div>}
    </div>
  );
}

function ChartBox({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card className="p-4">
      <h3 className="mb-3 text-sm font-medium text-neutral-600 dark:text-neutral-300">{title}</h3>
      <div style={{ width: "100%", height: 240 }}>
        <ResponsiveContainer>{children as any}</ResponsiveContainer>
      </div>
    </Card>
  );
}

function Pill({ ok, yes, no }: { ok: boolean; yes: string; no: string }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs ${
        ok
          ? "bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400"
          : "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400"
      }`}
    >
      {ok ? yes : no}
    </span>
  );
}

export default function AdminDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

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
    if (!confirm(`Delete ${u.email} and ALL their data (documents, chats)? This cannot be undone.`)) return;
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

  const tierData = useMemo(
    () => Object.entries(stats?.tier_distribution ?? {}).map(([name, value]) => ({ name, value })),
    [stats],
  );
  const providerData = useMemo(
    () => Object.entries(stats?.provider_distribution ?? {}).map(([name, value]) => ({ name, value })),
    [stats],
  );
  const verifyData = useMemo(
    () =>
      stats
        ? [
            { name: "Verified", value: stats.verified_users },
            { name: "Unverified", value: stats.unverified_users },
          ]
        : [],
    [stats],
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
          <StatCard label="👥 Users" value={String(stats?.total_users ?? 0)} accent="bg-indigo-100 dark:bg-indigo-500/15" sub={`${stats?.admin_users ?? 0} admin`} />
          <StatCard label="✅ Verified" value={String(stats?.verified_users ?? 0)} accent="bg-green-100 dark:bg-green-500/15" sub={`${stats?.unverified_users ?? 0} pending`} />
          <StatCard label="📄 Documents" value={String(stats?.total_documents ?? 0)} accent="bg-amber-100 dark:bg-amber-500/15" />
          <StatCard label="💬 Requests" value={String(stats?.total_messages ?? 0)} accent="bg-cyan-100 dark:bg-cyan-500/15" sub={`${stats?.total_conversations ?? 0} chats`} />
          <StatCard label="💾 Storage" value={formatBytes(stats?.total_storage_bytes ?? 0)} accent="bg-purple-100 dark:bg-purple-500/15" />
          <StatCard label="🗂️ Topics/chats" value={String(stats?.total_conversations ?? 0)} accent="bg-rose-100 dark:bg-rose-500/15" />
        </div>

        {/* Time series */}
        <div className="grid gap-4 lg:grid-cols-2">
          <ChartBox title="New signups (by day)">
            <AreaChart data={stats?.signups_by_day ?? []}>
              <defs>
                <linearGradient id="su" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#88888822" />
              <XAxis dataKey="date" fontSize={11} tickLine={false} />
              <YAxis allowDecimals={false} fontSize={11} width={28} />
              <Tooltip />
              <Area type="monotone" dataKey="count" stroke="#6366f1" fill="url(#su)" />
            </AreaChart>
          </ChartBox>
          <ChartBox title="Requests / messages (by day)">
            <LineChart data={stats?.messages_by_day ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#88888822" />
              <XAxis dataKey="date" fontSize={11} tickLine={false} />
              <YAxis allowDecimals={false} fontSize={11} width={28} />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#06b6d4" strokeWidth={2} dot={false} />
            </LineChart>
          </ChartBox>
        </div>

        {/* Distributions */}
        <div className="grid gap-4 md:grid-cols-3">
          <ChartBox title="Users by tier">
            <PieChart>
              <Pie data={tierData} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75} paddingAngle={3}>
                {tierData.map((_, i) => (
                  <Cell key={i} fill={PIE[i % PIE.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ChartBox>
          <ChartBox title="Email verification">
            <PieChart>
              <Pie data={verifyData} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75} paddingAngle={3}>
                <Cell fill="#22c55e" />
                <Cell fill="#f59e0b" />
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ChartBox>
          <ChartBox title="Auth provider">
            <BarChart data={providerData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#88888822" />
              <XAxis dataKey="name" fontSize={11} tickLine={false} />
              <YAxis allowDecimals={false} fontSize={11} width={28} />
              <Tooltip />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {providerData.map((_, i) => (
                  <Cell key={i} fill={PIE[i % PIE.length]} />
                ))}
              </Bar>
            </BarChart>
          </ChartBox>
        </div>

        {/* Users table */}
        <Card className="p-0 overflow-hidden">
          <div className="border-b border-neutral-200 px-5 py-3 text-sm font-medium dark:border-neutral-800">
            All users ({users.length})
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 text-left text-xs uppercase text-neutral-500 dark:bg-neutral-800/50">
                <tr>
                  <th className="px-5 py-2 font-medium">User</th>
                  <th className="px-3 py-2 font-medium">Tier</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium text-right">Storage</th>
                  <th className="px-3 py-2 font-medium text-right">Docs</th>
                  <th className="px-3 py-2 font-medium text-right">Requests</th>
                  <th className="px-3 py-2 font-medium">Joined</th>
                  <th className="px-3 py-2 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
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
                      <Pill ok={u.is_verified} yes="Verified" no="Pending" />
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
