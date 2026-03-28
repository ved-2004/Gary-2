"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

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
  const [settled, setSettled] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await fetch("/api/waitlist/count", { cache: "no-store" });
      const data = (await r.json()) as { count?: number; error?: string };
      setSettled(true);
      if (r.ok && typeof data.count === "number") {
        setCount(data.count);
        return;
      }
      setCount(null);
    } catch {
      setSettled(true);
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

  let label: ReactNode;
  if (!settled) {
    label = <span className="opacity-50">…</span>;
  } else if (count === null) {
    label = <span>Add your email below to join the waitlist.</span>;
  } else if (count === 0) {
    label = <span>Be the first on the waitlist</span>;
  } else {
    label = (
      <span>
        <strong className="text-[var(--ink)] font-normal tabular-nums">
          {count.toLocaleString()}
        </strong>
        {count === 1 ? " person" : " people"} on the waitlist
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center justify-center font-[family-name:var(--px)] text-[11px] text-[var(--ink-mid)] ${className}`}
      aria-live="polite"
    >
      {label}
    </span>
  );
}
