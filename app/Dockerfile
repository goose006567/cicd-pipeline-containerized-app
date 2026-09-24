# Build stage: run the test suite inside the build.
FROM python:3.12-slim AS build
WORKDIR /src
COPY app/requirements-dev.txt ./app/requirements-dev.txt
COPY app ./app
COPY tests ./tests
RUN pip install --no-cache-dir -r app/requirements-dev.txt \
    && python -m pytest tests/ -q

# Runtime stage: slim image with test artifacts stripped.
FROM python:3.12-slim AS runtime
ARG APP_VERSION
ENV PYTHONUNBUFFERED=1 APP_VERSION=${APP_VERSION:-1.0.0}
WORKDIR /srv
COPY app ./app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)"
CMD ["python", "app/app.py"]
