# Reforger Agent Harness

Local tools for Arma Reforger and Enfusion Workbench: open projects, validate and pack addons, run isolated tests, inspect logs, and capture gameplay.

This is tooling, not a mod. Addon source and game assets belong in their own repositories. Commands that launch or change game processes dry-run until `--execute` is supplied.

## Setup

Requires Windows with Arma Reforger and Reforger Tools, plus Node.js 24+. FFmpeg is optional for recordings.

1. Run `npm ci`.
2. Copy `reforger-agent.config.example.json` to `reforger-agent.config.json` and set your local paths.
3. Run `npm run cli -- doctor`.
4. Run `npm run typecheck && npm test && npm run build`.

Personal configuration and generated output stay Git-ignored. An optional read-only MCP server runs with `npm start` after building.

## Use

- [Getting started](docs/harness-handoff.md)
- [Mod workflows](docs/workflows.md) and [feature recipes](docs/feature-recipes.md)
- [Command examples and capture notes](docs/usage.md)
- [Workbench and gameplay troubleshooting](docs/operations-playbook.md)
- [Visual review](docs/clean-visual-review.md) and [audio capture](docs/loopback-audio.md)

GitHub CI checks TypeScript, unit tests, and compilation. It does not test Workbench, game behavior, or recordings. See [tested scope and limitations](docs/workflow-acceptance.md).

## License

[Apache-2.0](LICENSE); see [NOTICE](NOTICE). Third-party assets keep their own terms. Independent mods built with the tools do not inherit the harness license. Credit is appreciated, not required.
