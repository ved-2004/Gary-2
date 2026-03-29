"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useState } from "react";
import SimulationReplayClient from "@/components/SimulationReplayClient";
import WaitlistLiveCount from "@/components/WaitlistLiveCount";
import WaitlistModal from "@/components/WaitlistModal";
import { replayCatalog } from "@/lib/replay-catalog";

const PixelBlast = dynamic(() => import("@/components/PixelBlast"), {
  ssr: false,
});

export default function Home() {
  const [waitlistOpen, setWaitlistOpen] = useState(false);

  return (
    <div className="ld">
      <WaitlistModal
        open={waitlistOpen}
        onClose={() => setWaitlistOpen(false)}
      />

      <div className="ld-hero-stack">
        <div className="ld-hero-shader" aria-hidden>
          <PixelBlast
            variant="square"
            pixelSize={4}
            color="#B19EEF"
            patternScale={2}
            patternDensity={1}
            enableRipples
            rippleSpeed={0.4}
            rippleThickness={0.12}
            rippleIntensityScale={1.5}
            speed={0.5}
            edgeFade={0.25}
            transparent
            autoPauseOffscreen={false}
          />
        </div>

        <nav className="ld-nav">
          <div className="ld-nav-pill">
            <span className="ld-nav-wordmark">Gary.2</span>
            <div className="ld-nav-right">
              <a href="#live-replay" className="ld-nav-link">
                Watch replay
              </a>
              <button
                type="button"
                className="ld-nav-enter border-0 cursor-pointer font-inherit"
                onClick={() => setWaitlistOpen(true)}
              >
                Get updates&nbsp;&rsaquo;
              </button>
            </div>
          </div>
        </nav>

        <section className="ld-hero">
          <div className="ld-hero-content">
            <p className="ld-hero-eyebrow">The AI-native store lab</p>
            <h1 className="ld-hero-h1">
              Sketch two layouts.
              <br />
              <span className="ld-hero-h1-em">See which one sells.</span>
            </h1>
            <p className="ld-hero-sub">
              LLM shoppers roam your grid like it&apos;s opening day. Dwell time, baskets, a clean A/B verdict before you touch the floor.
            </p>
            <p className="mx-auto mb-3 mt-2 max-w-[520px]">
              <WaitlistLiveCount className="w-full" />
            </p>
            <button
              type="button"
              className="ld-hero-cta border-0 cursor-pointer font-inherit"
              onClick={() => setWaitlistOpen(true)}
            >
              Get updates by email&nbsp;&rsaquo;
            </button>
            <div className="mt-4">
              <a
                href="#live-replay"
                className="font-[family-name:var(--px)] text-[12px] text-[var(--ink)] underline decoration-[rgba(124,95,214,0.35)] underline-offset-4 transition hover:text-[var(--accent-deep)]"
              >
                Watch the simulation replay
              </a>
            </div>
          </div>
        </section>
      </div>

      <section
        id="live-replay"
        className="ld-showcase-anim mx-auto max-w-[92rem] overflow-hidden px-4 pb-12 sm:px-6 lg:px-8"
      >
        <SimulationReplayClient replays={replayCatalog} />
      </section>

      <section className="flex flex-col items-center px-6 py-24 text-center">
        <h2 className="mb-4 font-[family-name:var(--px)] text-[clamp(24px,4vw,44px)] leading-tight text-[var(--ink)]">
          Ready to pick the winning layout?
        </h2>
        <p className="mb-8 max-w-md font-[family-name:var(--px)] text-[12px] leading-relaxed text-[var(--ink-mid)]">
          Get notified when we open early access. Leave your email and we&apos;ll
          keep you in the loop.
        </p>
        <button
          type="button"
          onClick={() => setWaitlistOpen(true)}
          className="rounded-full border-0 bg-[var(--ink)] px-10 py-4 font-[family-name:var(--px)] text-[13px] text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[var(--accent-deep)] hover:shadow-[0_8px_28px_rgba(124,95,214,0.3)]"
        >
          Get updates by email&nbsp;&rsaquo;
        </button>
        <Link
          href="/replay"
          className="mt-4 font-[family-name:var(--px)] text-[12px] text-[var(--ink)] underline decoration-[rgba(124,95,214,0.35)] underline-offset-4 transition hover:text-[var(--accent-deep)]"
        >
          Open the replay in its own page
        </Link>
      </section>
    </div>
  );
}
