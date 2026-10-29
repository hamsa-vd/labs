# Tectonic LaTeX compiler as an isolated service (RG-035, decision D2).
#
# The .tex compiled here is untrusted user input. \write18, \input{/etc/passwd}
# and \openout are all real escapes, so this never runs in the API process.
# Hardening lives in three places and all three are required: the --untrusted
# flag below, the container constraints in docker-compose.dev.yml (read-only
# root, tmpfs scratch, dropped capabilities, non-root user, memory and CPU
# caps), and the macro denylist the API applies before a request ever arrives.

FROM debian:bookworm-slim AS tectonic

ARG TECTONIC_VERSION=0.17.0
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl; \
    case "$(dpkg --print-architecture)" in \
      amd64) arch=x86_64 ;; \
      arm64) arch=aarch64 ;; \
      *) echo "unsupported architecture: $(dpkg --print-architecture)" >&2; exit 1 ;; \
    esac; \
    curl -fsSL -o /tmp/tectonic.tar.gz \
      "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-${arch}-unknown-linux-musl.tar.gz"; \
    tar -xzf /tmp/tectonic.tar.gz -C /usr/local/bin tectonic; \
    chmod +x /usr/local/bin/tectonic; \
    rm -rf /tmp/tectonic.tar.gz /var/lib/apt/lists/*

# Pre-warm the package cache into the image by compiling a document that pulls
# the packages the seeded templates use. Runtime network egress can then be
# blocked entirely, which is the point: a compile must not be able to reach out.
COPY warmup.tex /warmup/warmup.tex
RUN set -eux; \
    cd /warmup; \
    TECTONIC_CACHE_DIR=/opt/tectonic-cache tectonic -X compile --untrusted --keep-logs warmup.tex \
      || { echo "warmup compile failed"; cat warmup.log 2>/dev/null; exit 1; }; \
    rm -rf /warmup


FROM debian:bookworm-slim

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends python3 python3-pip ca-certificates; \
    rm -rf /var/lib/apt/lists/*; \
    pip3 install --break-system-packages --no-cache-dir 'fastapi>=0.115' 'uvicorn[standard]>=0.32' 'pydantic>=2.9'; \
    useradd --uid 10001 --create-home --shell /usr/sbin/nologin tex

COPY --from=tectonic /usr/local/bin/tectonic /usr/local/bin/tectonic
COPY --from=tectonic /opt/tectonic-cache /opt/tectonic-cache
COPY app.py parse_log.py /srv/
COPY healthcheck /usr/local/bin/healthcheck

RUN chmod +x /usr/local/bin/healthcheck && chown -R 10001:10001 /opt/tectonic-cache

ENV TECTONIC_CACHE_DIR=/opt/tectonic-cache \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER 10001:10001
WORKDIR /srv
EXPOSE 8080
CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
