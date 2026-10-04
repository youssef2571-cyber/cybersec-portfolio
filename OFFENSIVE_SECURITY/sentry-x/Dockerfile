# syntax=docker/dockerfile:1
# SENTRY-X - production image
# Build:  docker build -t sentryx:0.1.0 .
# Run:    docker run --rm -it --env-file .env sentryx:0.1.0 sentryx --help
#
# Base image and every apt package below were installed and smoke-tested
# (nmap --version, whois --version, nikto -Version, whatweb --version,
# dig -v) against ubuntu:24.04 during development - see RUNBOOK.md.

FROM ubuntu:24.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.12 \
        python3-pip \
        python3-venv \
        nmap \
        whois \
        whatweb \
        dnsutils \
        curl \
        nikto \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libgdk-pixbuf2.0-0 \
        libffi8 \
        shared-mime-info \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash sentryx
WORKDIR /app

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir -e .

COPY migrations/ migrations/

RUN chown -R sentryx:sentryx /app
USER sentryx

ENTRYPOINT ["sentryx"]
CMD ["--help"]
