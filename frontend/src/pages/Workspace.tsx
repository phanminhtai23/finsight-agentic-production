import { useEffect, useState } from "react";
import { ChatView } from "../components/ChatView";
import { Logo } from "../components/Logo";
import { Sidebar } from "../components/Sidebar";
import { TopicsManager } from "../components/TopicsManager";
import { Button } from "../components/ui";
import { api } from "../lib/api";
import type { Conversation, Topic } from "../lib/types";

export default function Workspace() {
  const [selected, setSelected] = useState<Conversation | null>(null);
  const [showTopics, setShowTopics] = useState(false);
  const [version, setVersion] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [topics, setTopics] = useState<Topic[]>([]);

  useEffect(() => {
    api.get<Topic[]>("/topics").then((r) => setTopics(r.data));
  }, [version]);

  const topicName = topics.find((t) => t.id === selected?.topic_id)?.name;

  return (
    <div className="flex h-screen bg-white dark:bg-neutral-950">
      {sidebarOpen ? (
        <Sidebar
          selectedId={selected?.id ?? null}
          onSelect={setSelected}
          onManageData={() => setShowTopics(true)}
          onCollapse={() => setSidebarOpen(false)}
          dataVersion={version}
        />
      ) : (
        <div className="flex h-full w-14 shrink-0 flex-col items-center gap-3 border-r border-neutral-200 bg-neutral-50 py-3 dark:border-neutral-800 dark:bg-neutral-950">
          <button onClick={() => setSidebarOpen(true)} title="Expand sidebar">
            <Logo className="h-8 w-8" />
          </button>
          <button
            onClick={() => setSidebarOpen(true)}
            title="Expand sidebar"
            className="grid h-9 w-9 place-items-center rounded-lg text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
          >
            »
          </button>
          <button
            onClick={() => {
              setSelected(null);
              setSidebarOpen(true);
            }}
            title="New conversation"
            className="grid h-9 w-9 place-items-center rounded-lg text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
          >
            ＋
          </button>
        </div>
      )}

      <main className="flex-1 overflow-hidden">
        {selected ? (
          <ChatView key={selected.id} conversationId={selected.id} topicName={topicName} />
        ) : (
          <div className="grid h-full place-items-center text-center">
            <div>
              <h2 className="text-xl font-semibold">Start a conversation</h2>
              <p className="mt-1 text-sm text-neutral-500">
                Create a chat from the sidebar — pin a topic to ground answers in your data.
              </p>
              <Button className="mt-4" onClick={() => setShowTopics(true)}>
                Manage your data
              </Button>
            </div>
          </div>
        )}
      </main>

      {showTopics && (
        <TopicsManager
          onClose={() => {
            setShowTopics(false);
            setVersion((v) => v + 1);
          }}
          onChanged={() => setVersion((v) => v + 1)}
        />
      )}
    </div>
  );
}
