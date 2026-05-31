import { useEffect, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api, streamChat } from "../lib/api";
import type { ChartSpec, Citation, Message } from "../lib/types";
import { Chart } from "./Chart";
import { Logo } from "./Logo";
import { Markdown } from "./Markdown";
import { Spinner } from "./ui";

interface LocalMsg {
  role: string;
  content: string;
  citations?: Citation[];
  thinking?: string;
  charts?: ChartSpec[];
  tools?: string[];
}

const TOOL_LABELS: Record<string, string> = {
  rag_search: "🔎 Document search",
  web_search: "🌐 Web search · MCP",
  chart: "📊 Chart",
};

function ToolChips({ tools }: { tools: string[] }) {
  if (!tools.length) return null;
  return (
    <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
      <span className="text-[11px] text-neutral-400">Tools used:</span>
      {tools.map((t) => (
        <span
          key={t}
          className="inline-flex items-center rounded-full bg-indigo-50 px-2 py-0.5 text-[11px] font-medium text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"
        >
          {TOOL_LABELS[t] ?? t}
        </span>
      ))}
    </div>
  );
}

const SUGGESTIONS = [
  "Summarize the key figures",
  "What are the main risks?",
  "Is this worth investing in?",
];

function Avatar() {
  return <Logo className="mt-0.5 h-8 w-8 shrink-0" />;
}

function UserAvatar() {
  const { user } = useAuth();
  if (user?.avatar_url) {
    return (
      <img src={user.avatar_url} className="mt-0.5 h-8 w-8 shrink-0 rounded-full object-cover" />
    );
  }
  return (
    <div className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-neutral-300 text-xs font-semibold text-neutral-700 dark:bg-neutral-700 dark:text-neutral-200">
      {(user?.full_name ?? user?.email ?? "U")[0]?.toUpperCase()}
    </div>
  );
}

function Sources({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-1.5 border-t border-neutral-200 pt-2.5 dark:border-neutral-700">
      {citations.map((c) => {
        const label = `[${c.index}] ${c.document_title ?? c.document_id}${
          c.page != null ? ` · p.${c.page}` : ""
        }`;
        const cls =
          "inline-flex max-w-[16rem] items-center gap-1 truncate rounded-full border border-neutral-200 bg-white px-2.5 py-0.5 text-xs text-neutral-500 hover:border-indigo-300 hover:text-indigo-600 dark:border-neutral-700 dark:bg-neutral-900 dark:hover:border-indigo-700";
        return c.url ? (
          <a key={c.index} href={c.url} target="_blank" className={cls} title={c.snippet}>
            {label}
          </a>
        ) : (
          <span key={c.index} className={cls} title={c.snippet}>
            {label}
          </span>
        );
      })}
    </div>
  );
}

