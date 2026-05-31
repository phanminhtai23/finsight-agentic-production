import { Link } from "react-router-dom";
import { Button } from "../components/ui";
import { Logo } from "../components/Logo";
import { ThemeToggle } from "../components/ThemeToggle";
import { useAuth } from "../context/AuthContext";

function Icon({ path }: { path: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
    >
      <path d={path} />
    </svg>
  );
}

const FEATURES = [
  {
    icon: "M12 3v18M3 12h18",
    title: "Multi-agent reasoning",
    body: "A supervisor routes between Retrieval, Market Research, Analyst, Writer and a Critic that verifies every claim before you see it.",
  },
  {
    icon: "M4 6h16M4 12h10M4 18h7",
    title: "Grounded citations",
    body: "Each answer cites the exact document, page or live web source — no unverifiable numbers.",
  },
  {
    icon: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
    title: "Chat your documents",
    body: "Group files into topics, upload PDFs, Word docs or web links, and ask across them in natural language.",
  },
  {
    icon: "M13 2 3 14h9l-1 8 10-12h-9z",
    title: "Streaming + thinking",
    body: "Watch answers stream token-by-token, and expand the agent's step-by-step reasoning when you want it.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Create a topic",
    body: "A private knowledge space backed by its own vector collection.",
  },
  {
    n: "02",
    title: "Add your data",
    body: "Upload PDFs, Word files or paste web links — indexed automatically.",
  },
  {
    n: "03",
    title: "Ask anything",
    body: "Get a cited, analyst-grade answer with optional investment insight.",
  },
];

const STACK = ["LangGraph", "Qdrant", "Gemini", "MCP", "FastAPI", "React"];

