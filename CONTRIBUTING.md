# Contributing to FinSight

Thanks for your interest in contributing! This guide covers how to set up the project, the quality
bar, and how to propose changes.

## Development setup

```bash
# Backend
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows; use bin/activate on macOS/Linux
pip install -e ".[dev]"

# Frontend
cd ../frontend
npm install
```

Copy `.env.example` to `.env` and set at least `GOOGLE_API_KEY`. See [README.md](README.md) for the
full Docker-based workflow.

## Quality bar (enforced in CI)

Before opening a pull request, make sure these pass locally — the same checks run in
[GitHub Actions](.github/workflows/ci.yml):

```bash
cd backend
ruff check app tests evals          # lint
ruff format --check app tests evals # formatting
pytest -q                           # tests (69+), must stay green
```

- **Type hints** on public function signatures.
- **Docstrings** on modules and non-trivial functions.
- **Tests** for new behaviour. Safety-relevant changes must keep the adversarial eval green
  (`python -m evals.run_safety_eval`) and add cases to `evals/safety_dataset.py` when relevant.
- Keep functions small and avoid duplication; follow the existing SOLID layering
  (`api → services → repositories`, ports/adapters for external systems).

## Pull request process

1. Fork and branch from `main` (`feat/...`, `fix/...`, `docs/...`).
2. Make focused commits with [Conventional Commits](https://www.conventionalcommits.org) messages.
3. Ensure lint + tests pass and update docs (`README.md`, `docs/`) when behaviour changes.
4. Open a PR describing the change, the motivation, and how you verified it.

## Reporting issues

Please include steps to reproduce, expected vs actual behaviour, and the request's `X-Request-ID`
(returned on every response) when reporting a runtime error.

## Code of Conduct

Participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md).
