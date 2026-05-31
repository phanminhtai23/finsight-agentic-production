import { useEffect, useRef, useState } from "react";
import { api, formatBytes } from "../lib/api";
import type { Document, Topic } from "../lib/types";
import { Button, Input } from "./ui";

interface UploadProgress {
  name: string;
  phase: "uploading" | "extracting" | "done" | "failed";
  percent: number;
}

async function pollTask(taskId: string, onProgress: (p: number) => void): Promise<boolean> {
  for (let i = 0; i < 120; i++) {
    const { data } = await api.get(`/tasks/${taskId}`);
    onProgress(data.progress ?? 0);
    if (data.status === "succeeded") return true;
    if (data.status === "failed") return false;
    await new Promise((r) => setTimeout(r, 1500));
  }
  return false;
}

export function TopicsManager({
  onClose,
  onChanged,
}: {
  onClose: () => void;
  onChanged: () => void;
}) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [active, setActive] = useState<Topic | null>(null);
  const [docs, setDocs] = useState<Document[]>([]);
  const [newName, setNewName] = useState("");
  const [url, setUrl] = useState("");
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function loadTopics() {
    const { data } = await api.get<Topic[]>("/topics");
    setTopics(data);
  }
  async function loadDocs(topic: Topic) {
    setActive(topic);
    const { data } = await api.get<Document[]>(`/topics/${topic.id}/documents`);
    setDocs(data);
  }
  useEffect(() => {
    loadTopics();
  }, []);

  async function createTopic() {
    if (!newName.trim()) return;
    const { data } = await api.post<Topic>("/topics", { name: newName.trim() });
    setNewName("");
    await loadTopics();
    loadDocs(data);
    onChanged();
  }

  async function afterIngest(taskId: string) {
    setProgress((p) => (p ? { ...p, phase: "extracting", percent: 0 } : p));
    const ok = await pollTask(taskId, (pct) =>
      setProgress((p) => (p ? { ...p, percent: pct } : p)),
    );
    setProgress((p) => (p ? { ...p, phase: ok ? "done" : "failed" } : p));
    if (active) await loadDocs(active);
    await loadTopics();
    onChanged();
    setTimeout(() => setProgress(null), 1200);
  }

  async function uploadFile(file: File) {
    if (!active) return;
    setProgress({ name: file.name, phase: "uploading", percent: 0 });
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data } = await api.post(`/topics/${active.id}/documents`, fd, {
        onUploadProgress: (e) =>
          setProgress((p) =>
            p ? { ...p, percent: e.total ? Math.round((e.loaded / e.total) * 100) : 0 } : p,
          ),
      });
      await afterIngest(data.task_id);
    } catch {
      setProgress((p) => (p ? { ...p, phase: "failed" } : p));
    }
  }

  async function addUrl() {
    if (!active || !url.trim()) return;
    setProgress({ name: url.trim(), phase: "extracting", percent: 0 });
    try {
      const { data } = await api.post(`/topics/${active.id}/documents/url`, { url: url.trim() });
      setUrl("");
      await afterIngest(data.task_id);
    } catch {
      setProgress((p) => (p ? { ...p, phase: "failed" } : p));
    }
  }

  async function deleteDoc(id: string) {
    await api.delete(`/documents/${id}`);
    if (active) await loadDocs(active);
    await loadTopics();
    onChanged();
  }

  async function deleteTopic(t: Topic) {
    if (!confirm(`Delete topic "${t.name}" and all its data?`)) return;
    await api.delete(`/topics/${t.id}`);
    if (active?.id === t.id) {
      setActive(null);
      setDocs([]);
    }
    await loadTopics();
    onChanged();
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="flex h-[36rem] w-full max-w-4xl overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-xl dark:border-neutral-800 dark:bg-neutral-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Topics list */}
        <aside className="flex w-64 flex-col border-r border-neutral-200 dark:border-neutral-800">
          <div className="border-b border-neutral-200 p-3 font-medium dark:border-neutral-800">
            Topics
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {topics.map((t) => (
              <button
                key={t.id}
                onClick={() => loadDocs(t)}
                className={`group flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm ${
                  active?.id === t.id
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                    : "hover:bg-neutral-100 dark:hover:bg-neutral-800"
                }`}
              >
                <span className="truncate">
                  {t.name}
                  <span className="ml-1 text-xs text-neutral-400">({t.document_count})</span>
                </span>
                <span
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteTopic(t);
                  }}
                  className="hidden text-neutral-400 hover:text-red-500 group-hover:inline"
                >
                  ✕
                </span>
              </button>
            ))}
          </div>
          <div className="border-t border-neutral-200 p-2 dark:border-neutral-800">
            <Input
              placeholder="New topic name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && createTopic()}
            />
            <Button className="mt-2 w-full" onClick={createTopic}>
              Create topic
            </Button>
          </div>
        </aside>

        {/* Documents */}
        <section className="flex flex-1 flex-col">
          <div className="flex items-center justify-between border-b border-neutral-200 p-3 dark:border-neutral-800">
            <span className="font-medium">{active ? active.name : "Select a topic"}</span>
            <Button variant="ghost" onClick={onClose} className="px-2">
              ✕
            </Button>
          </div>

          {active ? (
            <>
              <div className="flex flex-wrap items-center gap-2 border-b border-neutral-200 p-3 dark:border-neutral-800">
                <input
                  ref={fileRef}
                  type="file"
                  hidden
                  accept=".pdf,.docx,.png,.jpg,.jpeg"
                  onChange={(e) => e.target.files?.[0] && uploadFile(e.target.files[0])}
                />
                <Button variant="outline" onClick={() => fileRef.current?.click()}>
                  Upload file
                </Button>
                <Input
                  className="max-w-xs"
                  placeholder="https://… web link"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && addUrl()}
                />
                <Button variant="outline" onClick={addUrl}>
                  Add link
                </Button>
              </div>

              {progress && (
                <div className="border-b border-neutral-200 px-4 py-3 text-sm dark:border-neutral-800">
                  <div className="mb-1 flex justify-between">
                    <span className="truncate">{progress.name}</span>
                    <span className="text-neutral-500">
                      {progress.phase === "uploading"
                        ? `Uploading ${progress.percent}%`
                        : progress.phase === "extracting"
                          ? `Extracting ${progress.percent}%`
                          : progress.phase === "done"
                            ? "Done ✓"
                            : "Failed ✕"}
                    </span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-800">
                    <div
                      className={
                        progress.phase === "failed" ? "h-full bg-red-500" : "h-full bg-indigo-600"
                      }
                      style={{ width: `${progress.percent}%` }}
                    />
                  </div>
                </div>
              )}

              <div className="flex-1 overflow-y-auto p-3">
                {docs.length === 0 && (
                  <p className="p-6 text-center text-sm text-neutral-400">
                    No documents yet. Upload a file or add a web link.
                  </p>
                )}
                {docs.map((d) => (
                  <div
                    key={d.id}
                    className="flex items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-neutral-50 dark:hover:bg-neutral-800"
                  >
                    <div className="min-w-0">
                      <div className="truncate">{d.title}</div>
                      <div className="text-xs text-neutral-400">
                        {d.source_type} · {formatBytes(d.size_bytes)} ·{" "}
                        <span
                          className={
                            d.status === "ready"
                              ? "text-green-600"
                              : d.status === "failed"
                                ? "text-red-500"
                                : "text-amber-500"
                          }
                        >
                          {d.status}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => deleteDoc(d.id)}
                      className="text-neutral-400 hover:text-red-500"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex-1 overflow-y-auto p-8">
              <h3 className="text-base font-semibold">How topics work</h3>
              <ol className="mt-4 space-y-3 text-sm text-neutral-600 dark:text-neutral-400">
                <li>
                  <b className="text-indigo-600">1. Create a topic</b> — a private knowledge
                  space. Each topic gets its own vector collection, so its data stays isolated.
                </li>
                <li>
                  <b className="text-indigo-600">2. Add data</b> — upload PDFs, Word files or
                  images, or paste a web link. Files are parsed, chunked and indexed automatically
                  (watch the extract progress bar).
                </li>
                <li>
                  <b className="text-indigo-600">3. Ask</b> — start a conversation and pin this
                  topic. Answers are grounded in this topic's documents, with citations.
                </li>
              </ol>
              <p className="mt-6 text-xs text-neutral-400">
                Supported: PDF, DOCX, images (OCR), web links · Storage is shared across your
                topics and counts toward your quota · Deleting a document frees its space.
              </p>
              <p className="mt-6 text-sm text-neutral-400">← Select a topic to manage its data.</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
