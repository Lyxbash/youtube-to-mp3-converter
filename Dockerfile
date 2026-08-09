FROM python:3.12-slim

# ffmpeg: audio transcode. curl/gnupg/git: install Node.js and fetch the POT
# provider source. Node.js 22 serves double duty: it runs the bgutil POT
# provider AND is yt-dlp's JS runtime for solving YouTube's "n" signature
# challenge (which requires Node >= 22.0.0; Node 20 is rejected as
# "unsupported", leaving only undownloadable storyboard formats). Using Node
# for both avoids installing a second runtime (Deno), whose presence made the
# bgutil plugin probe a slow Deno code path that timed out.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg curl ca-certificates gnupg git \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

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
