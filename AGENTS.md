# Repository Guidelines

## Project Structure & Module Organization
- `trendradar/` contains the main crawler, analysis, reporting, storage, and notification pipeline (`core/`, `crawler/`, `report/`, `storage/`, `notification/`, `ai/`).
- `mcp_server/` contains the FastMCP service (`server.py`) plus tool/service modules for MCP clients.
- `config/` holds runtime configuration (`config.yaml`, `frequency_words.txt`, `timeline.yaml`, AI prompt templates).
- `docker/` includes Dockerfiles, Compose files, and container entrypoint/manage scripts.
- `output/` stores generated data and reports (including sample data used for local validation).
- `.github/workflows/` defines scheduled crawling and Docker image publishing.

## Build, Test, and Development Commands
- `uv sync` — install/update dependencies from `pyproject.toml` (preferred local setup).
- `python3 -m pip install -r requirements.txt` — workflow-compatible dependency install path.
- `python3 -m trendradar` (or `uv run trendradar`) — run one local crawl/analysis cycle.
- `uv run python -m mcp_server.server --transport http --port 3333` — run MCP server in HTTP mode.
- `./start-http.sh` — helper script to launch MCP server with project defaults.
- `docker compose -f docker/docker-compose.yml up -d` — start prebuilt containers.
- `docker compose -f docker/docker-compose-build.yml up -d --build` — build images locally and run.

## Coding Style & Naming Conventions
- Target Python 3.10+; use 4-space indentation and follow PEP 8 conventions.
- Keep modules/functions in `snake_case`, classes in `PascalCase`, and constants in `UPPER_SNAKE_CASE`.
- Match existing style: type hints on new public functions and concise docstrings for non-trivial logic.
- Keep configuration keys and schema changes synchronized with `config/config.yaml` and related docs.

## Testing Guidelines
- There is currently no dedicated `tests/` suite; use lightweight smoke checks before opening a PR.
- Recommended baseline: `python3 -m compileall trendradar mcp_server scripts`.
- For behavior changes, run a local cycle (`python3 -m trendradar`) and verify generated output under `output/`.
- For MCP changes, validate at least one tool call by starting `mcp_server.server` locally.

## Commit & Pull Request Guidelines
- Follow the repository’s observed commit style: `type: short summary` (examples: `fix: ...`, `schedule: ...`).
- Keep commits focused; separate refactors, config updates, and feature changes when practical.
- PRs should include: purpose, key files changed, config or secret impacts, and manual verification steps.
- Link related issues and attach screenshots when report rendering or web output changes.

## Security & Configuration Tips
- Never commit real webhook tokens, API keys, or email credentials; use environment variables/secrets.
- Treat `config/config.yaml` and `docker/.env` as templates for local values, not places for production secrets.