export default function Landing() {
  const { user } = useAuth();
  return (
    <div className="min-h-screen bg-white text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">
      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-neutral-200/60 bg-white/70 backdrop-blur-xl dark:border-neutral-800/60 dark:bg-neutral-950/70">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3.5">
          <div className="flex items-center gap-2">
            <Logo className="h-7 w-7" />
            <span className="text-lg font-semibold tracking-tight">FinSight</span>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            {user ? (
              <Link to="/app">
                <Button>Open app</Button>
              </Link>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost">Sign in</Button>
                </Link>
                <Link to="/register">
                  <Button>Get started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute left-1/2 top-[-10rem] h-[28rem] w-[48rem] -translate-x-1/2 rounded-full bg-gradient-to-br from-indigo-300/40 to-violet-300/30 blur-3xl dark:from-indigo-600/20 dark:to-violet-700/20" />
        </div>
        <div className="mx-auto max-w-3xl px-6 pt-20 pb-10 text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-neutral-200 bg-white/60 px-3 py-1 text-xs text-neutral-600 dark:border-neutral-800 dark:bg-neutral-900/60 dark:text-neutral-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Multi-agent financial research
          </span>
          <h1 className="mt-6 text-balance text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
            Answers you can trust,{" "}
            <span className="bg-gradient-to-r from-indigo-600 to-violet-500 bg-clip-text text-transparent">
              with the receipts.
            </span>
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-pretty text-lg text-neutral-600 dark:text-neutral-400">
            FinSight reads your documents and the live web, reasons over them with a team of AI
            agents, and answers every question with inline citations.
          </p>
          <div className="mt-9 flex justify-center gap-3">
            <Link to={user ? "/app" : "/register"}>
              <Button className="px-6 py-3 text-base shadow-lg shadow-indigo-600/20">
                {user ? "Open the app" : "Start free"}
              </Button>
            </Link>
            <a href="https://github.com/phanminhtai23/finsight-multi-agent" target="_blank">
              <Button variant="outline" className="px-6 py-3 text-base">
                View on GitHub
              </Button>
            </a>
          </div>
        </div>

        {/* Product preview */}
        <div className="mx-auto max-w-3xl px-6 pb-20">
          <div className="overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-2xl shadow-neutral-900/10 dark:border-neutral-800 dark:bg-neutral-900">
            <div className="flex items-center gap-1.5 border-b border-neutral-200 px-4 py-3 dark:border-neutral-800">
              <span className="h-3 w-3 rounded-full bg-red-400" />
              <span className="h-3 w-3 rounded-full bg-amber-400" />
              <span className="h-3 w-3 rounded-full bg-green-400" />
              <span className="ml-3 text-xs text-neutral-400">FinSight — ACME Q3 report</span>
            </div>
            <div className="space-y-3 p-5 text-sm">
              <div className="flex justify-end">
                <div className="rounded-2xl bg-indigo-600 px-4 py-2 text-white">
                  What was Q3 net revenue and gross margin?
                </div>
              </div>
              <div className="max-w-[90%] rounded-2xl bg-neutral-100 px-4 py-3 dark:bg-neutral-800">
                Net revenue was <b>$1,250M</b>, up 18% YoY{" "}
                <sup className="text-indigo-500">[1]</sup>, with gross margin improving to{" "}
                <b>32%</b> <sup className="text-indigo-500">[1]</sup>.
                <div className="mt-2 border-t border-neutral-200 pt-2 text-xs text-neutral-400 dark:border-neutral-700">
                  Sources: [1] ACME_Q3_2024.pdf · p.4
                </div>
              </div>
            </div>
          </div>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm">
            <span className="text-xs uppercase tracking-wider text-neutral-400">Built with</span>
            {STACK.map((s) => (
              <span key={s} className="font-medium text-neutral-500 dark:text-neutral-400">
                {s}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="text-center text-3xl font-semibold tracking-tight">
          Research, grounded and fast
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-center text-neutral-500">
          Everything you need to turn a pile of filings into decisions you can defend.
        </p>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="group rounded-2xl border border-neutral-200 bg-white p-6 transition hover:border-indigo-300 hover:shadow-lg hover:shadow-indigo-600/5 dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-indigo-700"
            >
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300">
                <Icon path={f.icon} />
              </div>
              <h3 className="mt-4 font-medium">{f.title}</h3>
              <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="border-y border-neutral-200 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-900/40">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <h2 className="text-center text-3xl font-semibold tracking-tight">How it works</h2>
          <div className="mt-12 grid gap-8 sm:grid-cols-3">
            {STEPS.map((s) => (
              <div key={s.n}>
                <div className="bg-gradient-to-r from-indigo-600 to-violet-500 bg-clip-text font-mono text-4xl font-bold text-transparent">
                  {s.n}
                </div>
                <h3 className="mt-3 font-medium">{s.title}</h3>
                <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 to-violet-600 px-8 py-16 text-center text-white">
          <div className="pointer-events-none absolute inset-0 opacity-20 [background:radial-gradient(circle_at_30%_20%,white,transparent_40%)]" />
          <h2 className="relative text-3xl font-semibold tracking-tight sm:text-4xl">
            Start researching in minutes
          </h2>
          <p className="relative mx-auto mt-3 max-w-md text-indigo-100">
            Free to try. Bring your documents, ask your questions, get cited answers.
          </p>
          <Link to={user ? "/app" : "/register"} className="relative mt-8 inline-block">
            <button className="rounded-lg bg-white px-6 py-3 text-base font-medium text-indigo-700 transition hover:bg-indigo-50">
              {user ? "Open the app" : "Get started free"}
            </button>
          </Link>
        </div>
      </section>

      <footer className="border-t border-neutral-200 py-10 text-center text-sm text-neutral-500 dark:border-neutral-800">
        <div className="flex items-center justify-center gap-2">
          <Logo className="h-5 w-5" />
          <span className="font-medium text-neutral-700 dark:text-neutral-300">FinSight</span>
        </div>
        <p className="mt-2">Multi-agent financial research · LangGraph · Qdrant · Gemini</p>
      </footer>
    </div>
  );
}
