const LABELS: Record<string, string> = { free: "Free", pro: "Pro", pro_max: "Pro Max" };
const STYLES: Record<string, string> = {
  free: "border border-neutral-300 text-neutral-500 dark:border-neutral-700 dark:text-neutral-400",
  pro: "border border-indigo-300 bg-indigo-50 text-indigo-600 dark:border-indigo-800 dark:bg-indigo-950 dark:text-indigo-300",
  pro_max:
    "border border-transparent bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-sm",
};

export function TierBadge({ tier, className = "" }: { tier: string; className?: string }) {
  const key = tier in LABELS ? tier : "free";
  return (
    <span
      className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${STYLES[key]} ${className}`}
    >
      {LABELS[key]}
    </span>
  );
}
