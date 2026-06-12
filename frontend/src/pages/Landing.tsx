import { Link } from "react-router-dom";
import { Chart } from "../components/Chart";
import { Button } from "../components/ui";
import { Logo } from "../components/Logo";
import { ThemeToggle } from "../components/ThemeToggle";
import { useAuth } from "../context/AuthContext";
import type { ChartSpec } from "../lib/types";

const DEMO_CHART: ChartSpec = {
  type: "column",
  title: "ACME 2024 — Revenue vs Net income ($M)",
  x: "quarter",
  series: [
    { key: "revenue", name: "Revenue" },
    { key: "net_income", name: "Net income" },
  ],
  data: [
    { quarter: "Q1", revenue: 980, net_income: 120 },
    { quarter: "Q2", revenue: 1080, net_income: 150 },
    { quarter: "Q3", revenue: 1250, net_income: 180 },
    { quarter: "Q4", revenue: 1410, net_income: 210 },
  ],
};

const DEMO_TREND: ChartSpec = {
  type: "area",
  title: "Gross margin trend (%)",
  x: "quarter",
  smooth: true,
  series: [{ key: "margin", name: "Gross margin" }],
  data: [
    { quarter: "Q1", margin: 28 },
    { quarter: "Q2", margin: 30 },
    { quarter: "Q3", margin: 32 },
    { quarter: "Q4", margin: 34 },
  ],
};

function Icon({ path, className = "h-5 w-5" }: { path: string; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
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
    accent:
      "from-indigo-500 to-violet-500 shadow-indigo-500/25 group-hover:shadow-indigo-500/40",
    ring: "hover:border-indigo-300/70 dark:hover:border-indigo-700/70",
  },
  {
    icon: "M4 6h16M4 12h10M4 18h7",
    title: "Grounded citations",
    body: "Each answer cites the exact document, page or live web source — no unverifiable numbers.",
    accent: "from-cyan-500 to-sky-500 shadow-cyan-500/25 group-hover:shadow-cyan-500/40",
    ring: "hover:border-cyan-300/70 dark:hover:border-cyan-700/70",
  },
  {
    icon: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
    title: "Chat your documents",
    body: "Group files into topics, upload PDFs, Word docs or web links, and ask across them in natural language.",
    accent:
      "from-emerald-500 to-teal-500 shadow-emerald-500/25 group-hover:shadow-emerald-500/40",
    ring: "hover:border-emerald-300/70 dark:hover:border-emerald-700/70",
  },
  {
    icon: "M13 2 3 14h9l-1 8 10-12h-9z",
    title: "Streaming + thinking",
    body: "Watch answers stream token-by-token, and expand the agent's step-by-step reasoning when you want it.",
    accent: "from-amber-500 to-orange-500 shadow-amber-500/25 group-hover:shadow-amber-500/40",
    ring: "hover:border-amber-300/70 dark:hover:border-amber-700/70",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Create a topic",
    body: "A private knowledge space backed by its own vector collection.",
    icon: "M12 5v14M5 12h14",
  },
  {
    n: "02",
    title: "Add your data",
    body: "Upload PDFs, Word files or paste web links — indexed automatically.",
    icon: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12",
  },
  {
    n: "03",
    title: "Ask anything",
    body: "Get a cited, analyst-grade answer with optional investment insight.",
    icon: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
  },
];

const STACK = ["LangGraph", "Qdrant", "Gemini", "MCP", "FastAPI", "React"];

const PIPELINE = ["Supervisor", "Retrieval", "Analyst", "Critic"];

const STATS = [
  { value: "5", label: "specialized agents" },
  { value: "100%", label: "cited answers" },
  { value: "9+", label: "chart types, on the fly" },
];

