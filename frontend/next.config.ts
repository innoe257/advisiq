import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a self-contained server bundle (only the files actually needed
  // at runtime) — Vercel doesn't need this, but it's what makes the Docker
  // image below small and self-sufficient for self-hosting via docker compose.
  output: "standalone",
};

export default nextConfig;
