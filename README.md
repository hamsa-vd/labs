# Labs

Polyglot monorepo for applications and experiments owned under `hamsa-vd`.

## Layout

```text
apps/       independently buildable applications
packages/   reusable libraries, grouped by language when needed
tooling/    repository-wide automation and templates
archive/    inactive experiments retained for reference
```

Each application owns its runtime, dependencies, tests, and deployment configuration. The root provides discovery and convenience commands; it does not force every application into the same language or release cycle.

## Projects

| Project | Stack | Status | Purpose |
| --- | --- | --- | --- |
| `apps/ascend` | Next.js, TypeScript | Scaffold | Private job-application tracker |

## Commands

```sh
pnpm install
pnpm ascend:dev
pnpm ascend:check
```

If `just` is installed, equivalent shortcuts are available through the root `justfile`.