/** Staggered entrance for above-the-fold content. */
function fadeUp(step: number) {
  return { animationDelay: `${step * 0.12}s` } as const;
}

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
          <nav className="hidden items-center gap-1 text-sm text-neutral-600 md:flex dark:text-neutral-400">
            {[
              ["Demo", "#demo"],
              ["Features", "#features"],
              ["How it works", "#how"],
            ].map(([label, href]) => (
              <a
                key={href}
                href={href}
                className="rounded-lg px-3 py-1.5 transition hover:bg-neutral-100 hover:text-neutral-900 dark:hover:bg-neutral-800 dark:hover:text-neutral-100"
              >
                {label}
              </a>
            ))}
          </nav>
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
                  <Button className="shadow-md shadow-indigo-600/20">Get started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="bg-grid absolute inset-0 [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,black,transparent)]" />
          <div className="animate-float absolute left-[12%] top-[-6rem] h-[26rem] w-[26rem] rounded-full bg-gradient-to-br from-indigo-400/35 to-violet-400/25 blur-3xl dark:from-indigo-600/20 dark:to-violet-700/15" />
          <div className="animate-float-slow absolute right-[8%] top-[4rem] h-[22rem] w-[22rem] rounded-full bg-gradient-to-br from-cyan-300/25 to-sky-400/20 blur-3xl dark:from-cyan-600/10 dark:to-sky-700/10" />
        </div>

        <div className="mx-auto max-w-3xl px-6 pt-20 pb-12 text-center sm:pt-24">
          <span
            className="animate-fade-up inline-flex items-center gap-2 rounded-full border border-indigo-200/70 bg-white/70 px-3.5 py-1.5 text-xs font-medium text-neutral-600 shadow-sm backdrop-blur dark:border-indigo-800/50 dark:bg-neutral-900/70 dark:text-neutral-300"
            style={fadeUp(0)}
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            Multi-agent financial research
          </span>
          <h1
            className="animate-fade-up mt-7 text-balance text-5xl font-bold leading-[1.04] tracking-tight sm:text-7xl"
            style={fadeUp(1)}
          >
            Answers you can trust,{" "}
            <span className="bg-gradient-to-r from-indigo-600 via-violet-500 to-indigo-500 bg-clip-text text-transparent">
              with the receipts.
            </span>
          </h1>
          <p
            className="animate-fade-up mx-auto mt-6 max-w-xl text-pretty text-lg text-neutral-600 dark:text-neutral-400"
            style={fadeUp(2)}
          >
            FinSight reads your documents and the live web, reasons over them with a team of AI
            agents, and answers every question with inline citations.
          </p>
          <div className="animate-fade-up mt-9 flex justify-center gap-3" style={fadeUp(3)}>
            <Link to={user ? "/app" : "/register"}>
              <Button className="px-6 py-3 text-base shadow-lg shadow-indigo-600/25 transition-transform hover:-translate-y-0.5">
                {user ? "Open the app" : "Start free"}
                <Icon path="M5 12h14M13 6l6 6-6 6" className="h-4 w-4" />
              </Button>
            </Link>
            <a href="https://github.com/phanminhtai23/finsight-multi-agent" target="_blank">
              <Button
                variant="outline"
                className="bg-white/60 px-6 py-3 text-base backdrop-blur transition-transform hover:-translate-y-0.5 dark:bg-neutral-900/60"
              >
                View on GitHub
              </Button>
            </a>
          </div>

          <dl
            className="animate-fade-up mx-auto mt-12 flex max-w-lg items-center justify-center divide-x divide-neutral-200 dark:divide-neutral-800"
            style={fadeUp(4)}
          >
            {STATS.map((s) => (
              <div key={s.label} className="px-6 text-center sm:px-8">
                <dt className="sr-only">{s.label}</dt>
                <dd className="bg-gradient-to-r from-indigo-600 to-violet-500 bg-clip-text text-2xl font-bold text-transparent sm:text-3xl">
                  {s.value}
                </dd>
                <dd className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">{s.label}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* Product preview */}
        <div className="mx-auto max-w-3xl px-6 pb-20">
          <div className="animate-fade-up relative" style={fadeUp(5)}>
            <div className="pointer-events-none absolute -inset-x-8 -top-6 bottom-0 -z-10 rounded-[2rem] bg-gradient-to-b from-indigo-500/15 via-violet-500/5 to-transparent blur-2xl" />
            <div className="overflow-hidden rounded-2xl border border-neutral-200/80 bg-white shadow-2xl shadow-indigo-950/10 ring-1 ring-neutral-900/5 dark:border-neutral-800 dark:bg-neutral-900 dark:ring-white/5">
              <div className="flex items-center gap-1.5 border-b border-neutral-200 bg-neutral-50/60 px-4 py-3 dark:border-neutral-800 dark:bg-neutral-900/60">
                <span className="h-3 w-3 rounded-full bg-red-400" />
                <span className="h-3 w-3 rounded-full bg-amber-400" />
                <span className="h-3 w-3 rounded-full bg-green-400" />
                <span className="ml-3 text-xs text-neutral-400">FinSight — ACME Q3 report</span>
                <span className="ml-auto inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
                  <span className="h-1 w-1 rounded-full bg-emerald-500" />
                  Live
                </span>
              </div>
              <div className="space-y-3 p-5 text-sm">
                <div className="flex justify-end">
                  <div className="rounded-2xl rounded-tr-sm bg-gradient-to-br from-indigo-600 to-indigo-700 px-4 py-2 text-white shadow-sm">
                    What was Q3 net revenue and gross margin?
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-neutral-400">
                  {PIPELINE.map((p, i) => (
                    <span key={p} className="inline-flex items-center gap-1.5">
                      <span className="rounded-md border border-neutral-200 bg-neutral-50 px-2 py-0.5 font-medium text-neutral-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400">
                        {p}
                      </span>
                      {i < PIPELINE.length - 1 && <span>›</span>}
                    </span>
                  ))}
                  <span className="ml-1 inline-flex items-center gap-1 font-medium text-emerald-500">
                    <Icon path="M20 6 9 17l-5-5" className="h-3 w-3" />
                    verified
                  </span>
                </div>
                <div className="max-w-[90%] rounded-2xl rounded-tl-sm bg-neutral-100 px-4 py-3 dark:bg-neutral-800">
                  Net revenue was <b>$1,250M</b>, up 18% YoY{" "}
                  <sup className="text-indigo-500">[1]</sup>, with gross margin improving to{" "}
                  <b>32%</b> <sup className="text-indigo-500">[1]</sup>.
                  <div className="mt-2 border-t border-neutral-200 pt-2 text-xs text-neutral-400 dark:border-neutral-700">
                    Sources: [1] ACME_Q3_2024.pdf · p.4
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-12 flex flex-wrap items-center justify-center gap-2.5 text-sm">
            <span className="mr-2 text-xs uppercase tracking-wider text-neutral-400">
              Built with
            </span>
            {STACK.map((s) => (
              <span
                key={s}
                className="rounded-full border border-neutral-200 bg-white/60 px-3.5 py-1 text-xs font-medium text-neutral-500 backdrop-blur transition hover:border-indigo-300 hover:text-indigo-600 dark:border-neutral-800 dark:bg-neutral-900/60 dark:text-neutral-400 dark:hover:border-indigo-700 dark:hover:text-indigo-400"
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Live demo — question → grounded answer + beautiful charts */}
      <section
        id="demo"
        className="border-y border-neutral-200 bg-neutral-50/60 dark:border-neutral-800 dark:bg-neutral-900/40"
      >
        <div className="mx-auto max-w-6xl px-6 py-20 sm:py-24">
          <p className="text-center text-sm font-semibold uppercase tracking-widest text-indigo-500">
            Live demo
          </p>
          <h2 className="mt-3 text-center text-3xl font-bold tracking-tight sm:text-4xl">
            See it in action
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-center text-neutral-500">
            Ask in plain language — FinSight answers with grounded citations and renders
            beautiful, on-the-fly charts (powered by AntV).
          </p>

          <div className="mt-14 grid items-start gap-6 lg:grid-cols-5">
            {/* Conversation */}
            <div className="space-y-3 lg:col-span-2">
              <div className="flex justify-end">
                <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-gradient-to-br from-indigo-600 to-indigo-700 px-4 py-2.5 text-sm text-white shadow-md shadow-indigo-600/20">
                  Compare ACME's quarterly revenue and net income for 2024, and show the
                  gross-margin trend.
                </div>
              </div>
              <div className="rounded-2xl rounded-tl-sm border border-neutral-200/70 bg-white px-4 py-3 text-sm shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
                Revenue climbed every quarter, from <b>$980M</b> in Q1 to <b>$1,410M</b> in Q4{" "}
                <sup className="text-indigo-500">[1]</sup>, while net income roughly doubled to{" "}
                <b>$210M</b> <sup className="text-indigo-500">[1]</sup>. Gross margin expanded
                from <b>28%</b> to <b>34%</b> over the year — a healthy operating-leverage signal.
                <div className="mt-2 border-t border-neutral-200 pt-2 text-xs text-neutral-400 dark:border-neutral-700">
                  Sources: [1] ACME_FY2024.pdf · p.4
                </div>
                <div className="mt-2 inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-neutral-400">
                  ⬇ Export PDF
                </div>
              </div>
            </div>

            {/* Charts */}
            <div className="grid gap-4 sm:grid-cols-2 lg:col-span-3">
              <Chart spec={DEMO_CHART} />
              <Chart spec={DEMO_TREND} />
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-20 sm:py-24">
        <p className="text-center text-sm font-semibold uppercase tracking-widest text-indigo-500">
          Features
        </p>
        <h2 className="mt-3 text-center text-3xl font-bold tracking-tight sm:text-4xl">
          Research, grounded and fast
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-center text-neutral-500">
          Everything you need to turn a pile of filings into decisions you can defend.
        </p>
        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className={`group rounded-2xl border border-neutral-200 bg-white p-6 transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-neutral-900/5 dark:border-neutral-800 dark:bg-neutral-900 dark:hover:shadow-black/20 ${f.ring}`}
            >
              <div
                className={`grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br text-white shadow-lg transition ${f.accent}`}
              >
                <Icon path={f.icon} />
              </div>
              <h3 className="mt-5 font-semibold tracking-tight">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-neutral-500 dark:text-neutral-400">
                {f.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section
        id="how"
        className="border-y border-neutral-200 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-900/40"
      >
        <div className="mx-auto max-w-6xl px-6 py-20 sm:py-24">
          <p className="text-center text-sm font-semibold uppercase tracking-widest text-indigo-500">
            How it works
          </p>
          <h2 className="mt-3 text-center text-3xl font-bold tracking-tight sm:text-4xl">
            From documents to decisions in three steps
          </h2>
          <div className="relative mt-14 grid gap-10 sm:grid-cols-3 sm:gap-8">
            {/* Connector line (desktop) */}
            <div className="pointer-events-none absolute left-[16%] right-[16%] top-7 hidden border-t-2 border-dashed border-indigo-200 sm:block dark:border-indigo-900" />
            {STEPS.map((s) => (
              <div key={s.n} className="relative text-center sm:text-left">
                <div className="relative z-10 mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-600/25 sm:mx-0">
                  <Icon path={s.icon} className="h-6 w-6" />
                </div>
                <div className="mt-5 font-mono text-xs font-bold tracking-widest text-indigo-500">
                  STEP {s.n}
                </div>
                <h3 className="mt-2 text-lg font-semibold tracking-tight">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-neutral-500 dark:text-neutral-400">
                  {s.body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 via-indigo-700 to-violet-700 px-8 py-16 text-center text-white shadow-2xl shadow-indigo-900/30 sm:py-20">
          <div className="pointer-events-none absolute inset-0 opacity-25 [background:radial-gradient(circle_at_30%_20%,white,transparent_45%)]" />
          <div className="pointer-events-none absolute inset-0 opacity-[0.07] [background-image:linear-gradient(to_right,white_1px,transparent_1px),linear-gradient(to_bottom,white_1px,transparent_1px)] [background-size:44px_44px]" />
          <div className="animate-float pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
          <h2 className="relative text-3xl font-bold tracking-tight sm:text-5xl">
            Start researching in minutes
          </h2>
          <p className="relative mx-auto mt-4 max-w-md text-lg text-indigo-100">
            Free to try. Bring your documents, ask your questions, get cited answers.
          </p>
          <div className="relative mt-9 flex flex-wrap items-center justify-center gap-3">
            <Link to={user ? "/app" : "/register"}>
              <button className="inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3.5 text-base font-semibold text-indigo-700 shadow-lg transition hover:-translate-y-0.5 hover:bg-indigo-50">
                {user ? "Open the app" : "Get started free"}
                <Icon path="M5 12h14M13 6l6 6-6 6" className="h-4 w-4" />
              </button>
            </Link>
            <a href="https://github.com/phanminhtai23/finsight-multi-agent" target="_blank">
              <button className="rounded-xl border border-white/30 bg-white/10 px-7 py-3.5 text-base font-medium text-white backdrop-blur transition hover:-translate-y-0.5 hover:bg-white/20">
                View on GitHub
              </button>
            </a>
          </div>
        </div>
      </section>

      <footer className="border-t border-neutral-200 dark:border-neutral-800">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 px-6 py-10 sm:flex-row">
          <div className="flex items-center gap-2">
            <Logo className="h-6 w-6" />
            <span className="font-semibold tracking-tight text-neutral-700 dark:text-neutral-300">
              FinSight
            </span>
            <span className="ml-2 text-sm text-neutral-400">
              Multi-agent financial research
            </span>
          </div>
          <div className="flex items-center gap-5 text-sm text-neutral-500">
            <a href="#demo" className="transition hover:text-neutral-900 dark:hover:text-neutral-100">
              Demo
            </a>
            <a
              href="#features"
              className="transition hover:text-neutral-900 dark:hover:text-neutral-100"
            >
              Features
            </a>
            <a
              href="https://github.com/phanminhtai23/finsight-multi-agent"
              target="_blank"
              className="transition hover:text-neutral-900 dark:hover:text-neutral-100"
            >
              GitHub
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
