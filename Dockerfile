FROM python:3.12-slim

# ffmpeg: audio transcode. curl/gnupg/git/unzip: install Node.js + Deno and
# fetch the POT provider source. Node.js 20+ is required by the bgutil POT
# provider.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg curl ca-certificates gnupg git unzip \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Deno: yt-dlp's supported JavaScript runtime for solving YouTube's "n"
# signature challenge. Node is only used for the POT provider (it's
# "unsupported" for the challenge solver); without Deno, yt-dlp can't
# decipher format URLs and only storyboard images remain downloadable.
RUN curl -fsSL -o /tmp/deno.zip \
        https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip \
    && unzip /tmp/deno.zip -d /usr/local/bin \
    && rm /tmp/deno.zip \
    && chmod +x /usr/local/bin/deno

# Build the bgutil PO-token provider server. YouTube requires a proof-of-
# origin token from datacenter IPs even with cookies; this Node service mints
# them and yt-dlp's bgutil plugin calls it. Pinned to the same version as the
# pip plugin in requirements.txt so the two stay compatible.
ARG BGUTIL_VERSION=1.3.1
RUN git clone --single-branch --branch ${BGUTIL_VERSION} \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
        /opt/bgutil-ytdlp-pot-provider \
    && cd /opt/bgutil-ytdlp-pot-provider/server \
    && npm ci \
    && npx tsc
ENV BGUTIL_SERVER_HOME=/opt/bgutil-ytdlp-pot-provider/server

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 300 run:app
