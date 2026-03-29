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
      const response = await fetch("/api/waitlist/count", { cache: "no-store" });
      const data = (await response.json()) as { count?: number; error?: string };
      setSettled(true);

      if (response.ok && typeof data.count === "number") {
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
    const kickoff = window.setTimeout(() => {
      void load();
    }, 0);
    const interval = window.setInterval(() => {
      void load();
    }, POLL_MS);
    const onRefresh = () => {
      void load();
    };

    window.addEventListener(REFRESH_EVENT, onRefresh);
    return () => {
      window.clearTimeout(kickoff);
      window.clearInterval(interval);
      window.removeEventListener(REFRESH_EVENT, onRefresh);
    };
  }, [load]);

  const outerClass = `inline-flex items-center justify-center font-[family-name:var(--px)] text-[11px] text-[var(--ink-mid)] ${className}`;

  let label: ReactNode;
  if (!settled) {
    label = <span className="opacity-50">...</span>;
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
    <span className={outerClass} aria-live="polite">
      {label}
    </span>
  );
}
