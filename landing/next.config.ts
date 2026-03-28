import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Three.js + postprocessing ship modern ESM; transpiling avoids broken prod bundles.
  transpilePackages: ["three", "postprocessing"],
};

export default nextConfig;
