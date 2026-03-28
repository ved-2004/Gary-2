import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Allow HMR when the dev server is reached via a public host (reverse proxy / tunnel). */
  allowedDevOrigins: ["gary2.adityakotha.xyz"],
};

export default nextConfig;
