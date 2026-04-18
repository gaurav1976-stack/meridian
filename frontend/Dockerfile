# Meridian Airport PMO suite — frontend (Next.js 14) production image.
# (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
# Proprietary — unauthorised copying, distribution, modification or use prohibited.
#
# Multi-stage build:
#   1. deps   — install all npm deps against package.json only (cache-friendly)
#   2. build  — copy source, run `next build` producing .next/standalone
#   3. runner — slim node:20-alpine image serving the standalone output
#
# `output: "standalone"` in next.config.mjs is what makes the final image
# small enough to fit in Render's 512 MB free-tier budget.
#
# For local dev the root docker-compose.yml overrides CMD to `npm run dev`
# and bind-mounts the source tree; this Dockerfile is the artefact for Render.

# --- 1. deps ---------------------------------------------------------------
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

# --- 2. build --------------------------------------------------------------
FROM node:20-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Public API URL must be inlined into the client bundle at build time. Render
# overrides this via the service env; default points at the local compose
# stack so the image still works for a stand-alone `docker build && docker run`.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

RUN npm run build

# --- 3. runner -------------------------------------------------------------
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Non-root user — Render (and most managed platforms) prefer this.
RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 nextjs

COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static    ./.next/static
COPY --from=build --chown=nextjs:nodejs /app/public          ./public

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
