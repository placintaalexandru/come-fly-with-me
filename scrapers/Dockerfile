FROM python:3.13.0b4-slim as python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYSETUP_PATH="/opt/pysetup"

ENV PATH="$PYSETUP_PATH/.venv/bin:$PATH"


FROM python-base as builder-base

ENV POETRY_VESION="1.5.0" \
    # Will create a .venv directory with dependencies where `poetry install` is run
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_HOME="/opt/poetry"

ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR $PYSETUP_PATH

COPY scrapers/poetry.lock scrapers/pyproject.toml ./

RUN set -eux; \
    apt-get update && apt-get install -y --no-install-recommends wget; \
    wget -qO- https://install.python-poetry.org | python3 -; \
    poetry install --no-interaction --without dev; \
    # Remove .venv's pip
    pip uninstall -y pip


FROM python-base as release

ARG USER=scraper

COPY --from=builder-base "$PYSETUP_PATH/.venv" "$PYSETUP_PATH/.venv"

RUN set -eux; \
    adduser --no-create-home --disabled-password "${USER}"; \
    apt-get update && apt-get install -y --no-install-recommends cron; \
    chmod gu+rw /var/run && chmod gu+s /usr/sbin/cron; \
    # Remove python-base's pip
    pip uninstall -y pip; \
    rm -rf /var/lib/apt/lists/*;

COPY scrapers/scrapers "/${USER}/scrapers"
COPY scrapers/scrapy.cfg "/${USER}"

RUN chown -R "${USER}:${USER}" "/$USER"

USER "${USER}"

WORKDIR "/${USER}"

ENTRYPOINT ["/bin/bash", "-c", "tail -f /dev/null"]
