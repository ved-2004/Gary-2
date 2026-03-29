"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useState } from "react";
import AskModal from "@/components/AskModal";
import SimulationReplayClient from "@/components/SimulationReplayClient";
import WaitlistLiveCount from "@/components/WaitlistLiveCount";
import WaitlistModal from "@/components/WaitlistModal";
import { replayCatalog } from "@/lib/replay-catalog";

const PixelBlast = dynamic(() => import("@/components/PixelBlast"), {
  ssr: false,
});

export default function Home() {
  const [askOpen, setAskOpen] = useState(false);
  const [waitlistOpen, setWaitlistOpen] = useState(false);
  const [waitlistMode, setWaitlistMode] = useState<"default" | "intro">(
    "default",
  );

  function openDefaultWaitlist() {
    setAskOpen(false);
    setWaitlistMode("default");
    setWaitlistOpen(true);
  }

  function openIntroWaitlist() {
    setAskOpen(false);
    setWaitlistMode("intro");
    setWaitlistOpen(true);
  }

  return (
    <div className="ld">
      <AskModal
        open={askOpen}
        onClose={() => setAskOpen(false)}
        onPrimaryAction={openIntroWaitlist}
      />
      <WaitlistModal
        key={`${waitlistMode}-${waitlistOpen ? "open" : "closed"}`}
        open={waitlistOpen}
        onClose={() => setWaitlistOpen(false)}
        title={
          waitlistMode === "intro"
            ? "Help us start a retail pilot"
            : undefined
        }
        description={
          waitlistMode === "intro"
            ? "If you can introduce Gary.2 to retail clients who might pilot the product, leave your details here and tell us who you have in mind."
            : undefined
        }
        submitLabel={
          waitlistMode === "intro" ? "Send the intro lead" : undefined
        }
        prefillMessage={
          waitlistMode === "intro"
            ? "I can introduce Gary.2 to retail clients who may be open to a pilot."
            : undefined
        }
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
                See the demo
              </a>
              <button
                type="button"
                className="ld-nav-enter border-0 cursor-pointer font-inherit"
                onClick={openDefaultWaitlist}
              >
                Get early access&nbsp;&rsaquo;
              </button>
            </div>
          </div>
        </nav>

        <section className="ld-hero">
          <div className="ld-hero-content">
            <p className="ld-hero-eyebrow">Digital twins for retail</p>
            <h1 className="ld-hero-h1">
              Predict what shoppers will buy.
              <br />
              <span className="ld-hero-h1-em">Before the store exists.</span>
            </h1>
            <p className="mx-auto mb-3 mt-2 max-w-[520px]">
              <WaitlistLiveCount className="w-full" />
            </p>
            <button
              type="button"
              className="ld-hero-cta border-0 cursor-pointer font-inherit"
              onClick={openDefaultWaitlist}
            >
              Get early access&nbsp;&rsaquo;
            </button>
            <div className="mt-4">
              <a
                href="#live-replay"
                className="font-[family-name:var(--px)] text-[12px] text-[var(--ink)] underline decoration-[rgba(124,95,214,0.35)] underline-offset-4 transition hover:text-[var(--accent-deep)]"
              >
                See the AI shoppers in action
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
          Build less. Simulate more.
        </h2>
        <p className="mb-8 max-w-md font-[family-name:var(--px)] text-[12px] leading-relaxed text-[var(--ink-mid)]">
          Join early access to test layouts, merchandising moves, and shopper
          behavior inside Gary.2 before anything goes live in the real world.
        </p>
        <p className="mb-3 max-w-[520px]">
          <WaitlistLiveCount className="w-full" />
        </p>
        <button
          type="button"
          onClick={() => setAskOpen(true)}
          className="rounded-full border-0 bg-[var(--ink)] px-10 py-4 font-[family-name:var(--px)] text-[13px] text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[var(--accent-deep)] hover:shadow-[0_8px_28px_rgba(124,95,214,0.3)]"
        >
          I can help with an intro&nbsp;&rsaquo;
        </button>
        <Link
          href="/replay"
          className="mt-4 font-[family-name:var(--px)] text-[12px] text-[var(--ink)] underline decoration-[rgba(124,95,214,0.35)] underline-offset-4 transition hover:text-[var(--accent-deep)]"
        >
          Open the full replay demo
        </Link>
      </section>
    </div>
  );
}
