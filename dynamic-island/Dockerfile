# syntax=docker/dockerfile:1

# --- Build: static Vite/React bundle ---
# Note: this containerizes the web build of the demo UI only. The Tauri/Rust
# desktop shell (src-tauri/) produces a native binary and is not something
# that makes sense to run inside a container, so it's not part of this image.
FROM node:22-slim AS build

RUN corepack enable && corepack prepare pnpm@12 --activate

WORKDIR /app

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

# --- Serve: static files via nginx ---
FROM nginx:1.29-alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
