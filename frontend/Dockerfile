# Deployed on Vercel in practice (zero-config for Next.js), but this image
# exists so the whole stack can also be self-hosted via docker compose, and
# to satisfy the "multi-stage Dockerfile for frontend" requirement directly.

FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# The backend URL is baked in at build time since NEXT_PUBLIC_* vars are
# inlined into the client bundle, not read at container startup.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN npm run build

# ---- runtime: only the standalone server output, non-root ----
FROM node:22-slim AS production
WORKDIR /app
# node:22-slim already ships a non-root "node" user at uid 1000.
COPY --from=builder /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
USER node
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
