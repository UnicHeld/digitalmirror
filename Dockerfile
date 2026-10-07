ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        coreutils dbus libglib2.0-bin systemd \
        x11-utils x11-xserver-utils xdotool xprintidle \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 digitalmirror \
    && useradd --uid 1000 --gid digitalmirror --no-create-home digitalmirror \
    && mkdir -p /run/host/user

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/

FROM base AS runtime
RUN python -m pip install --no-cache-dir .
USER 1000:1000
CMD ["digitalmirror", "doctor"]

FROM base AS development
COPY . .
RUN python -m pip install --no-cache-dir 'setuptools>=68' wheel \
    && python -m pip install --no-cache-dir -e '.[dev]'
ENV RUFF_CACHE_DIR=/tmp/ruff-cache \
    MYPY_CACHE_DIR=/tmp/mypy-cache
USER 1000:1000
CMD ["sh", "scripts/check"]
