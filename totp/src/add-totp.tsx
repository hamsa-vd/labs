import { execFile } from "child_process";
import { Action, ActionPanel, Form, popToRoot, showHUD } from "@raycast/api";
import { useState } from "react";
import { promisify } from "util";

const run = promisify(execFile);

export default function Command() {
  const [appError, setAppError] = useState<string | undefined>();
  const [secretError, setSecretError] = useState<string | undefined>();

  async function handleSubmit(values: { app: string; secret: string }) {
    const app = values.app.trim();
    const secret = values.secret.trim();

    let valid = true;
    if (!app) {
      setAppError("App name is required");
      valid = false;
    } else {
      setAppError(undefined);
    }
    if (!secret) {
      setSecretError("Secret is required");
      valid = false;
    } else {
      setSecretError(undefined);
    }
    if (!valid) return;

    try {
      await run("/usr/bin/security", [
        "add-generic-password",
        "-a",
        process.env.USER ?? "",
        "-s",
        `totp-${app}`,
        "-w",
        secret,
      ]);
      await showHUD(`✅ Added TOTP for "${app}"`);
      await popToRoot();
    } catch (e) {
      const msg = (e as Error & { stderr?: string }).stderr?.trim() || (e as Error).message;
      await showHUD(`❌ Failed: ${msg}`);
    }
  }

  return (
    <Form
      actions={
        <ActionPanel>
          <Action.SubmitForm title="Add TOTP Secret" onSubmit={handleSubmit} />
        </ActionPanel>
      }
    >
      <Form.TextField
        id="app"
        title="App Name"
        placeholder="e.g. github"
        error={appError}
        onChange={() => setAppError(undefined)}
      />
      <Form.PasswordField
        id="secret"
        title="TOTP Secret"
        placeholder="Base32 secret key"
        error={secretError}
        onChange={() => setSecretError(undefined)}
      />
    </Form>
  );
}
