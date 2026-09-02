# Contributing to BunkerWeb by HTTP for Zabbix

Thanks for helping improve the BunkerWeb Zabbix template.

## Before you start

- Search open and closed issues before creating a new one.
- Open an issue before working on a pull request unless the change is a typo or clearly mechanical maintenance.
- Use the bug, improvement, or question form so maintainers have the context they need.
- Do not disclose suspected vulnerabilities publicly. Follow the [BunkerWeb security policy](https://github.com/bunkerity/bunkerweb/security/policy) instead.
- Read [AGENTS.md](../AGENTS.md) for repository structure, validation commands, style, versioning, and release rules.

## Make a change

Keep each contribution focused. Preserve the template's existing key order, quoting style, and stable UUIDs. Update `tests/metrics.prom`, the import harness, and `README.md` when the behavior they describe changes.

Changes to `template_bunkerweb.yaml` must increase `vendor.version` using Zabbix's `X.Y-N` format. Run `pre-commit run --all-files`, review any automatic fixes, and then run the relevant integration validation from `AGENTS.md` before opening a pull request.

## Open a pull request

Link the related issue with `Fixes #123` or `Refs #123`. Explain what changed, which items, macros, triggers, or discovery rules are affected, and how the change was validated. Include the template version change and any documentation or fixture updates.
