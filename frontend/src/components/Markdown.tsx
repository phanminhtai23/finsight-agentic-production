import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Markdown rendered with explicit Tailwind classes (no typography plugin needed).
export function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: (p) => <p className="mb-2 leading-relaxed last:mb-0" {...p} />,
        ul: (p) => <ul className="mb-2 ml-4 list-disc space-y-1 last:mb-0" {...p} />,
        ol: (p) => <ol className="mb-2 ml-4 list-decimal space-y-1 last:mb-0" {...p} />,
        li: (p) => <li className="leading-relaxed" {...p} />,
        strong: (p) => <strong className="font-semibold" {...p} />,
        em: (p) => <em className="italic" {...p} />,
        a: (p) => (
          <a className="text-indigo-600 hover:underline dark:text-indigo-400" target="_blank" {...p} />
        ),
        h1: (p) => <h1 className="mb-2 mt-1 text-lg font-semibold" {...p} />,
        h2: (p) => <h2 className="mb-2 mt-1 text-base font-semibold" {...p} />,
        h3: (p) => <h3 className="mb-1 mt-1 font-semibold" {...p} />,
        blockquote: (p) => (
          <blockquote
            className="my-2 border-l-2 border-neutral-300 pl-3 text-neutral-500 dark:border-neutral-700"
            {...p}
          />
        ),
        code: (p) => (
          <code
            className="rounded bg-neutral-200/70 px-1 py-0.5 font-mono text-[0.85em] dark:bg-neutral-700/70"
            {...p}
          />
        ),
        table: (p) => (
          <div className="my-2 overflow-x-auto">
            <table className="w-full border-collapse text-sm" {...p} />
          </div>
        ),
        th: (p) => (
          <th
            className="border border-neutral-300 bg-neutral-100 px-2 py-1 text-left font-medium dark:border-neutral-700 dark:bg-neutral-800"
            {...p}
          />
        ),
        td: (p) => <td className="border border-neutral-300 px-2 py-1 dark:border-neutral-700" {...p} />,
      }}
    >
      {children}
    </ReactMarkdown>
  );
}
