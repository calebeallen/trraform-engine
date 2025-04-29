# ───────────────────────── base image ─────────────────────────
FROM python:3.11-slim
WORKDIR /app

# ─────────────────── runtime directories / deps ───────────────
RUN mkdir -p /app/point_clouds

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ───────────────────── install Supercronic ────────────────────
# Latest releases: https://github.com/aptible/supercronic/releases
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.33/supercronic-linux-amd64 \
    SUPERCRONIC=supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=71b0d58cc53f6bd72cf2f293e09e294b79c666d8

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
 && curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" /usr/local/bin/ \
 && ln -s /usr/local/bin/${SUPERCRONIC} /usr/local/bin/supercronic \
 && apt-get purge -y curl ca-certificates && rm -rf /var/lib/apt/lists/*

# ────────────────────────── app code ──────────────────────────
COPY . .

# plain-text cron file goes at /app/crontab
COPY crontab /app/crontab

# ──────────────────── default container entry ─────────────────
CMD ["supercronic", "/app/crontab"]