function Thinking({ text }: { text: string }) {
  return (
    <details className="mb-2 rounded-xl border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm dark:border-neutral-800 dark:bg-neutral-900/60">
      <summary className="cursor-pointer select-none text-xs font-medium text-neutral-500">
        💭 Reasoning
      </summary>
      <p className="mt-2 whitespace-pre-wrap text-neutral-500 dark:text-neutral-400">{text}</p>
    </details>
  );
}

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5">
      <path
        d="M12 19V5M5 12l7-7 7 7"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function ChatView({
  conversationId,
  topicName,
}: {
  conversationId: string;
  topicName?: string;
}) {
  const [messages, setMessages] = useState<LocalMsg[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [liveThinking, setLiveThinking] = useState("");
  const [liveAnswer, setLiveAnswer] = useState("");
  const [liveCharts, setLiveCharts] = useState<ChartSpec[]>([]);
  const [liveTools, setLiveTools] = useState<string[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<number | null>(null);

  function stopTimer() {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }
  useEffect(() => stopTimer, []);

  useEffect(() => {
    api
      .get<Message[]>(`/conversations/${conversationId}/messages`)
      .then((r) =>
        setMessages(
          r.data.map((m) => ({
            role: m.role,
            content: m.content,
            citations: m.citations ?? undefined,
            charts: m.charts ?? undefined,
            tools: m.tools ?? undefined,
          })),
        ),
      );
    setLiveThinking("");
    setLiveAnswer("");
  }, [conversationId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, liveAnswer, liveThinking]);

  async function send(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || streaming) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: msg }]);
    setStreaming(true);
    setLiveThinking("");
    setLiveAnswer("");
    setLiveCharts([]);
    setLiveTools([]);
    setElapsed(0);
    const start = Date.now();
    timerRef.current = window.setInterval(() => setElapsed((Date.now() - start) / 1000), 100);

    let answer = "";
    let think = "";
    let cites: Citation[] = [];
    let toolList: string[] = [];
    const chartList: ChartSpec[] = [];
    try {
      await streamChat(conversationId, msg, thinking, (ev) => {
        if (ev.type === "thinking") setLiveThinking((think += ev.token));
        else if (ev.type === "token") setLiveAnswer((answer += ev.token));
        else if (ev.type === "citations") cites = ev.citations;
        else if (ev.type === "tools") {
          toolList = ev.tools;
          setLiveTools(ev.tools);
        } else if (ev.type === "chart") {
          chartList.push(ev.chart);
          setLiveCharts([...chartList]);
        }
      });
    } catch {
      answer = answer || "⚠️ Streaming failed.";
    }
    stopTimer();
    setMessages((m) => [
      ...m,
      {
        role: "assistant",
        content: answer,
        citations: cites,
        thinking: think || undefined,
        charts: chartList.length ? chartList : undefined,
        tools: toolList.length ? toolList : undefined,
      },
    ]);
    setLiveThinking("");
    setLiveAnswer("");
    setLiveCharts([]);
    setLiveTools([]);
    setStreaming(false);
  }

  return (
    <div className="flex h-full flex-col bg-white dark:bg-neutral-950">
      <div className="flex items-center gap-2 border-b border-neutral-200 px-4 py-2.5 dark:border-neutral-800">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
            topicName
              ? "bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"
              : "bg-neutral-100 text-neutral-500 dark:bg-neutral-800"
          }`}
        >
          {topicName ? `📁 ${topicName}` : "🌐 Web research"}
        </span>
        <span className="text-xs text-neutral-400">
          {topicName ? "Answers grounded in this topic's data" : "No topic — answers from the web"}
        </span>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.length === 0 && !streaming && (
            <div className="flex h-[60vh] flex-col items-center justify-center text-center">
              <Logo className="h-14 w-14" />
              <h2 className="mt-5 text-xl font-semibold">How can I help?</h2>
              <p className="mt-1 text-sm text-neutral-500">
                Ask about this topic's documents — or the live web.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="rounded-full border border-neutral-200 px-3.5 py-1.5 text-sm text-neutral-600 transition hover:border-indigo-300 hover:text-indigo-600 dark:border-neutral-800 dark:text-neutral-400 dark:hover:border-indigo-700"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) =>
            m.role === "user" ? (
              <div key={i} className="flex justify-end gap-3">
                <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-indigo-600 px-4 py-2.5 text-[15px] text-white shadow-sm">
                  {m.content}
                </div>
                <UserAvatar />
              </div>
            ) : (
              <div key={i} className="flex gap-3">
                <Avatar />
                <div className="min-w-0 flex-1">
                  {m.thinking && <Thinking text={m.thinking} />}
                  {m.tools?.length ? <ToolChips tools={m.tools} /> : null}
                  <div className="rounded-2xl rounded-tl-sm bg-neutral-100 px-4 py-3 text-[15px] dark:bg-neutral-800">
                    <Markdown>{m.content}</Markdown>
                    {m.citations && <Sources citations={m.citations} />}
                  </div>
                  {m.charts?.map((c, j) => <Chart key={j} spec={c} />)}
                </div>
              </div>
            ),
          )}

          {streaming && (
            <div className="flex gap-3">
              <Avatar />
              <div className="min-w-0 flex-1">
                <div className="mb-2 flex items-center gap-2 text-xs text-neutral-400">
                  <Spinner className="h-3.5 w-3.5" />
                  <span>
                    {liveAnswer ? "Generating" : liveThinking ? "Thinking" : "Researching"}…
                  </span>
                  <span className="font-mono tabular-nums text-neutral-500">
                    {elapsed.toFixed(1)}s
                  </span>
                </div>
                {liveTools.length > 0 && <ToolChips tools={liveTools} />}
                {liveThinking && (
                  <div className="mb-2 rounded-xl border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm dark:border-neutral-800 dark:bg-neutral-900/60">
                    <div className="text-xs font-medium text-neutral-500">💭 Reasoning…</div>
                    <p className="mt-1 whitespace-pre-wrap text-neutral-500 dark:text-neutral-400">
                      {liveThinking}
                    </p>
                  </div>
                )}
                {liveAnswer && (
                  <div className="rounded-2xl rounded-tl-sm bg-neutral-100 px-4 py-3 text-[15px] dark:bg-neutral-800">
                    <Markdown>{liveAnswer}</Markdown>
                  </div>
                )}
                {liveCharts.map((c, j) => <Chart key={j} spec={c} />)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Composer */}
      <div className="px-4 pb-4 pt-2">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-end gap-1.5 rounded-2xl border border-neutral-300 bg-white p-2 shadow-sm transition focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/15 dark:border-neutral-700 dark:bg-neutral-900">
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Ask anything…"
              className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-neutral-400"
            />
            <button
              onClick={() => setThinking((v) => !v)}
              title="Toggle step-by-step reasoning"
              className="flex items-center gap-1.5 rounded-xl px-2 py-1.5"
            >
              <span
                className={`relative h-5 w-9 rounded-full transition ${
                  thinking ? "bg-indigo-600" : "bg-neutral-300 dark:bg-neutral-600"
                }`}
              >
                <span
                  className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${
                    thinking ? "left-[1.125rem]" : "left-0.5"
                  }`}
                />
              </span>
              <span className="text-xs font-medium text-neutral-500">💭 Thinking</span>
            </button>
            <button
              onClick={() => send()}
              disabled={streaming || !input.trim()}
              className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-indigo-600 text-white transition hover:bg-indigo-500 disabled:opacity-40"
            >
              {streaming ? <Spinner className="h-4 w-4 border-white/40 border-t-white" /> : <SendIcon />}
            </button>
          </div>
          <p className="mt-1.5 text-center text-[11px] text-neutral-400">
            FinSight can make mistakes — verify important figures.
          </p>
        </div>
      </div>
    </div>
  );
}
