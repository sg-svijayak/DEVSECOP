# Todo App

FastAPI + SQLite backend with a tiny static UI.

```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # http://localhost:8000
pytest
```

## Pipeline (`.github/workflows/ci-cd.yml`)

- **Pull request:** ruff lint, pytest, pip-audit.
- **Push to `DEV`:** the above, then build image, Trivy scan, push to GHCR, deploy to `dev` environment.
- **Push to `main`:** same, deploy to `production` (add required reviewers on that GitHub Environment for approval).

`deploy.sh` is a stub; fill it in for your hosting target.
