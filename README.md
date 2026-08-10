# Extensions

Monorepo for Raycast extensions. Each extension lives in its own subfolder under this directory.

## Available extensions

- `totp/` — manage TOTP secrets stored in macOS Keychain and generate codes in Raycast.

## Common commands

- `pnpm --filter totp dev` — run the TOTP extension in Raycast dev mode
- `pnpm --filter totp lint` — lint the TOTP extension
- `pnpm --filter totp build` — build the TOTP extension
