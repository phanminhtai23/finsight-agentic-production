import { useId } from "react";

/** FinSight logo mark — finance (rising chart) + insight (focal node). */
export function Logo({ className = "h-8 w-8" }: { className?: string }) {
  const id = useId();
  return (
    <svg viewBox="0 0 48 48" fill="none" className={className} aria-label="FinSight">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6366F1" />
          <stop offset="1" stopColor="#8B5CF6" />
        </linearGradient>
      </defs>
      <rect width="48" height="48" rx="12" fill={`url(#${id})`} />
      <path
        d="M11 31 L20 24 L27 28 L37 14"
        stroke="white"
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeOpacity="0.95"
      />
      <circle cx="37" cy="14" r="7" stroke="white" strokeWidth="1.4" strokeOpacity="0.4" />
      <circle cx="37" cy="14" r="4.2" fill="white" />
    </svg>
  );
}
