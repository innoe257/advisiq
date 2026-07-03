import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a self-contained server bundle for the Docker image (see
  // frontend/Dockerfile) — needed for self-hosting via docker compose, but
  // NOT for Vercel: Vercel has its own deployment format, and setting
  // `standalone` there breaks routing (every route 404s). Vercel sets the
  // VERCEL env var automatically during its builds, so this only applies
  // outside of Vercel.
  ...(process.env.VERCEL ? {} : { output: "standalone" as const }),
};

export default nextConfig;
