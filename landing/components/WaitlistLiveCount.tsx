"use client";

import { useCallback, useEffect, useState } from "react";

const POLL_MS = 30_000;
const REFRESH_EVENT = "reanimate-waitlist-count-refresh";

export function dispatchWaitlistCountRefresh() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(REFRESH_EVENT));
  }
}

export default function WaitlistLiveCount({
  className = "",
}: {
  className?: string;
}) {
  const [count, setCount] = useState<number | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await fetch("/api/waitlist/count", { cache: "no-store" });
      const data = (await r.json()) as { count?: number; error?: string };
      if (!r.ok) {
        setUnavailable(true);
        setCount(null);
        return;
      }
      if (typeof data.count === "number") {
        setCount(data.count);
        setUnavailable(false);
      }
    } catch {
      setUnavailable(true);
      setCount(null);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, POLL_MS);
    const onRefresh = () => {
      load();
    };
    window.addEventListener(REFRESH_EVENT, onRefresh);
    return () => {
      clearInterval(interval);
      window.removeEventListener(REFRESH_EVENT, onRefresh);
    };
  }, [load]);

  if (unavailable || count === null) {
    return (
      <span
        className={`inline-flex items-center justify-center font-[family-name:var(--px)] text-[11px] text-[var(--ink-mid)] opacity-60 ${className}`}
        aria-live="polite"
      >
        <span
          className="inline-block h-2.5 w-20 max-w-full rounded bg-black/[0.08] align-middle"
          aria-hidden
        />
      </span>
    );
  }

  if (count === 0) {
    return (
      <span
        className={`inline-flex items-center gap-2 justify-center font-[family-name:var(--px)] text-[11px] text-[var(--ink-mid)] ${className}`}
        aria-live="polite"
      >
        <LiveDot />
        <span>Be the first on the waitlist</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-2 justify-center font-[family-name:var(--px)] text-[11px] text-[var(--ink-mid)] ${className}`}
      aria-live="polite"
    >
      <LiveDot />
      <span>
        <strong className="text-[var(--ink)] font-normal tabular-nums">
          {count.toLocaleString()}
        </strong>
        {count === 1 ? " person" : " people"} on the waitlist
      </span>
    </span>
  );
}

function LiveDot() {
  return (
    <span className="relative flex h-2 w-2 shrink-0" aria-hidden>
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-35" />
      <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-600" />
    </span>
  );
}
