import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { Conversation, Topic } from "../lib/types";
import { useAuth } from "../context/AuthContext";
import { Logo } from "./Logo";
import { ProfileModal } from "./ProfileModal";
import { ThemeToggle } from "./ThemeToggle";
import { TierBadge } from "./TierBadge";
import { Button, Input } from "./ui";
import { UsageBar } from "./UsageBar";

export function Sidebar({
  selectedId,
  onSelect,
  onManageData,
  onCollapse,
  dataVersion,
}: {
  selectedId: string | null;
  onSelect: (c: Conversation) => void;
  onManageData: () => void;
  onCollapse: () => void;
  dataVersion: number;
}) {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [topicId, setTopicId] = useState<string>("");
  const [showProfile, setShowProfile] = useState(false);

  async function loadConversations() {
    const { data } = await api.get<Conversation[]>("/conversations");
    setConversations(data);
  }
  useEffect(() => {
    loadConversations();
    api.get<Topic[]>("/topics").then((r) => setTopics(r.data));
  }, [dataVersion]);

  const topicName = (id?: string | null) => topics.find((t) => t.id === id)?.name;

  async function deleteConversation(c: Conversation, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm(`Delete "${c.title ?? "New conversation"}"?`)) return;
    await api.delete(`/conversations/${c.id}`);
    await loadConversations();
    if (selectedId === c.id) onSelect(null as unknown as Conversation);
  }

  async function createConversation() {
    const { data } = await api.post<Conversation>("/conversations", {
      title: title.trim() || null, // empty → auto-named from the first message
      topic_id: topicId || null,
    });
    setCreating(false);
    setTitle("");
    setTopicId("");
    await loadConversations();
    onSelect(data);
  }

  return (
    <aside className="flex h-full w-72 flex-col border-r border-neutral-200 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-950">
      <div className="flex items-center justify-between p-3">
        <div className="flex items-center gap-2">
          <Logo className="h-7 w-7" />
          <span className="font-semibold tracking-tight">FinSight</span>
        </div>
        <div className="flex items-center gap-1">
          <Button onClick={() => setCreating((v) => !v)} className="px-2 py-1 text-xs">
            + New
          </Button>
          <Button
            variant="ghost"
            onClick={onCollapse}
            className="px-2 py-1"
            title="Collapse sidebar"
          >
            «
          </Button>
        </div>
      </div>

      {creating && (
        <div className="space-y-2 border-y border-neutral-200 p-3 dark:border-neutral-800">
          <Input
            placeholder="Title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <select
            value={topicId}
            onChange={(e) => setTopicId(e.target.value)}
            className="w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm dark:border-neutral-700 dark:bg-neutral-900"
          >
            <option value="">No topic (web only)</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <Button className="w-full" onClick={createConversation}>
            Create
          </Button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-2">
        {conversations.map((c) => (
          <div
            key={c.id}
            className={`group flex items-center rounded-lg ${
              selectedId === c.id
                ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                : "hover:bg-neutral-100 dark:hover:bg-neutral-800"
            }`}
          >
            <button
              onClick={() => onSelect(c)}
              className="min-w-0 flex-1 px-3 py-2 text-left"
            >
              <div className="truncate text-sm">{c.title ?? "New conversation"}</div>
              {c.topic_id && (
                <div className="truncate text-xs text-neutral-400">📁 {topicName(c.topic_id)}</div>
              )}
            </button>
            <button
              onClick={(e) => deleteConversation(c, e)}
              className="mr-1 hidden rounded p-1 text-neutral-400 hover:bg-red-100 hover:text-red-600 group-hover:block dark:hover:bg-red-900/40 dark:hover:text-red-400"
              title="Delete conversation"
            >
              🗑
            </button>
          </div>
        ))}
      </div>

      <div className="border-t border-neutral-200 dark:border-neutral-800">
        <button
          onClick={onManageData}
          className="w-full px-4 py-2 text-left text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800"
        >
          📁 Manage data (topics)
        </button>
        {user?.is_admin && (
          <Link
            to="/admin"
            className="block w-full px-4 py-2 text-left text-sm font-medium text-indigo-600 hover:bg-neutral-100 dark:text-indigo-400 dark:hover:bg-neutral-800"
          >
            🛡️ Admin dashboard
          </Link>
        )}
        <UsageBar refreshKey={dataVersion} />

        <div className="flex items-center gap-2 border-t border-neutral-200 p-3 dark:border-neutral-800">
          <button
            onClick={() => setShowProfile(true)}
            className="flex min-w-0 flex-1 items-center gap-2 rounded-lg p-1 text-left hover:bg-neutral-100 dark:hover:bg-neutral-800"
          >
            {user?.avatar_url ? (
              <img src={user.avatar_url} className="h-8 w-8 rounded-full object-cover" />
            ) : (
              <div className="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-semibold text-white">
                {(user?.full_name ?? user?.email ?? "?")[0]?.toUpperCase()}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-sm font-medium">
                  {user?.full_name ?? "Account"}
                </span>
                {user && <TierBadge tier={user.tier} />}
              </div>
              <div className="truncate text-xs text-neutral-400">{user?.email}</div>
            </div>
          </button>
          <ThemeToggle />
        </div>
      </div>

      {showProfile && <ProfileModal onClose={() => setShowProfile(false)} />}
    </aside>
  );
}
