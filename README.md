# CI/CD Pipeline for a Containerized App

A zero-dependency Python web app delivered through a real CI/CD pipeline:
GitHub Actions builds, tests, and ships the Docker image to GitHub Packages
(GHCR). The pipeline logic is fully demonstrated offline.

## The app (`app/`)

Simple stdlib web server (no pip installs at runtime — a hermetic build):

| Route      | Response                                          |
| ---------- | ------------------------------------------------- |
| `/`        | `{"message": "hello", "total_requests": N}`       |
| `/healthz` | `{"status": "ok"}` (health check target)          |
| `/version` | `{"version": "1.0.0"}` (overridable via build arg)|

## The pipeline (`.github/workflows/`)

`ci.yml` — on every push/PR:
1. checkout, setup Python 3.12
2. `pip install pytest` → `pytest tests/ -v`
3. **build the image with tests running inside the build stage**
4. login to GHCR → push `ghcr.io/goose006567/cicd-app:ci-$sha`

`deploy.yml` — on push to `main`, after CI:
1. tag the release image `:latest` + `:$sha`
2. push both to GHCR
3. `rollout` job = rolling update on the target host

## Offline validation (no GitHub, no Docker needed)

```bash
python3.12 -m venv .venv
.venv/bin/pip install pytest PyYAML
.venv/bin/python local/simulate_ci.py
```

This replays the pipeline locally:
1. parses and prints both workflow files (structure check)
2. runs the **exact** command `ci.yml` runs — `pytest tests/ -v` (5 tests)
3. attempts the real `docker build` if a daemon is available

Expected result: `5 passed`, workflow jobs/steps printed, build step
gracefully noted as deferred to GitHub runners.

## Run the app locally

```bash
python3.12 app/app.py            # :8080
curl localhost:8080/healthz      # {"status": "ok"}
curl localhost:8080/version      # {"version": "1.0.0"}
```

## Deploy for real

1. Push this repo to GitHub (workflows include GHCR push on `main`).
2. Open **Actions** — CI runs automatically; `main` gets a release image.
3. Pull it anywhere: `docker run -p 8080:8080 ghcr.io/goose006567/cicd-app:latest`

## Why "tests run inside the Docker build"?

The multi-stage `Dockerfile` runs `pytest` in the `build` stage and copies only
the app into the slim `runtime` stage. A red test **fails the image build** —
one of the strongest guarantees CI/CD can give: unbuildable == untested.
