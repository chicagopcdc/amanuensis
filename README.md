## Overview

Amanuensis is a backend service used in the GEN3 ecosystem to handle project
requests and access workflows. It integrates with Fence, Arborist, and other
GEN3 services.

## DEPRECATED ##
To speed up the local development workflow for amanuensis, alongside the gen3 stack, follow these steps.
## Amanuensis — Quick start for new contributors (GSoC friendly)

Welcome! This README is written for contributors new to the project and to students joining through programs like Google Summer of Code (GSoC).

If you're experienced, the repository already contains more detailed docs. This file gives a small, friendly path to get you productive quickly.

## What is Amanuensis?

Amanuensis is a backend service in the GEN3 ecosystem that helps manage project requests and access workflows. It integrates with other GEN3 services such as Fence and Arborist and exposes HTTP endpoints used by the platform.

Why you might care (for GSoC):

- Work touches authentication, authorization, backend APIs, and testing.
- Plenty of small-to-medium features and improvements are available as mentoring-friendly tasks.
- Well-tested codebase: tests and fixtures make it easier to iterate safely.

## Beginner-friendly roadmap

1. Read this README and open the project in your editor.
2. Run the test suite and make a small change that keeps tests green (fix a typo or add a tiny test) to learn the workflow.
3. Pick a "good first issue" or ask the project maintainers for a small starter task.
4. Send a pull request and iterate on feedback.

Maintainers: See the repository's issue tracker for mentoring tags and contact info.

## Quick setup (local development)

These commands assume macOS (zsh) and that Python 3.8+ is installed.

1) Create and activate a virtual environment

```bash
python -m venv env
source env/bin/activate
```

2) Install project dependencies with Poetry (this project uses Poetry)

```bash
poetry install
```

3) Generate a default config (creates a file under ~/.gen3/amanuensis/)

```bash
python cfg_help.py create
```

4) Run the app in development mode

There are two common development workflows:

- Lightweight (run tests and small scripts): use the Python environment and run the test server or scripts directly.
- Containerized (recommended for running the full GEN3 stack): use the provided Docker development image.

To run using the Docker development image (optional):

```bash
docker build -f Dockerfile.dev -t amanuensis:test .
```

If you use the GEN3 compose/helm workflow, map your local source into the container so edits are visible during development. The repo already includes a `watch-files.sh` script used in development containers to restart the server automatically on changes.

## Running tests

Run the full test suite with pytest. Some tests rely on additional files or configuration described below.

```bash
pytest --order-scope=module
```

Notes:
- Tests that validate filter set behavior require external JSON files (gitops.json and es_to_dd_map.json) from related GEN3 repos. See the tests folder and test docstrings for details.
- Use `--configuration-file="<config-file.yaml>"` to pass a custom config file when needed; default is `amanuensis-config.yaml`.

## Database migrations

This project uses Alembic for migrations. Typical commands:

```bash
alembic upgrade head    # apply latest migrations
alembic downgrade base  # revert all migrations
alembic revision -m "your message"  # create a new revision file
```

## Architecture overview (short)

- `amanuensis/` — main Python package and application code.
- `amanuensis/auth/` — authentication helpers and auth-related routes.
- `amanuensis/resources/` — service resource implementations (Fence, projects, etc.).
- `migrations/` — Alembic migration scripts.
- `tests/` — pytest test suite and fixtures (see `conftest.py`).

This is intentionally short — explore these folders and open issues when you need clarification.

## Mocking and tests notes (for contributors)

- `conftest.py` contains fixtures that mock external services (Fence, Arborist, S3, etc.). Use these fixtures when adding tests.
- Helpful fixtures: `client` (test client), `session` (db session), `s3` (S3 test bucket), and `register_user` / `fence_users` to mock users.

## Common commands summary

- Install deps: `poetry install`
- Create venv: `python -m venv env && source env/bin/activate`
- Generate default config: `python cfg_help.py create`
- Build dev Docker image: `docker build -f Dockerfile.dev -t amanuensis:test .`
- Run tests: `pytest --order-scope=module`
- Alembic migrations: `alembic upgrade head` / `alembic revision -m "msg"`

## Contributing (short guide)

1. Fork the repository and create a branch named `gsoc/your-topic` or `fix/short-description`.
2. Write tests for new behavior when possible.
3. Run tests locally and ensure they pass.
4. Open a pull request with a clear description of your change and link to any related issue.

For GSoC students: describe your proposal clearly, include a timeline, and list any help you need from mentors. Start by picking a small, well-scoped first task to show progress early.

## Troubleshooting

- If tests fail because of missing external files, check the failing test's docstring and the repository tests/ for the required artifact.
- For container-related issues, check logs with `docker logs <container>` and verify volumes map your local code into the container.

## Where to get help

- Open an issue or comment on an existing issue describing your question.
- Look for CONTRIBUTING.md or project issue tags like `good-first-issue` or `help-wanted`.

----

If you want, I can also:

- Add a short CONTRIBUTING.md with a checklist for new contributors.
- Create a `good-first-issue` template with steps to reproduce and a starter test.

Tell me which of those you'd like next and I will create the files.
