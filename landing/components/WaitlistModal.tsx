"use client";

import { useEffect, useEffectEvent, useId, useState } from "react";
import { dispatchWaitlistCountRefresh } from "@/components/WaitlistLiveCount";

type WaitlistModalProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  submitLabel?: string;
  prefillMessage?: string;
};

export default function WaitlistModal({
  open,
  onClose,
  title,
  description,
  submitLabel,
  prefillMessage,
}: WaitlistModalProps) {
  const titleId = useId();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState(prefillMessage ?? "");
  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error" | "already"
  >("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [alreadyMessage, setAlreadyMessage] = useState("");
  const modalTitle = title ?? "Get early access to Gary.2";
  const modalDescription =
    description ?? "Leave your email and we'll reach out as we open access.";
  const modalSubmitLabel = submitLabel ?? "Submit & join the list";

  function resetForm() {
    setName("");
    setEmail("");
    setMessage(prefillMessage ?? "");
    setStatus("idle");
    setErrorMessage("");
    setAlreadyMessage("");
  }

  function handleClose() {
    resetForm();
    onClose();
  }

  const onEscape = useEffectEvent(() => {
    handleClose();
  });

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onEscape();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!open) return null;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setStatus("loading");
    setErrorMessage("");
    try {
      const response = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, message }),
      });
      const data = (await response.json().catch(() => ({}))) as {
        error?: string;
        code?: string;
      };

      if (response.status === 409 && data.code === "already_subscribed") {
        setStatus("already");
        setAlreadyMessage(
          data.error ??
            "You're already on the list with this email. No need to sign up again.",
        );
        return;
      }

      if (!response.ok) {
        setStatus("error");
        setErrorMessage(data.error ?? "Something went wrong");
        return;
      }

      setStatus("success");
      dispatchWaitlistCountRefresh();
    } catch {
      setStatus("error");
      setErrorMessage("Network error - try again in a moment");
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
        onClick={handleClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative z-[1] w-full max-w-md rounded-[20px] bg-[var(--page-bg,#f5f3f0)] p-8 shadow-[0_12px_48px_rgba(0,0,0,0.18),0_0_0_1px_rgba(0,0,0,0.06)]"
      >
        <button
          type="button"
          onClick={handleClose}
          className="absolute right-4 top-4 font-[family-name:var(--px)] text-[11px] text-[var(--ink-mid)] hover:text-[var(--ink)]"
        >
          Close
        </button>

        {status === "success" ? (
          <div className="pt-2 text-center">
            <p
              id={titleId}
              className="mb-3 font-[family-name:var(--px)] text-[15px] text-[var(--ink)]"
            >
              You&apos;re on the list
            </p>
            <p className="font-[family-name:var(--px)] text-[12px] leading-relaxed text-[var(--ink-mid)]">
              We&apos;ll reach out at {email} when there&apos;s news.
            </p>
            <button
              type="button"
              onClick={handleClose}
              className="mt-8 rounded-full bg-[var(--ink)] px-8 py-3 font-[family-name:var(--px)] text-[12px] text-white transition-colors hover:bg-[var(--accent-deep)]"
            >
              Done
            </button>
          </div>
        ) : status === "already" ? (
          <div className="pt-2 text-center">
            <p
              id={titleId}
              className="mb-3 font-[family-name:var(--px)] text-[15px] text-[var(--ink)]"
            >
              Already signed up
            </p>
            <p className="font-[family-name:var(--px)] text-[12px] leading-relaxed text-[var(--ink-mid)]">
              {alreadyMessage}
            </p>
            <button
              type="button"
              onClick={handleClose}
              className="mt-8 rounded-full bg-[var(--ink)] px-8 py-3 font-[family-name:var(--px)] text-[12px] text-white transition-colors hover:bg-[var(--accent-deep)]"
            >
              Got it
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="pt-2">
            <h2
              id={titleId}
              className="mb-1 pr-10 font-[family-name:var(--px)] text-[17px] text-[var(--ink)]"
            >
              {modalTitle}
            </h2>
            <p className="mb-6 font-[family-name:var(--px)] text-[11px] leading-relaxed text-[var(--ink-mid)]">
              {modalDescription}
            </p>

            <label className="mb-4 block">
              <span className="font-[family-name:var(--px)] text-[10px] uppercase tracking-wider text-[var(--ink-mid)]">
                Name
              </span>
              <input
                required
                autoComplete="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="mt-1.5 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 font-[family-name:var(--px)] text-[13px] text-[var(--ink)] outline-none focus:border-[var(--accent-deep)] focus:ring-1 focus:ring-[var(--accent-deep)]/30"
                placeholder="Your name"
              />
            </label>

            <label className="mb-4 block">
              <span className="font-[family-name:var(--px)] text-[10px] uppercase tracking-wider text-[var(--ink-mid)]">
                Email
              </span>
              <input
                required
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-1.5 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 font-[family-name:var(--px)] text-[13px] text-[var(--ink)] outline-none focus:border-[var(--accent-deep)] focus:ring-1 focus:ring-[var(--accent-deep)]/30"
                placeholder="you@company.com"
              />
            </label>

            <label className="mb-6 block">
              <span className="font-[family-name:var(--px)] text-[10px] uppercase tracking-wider text-[var(--ink-mid)]">
                Anything else?{" "}
                <span className="normal-case text-[var(--ink-light,#999)]">
                  (optional)
                </span>
              </span>
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                rows={3}
                className="mt-1.5 w-full resize-y rounded-xl border border-black/10 bg-white px-3 py-2.5 font-[family-name:var(--px)] text-[13px] text-[var(--ink)] outline-none focus:border-[var(--accent-deep)] focus:ring-1 focus:ring-[var(--accent-deep)]/30"
                placeholder="Store type, use case, questions..."
              />
            </label>

            {status === "error" ? (
              <p className="mb-3 font-[family-name:var(--px)] text-[11px] text-red-600">
                {errorMessage}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={status === "loading"}
              className="w-full rounded-full bg-[var(--ink)] py-3.5 font-[family-name:var(--px)] text-[13px] text-white transition-all hover:bg-[var(--accent-deep)] hover:shadow-[0_8px_28px_rgba(124,95,214,0.3)] disabled:opacity-60"
            >
              {status === "loading" ? "Sending..." : modalSubmitLabel}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
