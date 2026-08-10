# TOTP

Raycast extension for storing TOTP secrets in macOS Keychain and generating one-time codes from them. It lets you add a secret, view/copy/paste the current code, edit the app name or secret, and delete entries.

## Prerequisites

- macOS
- Raycast installed
- `security` command available (included with macOS)
- `oathtool` installed at `/opt/homebrew/bin/oathtool`
  - If you use Intel Homebrew, update the path in `src/totp-codes.tsx`

## Usage

### Add a TOTP secret

1. Open **Add TOTP Secret** in Raycast.
2. Enter the app name. This becomes the Keychain service name: `totp-{app}`.
3. Enter the Base32 TOTP secret.
4. Save the entry.

### Generate a code

1. Open **TOTP Codes**.
2. Search for the app.
3. Use **Copy Code** or **Paste Code**.

### Edit an entry

1. Open **TOTP Codes**.
2. Choose **Edit**.
3. Change the app name, the secret, or both.
4. Save changes. If you only change the name, leave the secret as-is.

### Delete an entry

1. Open **TOTP Codes**.
2. Choose **Delete**.
3. Confirm the prompt.

## Storage format

Entries are stored as macOS generic passwords with the service name `totp-{app}` and the secret as the password value.
