"use client";

import { useEffect, useId, useState } from "react";
import { dispatchWaitlistCountRefresh } from "@/components/WaitlistLiveCount";

type WaitlistModalProps = {
  open: boolean;
  onClose: () => void;
};

export default function WaitlistModal({ open, onClose }: WaitlistModalProps) {
  const titleId = useId();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error" | "already"
  >("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [alreadyMessage, setAlreadyMessage] = useState("");

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  useEffect(() => {
    if (!open) {
      setName("");
      setEmail("");
      setMessage("");
      setStatus("idle");
      setErrorMessage("");
      setAlreadyMessage("");
    }
  }, [open]);

  if (!open) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, message }),
      });
      const data = (await res.json().catch(() => ({}))) as {
        error?: string;
        code?: string;
      };
      if (res.status === 409 && data.code === "already_subscribed") {
        setStatus("already");
        setAlreadyMessage(
          data.error ??
            "You're already on the list with this email. No need to sign up again."
        );
        return;
      }
      if (!res.ok) {
        setStatus("error");
        setErrorMessage(data.error ?? "Something went wrong");
        return;
      }
      setStatus("success");
      dispatchWaitlistCountRefresh();
    } catch {
      setStatus("error");
      setErrorMessage("Network error — try again in a moment");
    }
  }

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-4"
      role="presentation"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/45 backdrop-blur-[2px]"
        aria-label="Close dialog"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative z-[1] w-full max-w-md rounded-[20px] bg-[var(--page-bg,#f5f3f0)] p-8 shadow-[0_12px_48px_rgba(0,0,0,0.18),0_0_0_1px_rgba(0,0,0,0.06)]"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 font-[family-name:var(--px)] text-[11px] text-[var(--ink-mid)] hover:text-[var(--ink)]"
        >
          Close
        </button>

        {status === "success" ? (
          <div className="pt-2 text-center">
            <p
              id={titleId}
              className="font-[family-name:var(--px)] text-[15px] text-[var(--ink)] mb-3"
            >
              You&apos;re on the list
            </p>
            <p className="font-[family-name:var(--px)] text-[12px] text-[var(--ink-mid)] leading-relaxed">
              We&apos;ll reach out at {email} when there&apos;s news.
            </p>
            <button
              type="button"
              onClick={onClose}
              className="mt-8 font-[family-name:var(--px)] text-[12px] text-white bg-[var(--ink)] px-8 py-3 rounded-full hover:bg-[var(--accent-deep)] transition-colors"
            >
              Done
            </button>
          </div>
        ) : status === "already" ? (
          <div className="pt-2 text-center">
            <p
              id={titleId}
              className="font-[family-name:var(--px)] text-[15px] text-[var(--ink)] mb-3"
            >
              Already signed up
            </p>
            <p className="font-[family-name:var(--px)] text-[12px] text-[var(--ink-mid)] leading-relaxed">
              {alreadyMessage}
            </p>
            <button
              type="button"
              onClick={onClose}
              className="mt-8 font-[family-name:var(--px)] text-[12px] text-white bg-[var(--ink)] px-8 py-3 rounded-full hover:bg-[var(--accent-deep)] transition-colors"
            >
              Got it
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="pt-2">
            <h2
              id={titleId}
              className="font-[family-name:var(--px)] text-[17px] text-[var(--ink)] mb-1 pr-10"
            >
              Get updates from ReAnimate
            </h2>
            <p className="font-[family-name:var(--px)] text-[11px] text-[var(--ink-mid)] mb-6 leading-relaxed">
              Leave your email and we&apos;ll notify you as we ship.
            </p>

            <label className="block mb-4">
              <span className="font-[family-name:var(--px)] text-[10px] uppercase tracking-wider text-[var(--ink-mid)]">
                Name
              </span>
              <input
                required
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 font-[family-name:var(--px)] text-[13px] text-[var(--ink)] outline-none focus:border-[var(--accent-deep)] focus:ring-1 focus:ring-[var(--accent-deep)]/30"
                placeholder="Your name"
              />
            </label>

            <label className="block mb-4">
              <span className="font-[family-name:var(--px)] text-[10px] uppercase tracking-wider text-[var(--ink-mid)]">
                Email
              </span>
              <input
                required
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 font-[family-name:var(--px)] text-[13px] text-[var(--ink)] outline-none focus:border-[var(--accent-deep)] focus:ring-1 focus:ring-[var(--accent-deep)]/30"
                placeholder="you@company.com"
              />
            </label>

            <label className="block mb-6">
              <span className="font-[family-name:var(--px)] text-[10px] uppercase tracking-wider text-[var(--ink-mid)]">
                Anything else?{" "}
                <span className="normal-case text-[var(--ink-light,#999)]">
                  (optional)
                </span>
              </span>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={3}
                className="mt-1.5 w-full resize-y rounded-xl border border-black/10 bg-white px-3 py-2.5 font-[family-name:var(--px)] text-[13px] text-[var(--ink)] outline-none focus:border-[var(--accent-deep)] focus:ring-1 focus:ring-[var(--accent-deep)]/30"
                placeholder="Store type, use case, questions…"
              />
            </label>

            {status === "error" ? (
              <p className="font-[family-name:var(--px)] text-[11px] text-red-600 mb-3">
                {errorMessage}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={status === "loading"}
              className="w-full font-[family-name:var(--px)] text-[13px] text-white bg-[var(--ink)] py-3.5 rounded-full transition-all hover:bg-[var(--accent-deep)] hover:shadow-[0_8px_28px_rgba(124,95,214,0.3)] disabled:opacity-60"
            >
              {status === "loading" ? "Sending…" : "Submit & join the list"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
