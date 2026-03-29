"use client";

import { useEffect, useEffectEvent, useId } from "react";

type AskModalProps = {
  open: boolean;
  onClose: () => void;
  onPrimaryAction: () => void;
};

export default function AskModal({
  open,
  onClose,
  onPrimaryAction,
}: AskModalProps) {
  const titleId = useId();

  const onEscape = useEffectEvent(() => {
    onClose();
  });

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onEscape();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-[190] flex items-end justify-center p-4 sm:items-center"
      role="presentation"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/20 backdrop-blur-[1.5px]"
        aria-label="Close ask dialog"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative z-[1] w-full max-w-[30rem] overflow-hidden rounded-[24px] border border-[rgba(124,95,214,0.12)] bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(247,243,238,0.98))] p-5 shadow-[0_20px_50px_rgba(17,17,17,0.14)] sm:p-6"
      >
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-6 top-0 h-24 rounded-b-[28px] bg-[radial-gradient(circle_at_top,rgba(177,158,239,0.22),transparent_72%)]"
        />
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 font-[family-name:var(--px)] text-[11px] text-[var(--ink-mid)] transition hover:text-[var(--ink)]"
        >
          Close
        </button>

        <div className="relative">
          <div className="inline-flex rounded-full border border-[rgba(124,95,214,0.16)] bg-[rgba(124,95,214,0.08)] px-3 py-1.5 font-[family-name:var(--px)] text-[10px] uppercase tracking-[0.16em] text-[var(--accent-deep)]">
            Ask
          </div>
          <h2
            id={titleId}
            className="mt-4 max-w-[22rem] font-[family-name:var(--px)] text-[18px] leading-[1.45] text-[var(--ink)] sm:text-[20px]"
          >
            If you love what we&apos;re building, our ask is simple.
          </h2>
          <p className="mt-4 text-[13px] leading-7 text-[var(--ink-mid)]">
            We&apos;re looking for introductions to retail clients who would be open
            to starting a pilot with Gary.2.
          </p>

          <div className="mt-5 rounded-[18px] border border-black/8 bg-white/82 px-4 py-4">
            <div className="font-[family-name:var(--px)] text-[10px] uppercase tracking-[0.14em] text-black/42">
              Best fit
            </div>
            <div className="mt-2 text-[13px] leading-7 text-black/62">
              Brands, store operators, merchandising teams, or anyone who owns
              layout decisions and can help kick off a pilot conversation.
            </div>
          </div>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={onPrimaryAction}
              className="rounded-full bg-[var(--ink)] px-5 py-3 font-[family-name:var(--px)] text-[11px] text-white transition hover:-translate-y-0.5 hover:bg-[var(--accent-deep)] hover:shadow-[0_10px_26px_rgba(124,95,214,0.24)]"
            >
              I can help with an intro
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-black/10 bg-white/70 px-5 py-3 font-[family-name:var(--px)] text-[11px] text-[var(--ink)] transition hover:border-[var(--accent-deep)]/30 hover:text-[var(--accent-deep)]"
            >
              Maybe later
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
