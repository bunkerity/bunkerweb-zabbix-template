# Repository Guidelines

## Project Structure & Module Organization

`template_bunkerweb.yaml` is the Zabbix 7.0 release artifact. Keep its macros and release instructions aligned with `README.md`. The `tests/` directory contains the Python import harness, Prometheus fixture, and Docker Compose Zabbix stack. Workflows under `.github/workflows/` validate and release the template. `.plumber.yaml` configures workflow security checks.

## Build, Test, and Development Commands

The repository has no build step. Run CI's core integration flow:

```sh
docker compose -f tests/docker-compose.yml up -d --wait
target=$(docker compose -f tests/docker-compose.yml exec -T server getent hosts metrics | awk 'NR == 1 { print $1 }')
test -n "$target"
python3 tests/import_template.py --url http://127.0.0.1:18080/api_jsonrpc.php --template template_bunkerweb.yaml --target "$target"
docker compose -f tests/docker-compose.yml down --volumes
git diff --check
```

The import command loads the template, creates a test host, and checks required and discovered items. Run the cleanup command after failures.

## Coding Style & Naming Conventions

Use two-space indentation in YAML and preserve the export's existing key order, quoted scalar style, and stable UUIDs. Avoid whole-file reformatting. Zabbix item keys use the existing `bw.*` pattern; user macros use `{$BUNKERWEB.*}`.

Python uses four-space indentation, `snake_case` for functions and variables, and uppercase names for constants. Keep the test harness on the standard library unless a new dependency has a measured benefit.

## Testing Guidelines

Run the Docker integration test after changes to the template, fixture, or import harness. Update `tests/metrics.prom` when a new item or discovery rule needs data. The harness enforces vendor metadata, version syntax, import success, and supported item collection. The project sets no numeric coverage target.

Template changes must increase `vendor.version` using Zabbix's `X.Y-N` format. Pull-request CI compares changed templates with the base revision and rejects a missing or non-increasing bump.

## Commit & Pull Request Guidelines

Follow the Conventional Commit style visible in history, such as `feat: add cache metrics`. Dependabot uses scoped prefixes such as `deps/gha:` and `deps/tests:`. Keep each commit focused.

In a pull request, describe affected items, macros, triggers, or discovery rules; state the version change and test result; and link the relevant issue. Add screenshots only when README rendering changes.

## Security & Release Notes

Keep GitHub Actions pinned to commit SHAs and container images pinned to digests. Do not add credentials or live exporter addresses. Maintainers publish releases from signed `vX.Y-N` tags after CI succeeds.
