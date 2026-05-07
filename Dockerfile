ARG PYTHON_VERSION=3.12-slim

FROM python:${PYTHON_VERSION} AS python

FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=requirements

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY ./${BUILD_ENVIRONMENT}.txt .

RUN pip wheel --wheel-dir /usr/src/app/wheels \
    -r ${BUILD_ENVIRONMENT}.txt

FROM python AS django-stage

ARG BUILD_ENVIRONMENT=requirements
ARG APP_HOME=/home/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN addgroup --system django \
    && adduser --system --ingroup django django

RUN apt-get update && apt-get install --no-install-recommends -y \
    libpq-dev \
    && apt-get purge -y --auto-remove \
        -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-build-stage /usr/src/app/wheels /wheels/

RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
    && rm -rf /wheels/

COPY --chown=django:django . ${APP_HOME}

USER django

WORKDIR ${APP_HOME}

CMD ["python", "main.py"]