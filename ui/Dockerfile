# Multi-stage: build the static bundle with Node, then throw Node away and serve the
# files from a tiny nginx image. The final image has no Node, no source, no
# node_modules — ~50MB, and nothing at runtime but a static file server.

# ---- build stage ----
FROM node:20-alpine AS build
WORKDIR /app

# Copy manifests first so `npm install` is cached unless dependencies change.
COPY package.json package-lock.json* ./
# npm ci is stricter and reproducible, but needs a committed package-lock.json.
# Falls back to install on first run before a lockfile exists — commit the lockfile
# afterwards and this becomes a deterministic `npm ci`.
RUN npm ci || npm install

COPY . .
RUN npm run build        # tsc + vite build -> /app/dist

# ---- runtime stage ----
FROM nginx:1.27-alpine

# Anything in /etc/nginx/templates/*.template is envsubst'd by the image's entrypoint
# at container START and written to /etc/nginx/conf.d/. This is what makes the config
# runtime-configurable — see the long note in nginx.conf.template.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Where nginx forwards /api. Overridden per environment:
#   compose -> http://api:8000          k8s -> http://realtime-app:8080
# The default is the Kubernetes one, so the manifests need no extra env var.
ENV API_UPSTREAM=http://realtime-app:8080

# Restrict envsubst to API_* names ONLY. Without this it would also try to expand
# nginx's own runtime variables ($uri, $host, $remote_addr) and produce a broken config.
ENV NGINX_ENVSUBST_FILTER=^API_

# The compiled static files — the only thing that ships from the build stage.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
# nginx:alpine's own entrypoint/CMD handles envsubst + startup; no override needed.