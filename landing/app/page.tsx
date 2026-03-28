"use client";

import Image from "next/image";
import dynamic from "next/dynamic";
import { useState } from "react";
import WaitlistModal from "@/components/WaitlistModal";

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

      <nav className="ld-nav">
        <div className="ld-nav-pill">
          <span className="ld-nav-wordmark">ReAnimate.live</span>
          <div className="ld-nav-right">
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
        <div className="ld-hero-shader">
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
          />
        </div>

        <div className="ld-hero-content">
          <p className="ld-hero-eyebrow">The AI-native store lab</p>
          <h1 className="ld-hero-h1">
            Sketch two layouts.
            <br />
            <span className="ld-hero-h1-em">See which one sells.</span>
          </h1>
          <p className="ld-hero-sub">
            LLM shoppers roam your grid like it&apos;s opening day.
            <br />
            Dwell time, baskets, a clean A/B verdict—before you touch the floor.
          </p>
          <button
            type="button"
            className="ld-hero-cta border-0 cursor-pointer font-inherit"
            onClick={() => setWaitlistOpen(true)}
          >
            Get updates by email&nbsp;&rsaquo;
          </button>
        </div>
      </section>

      <section className="pb-12 ld-showcase-anim max-w-[80%] mx-auto">
        <div className="relative rounded-[20px] overflow-hidden bg-[#1a1a2e] shadow-[0_2px_4px_rgba(0,0,0,0.04),0_12px_40px_rgba(0,0,0,0.10),0_0_0_1px_rgba(0,0,0,0.04)]">
          <Image
            src="/building.jpg"
            alt="ReAnimate retail floor grid simulation"
            width={1600}
            height={700}
            className="block w-full aspect-[16/7] object-cover object-[center_35%]"
            draggable={false}
            priority
          />

          <div className="absolute inset-0 flex items-center justify-center">
            <div className="frosted-glass px-12 py-8 max-w-xl text-center">
              <p className="font-[family-name:var(--px)] text-[clamp(18px,2.8vw,30px)] text-white leading-snug tracking-tight">
                Not a focus group. A living floor plan.
              </p>
              <p className="font-[family-name:var(--px)] text-[clamp(10px,1.2vw,13px)] text-white/70 mt-3 leading-relaxed">
                Every run scores the route, the pause, the basket—Layout A vs B,
                spelled out in the chart.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="flex flex-col items-center text-center py-24 px-6">
        <h2 className="font-[family-name:var(--px)] text-[clamp(24px,4vw,44px)] text-[var(--ink)] leading-tight mb-4">
          Ready to pick the winning layout?
        </h2>
        <p className="font-[family-name:var(--px)] text-[12px] text-[var(--ink-mid)] mb-8 max-w-md leading-relaxed">
          Get notified when we open early access—leave your email and we&apos;ll
          keep you in the loop.
        </p>
        <button
          type="button"
          onClick={() => setWaitlistOpen(true)}
          className="font-[family-name:var(--px)] text-[13px] text-white bg-[var(--ink)] px-10 py-4 rounded-full border-0 cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:bg-[var(--accent-deep)] hover:shadow-[0_8px_28px_rgba(124,95,214,0.3)]"
        >
          Get updates by email&nbsp;&rsaquo;
        </button>
      </section>
    </div>
  );
}
