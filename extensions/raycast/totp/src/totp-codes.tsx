import { execFile } from "child_process";
import {
  Action,
  ActionPanel,
  Alert,
  Clipboard,
  confirmAlert,
  Form,
  Icon,
  List,
  showHUD,
  useNavigation,
} from "@raycast/api";
import { useEffect, useState } from "react";
import { promisify } from "util";

const run = promisify(execFile);

// Homebrew oathtool path: Apple Silicon vs Intel. Adjust if `which oathtool` differs.
const OATHTOOL = "/opt/homebrew/bin/oathtool";

interface Service {
  name: string; // e.g. "auth0" (the part after "totp-")
  key: string; // full keychain service name, e.g. "totp-auth0"
}

async function listServices(): Promise<Service[]> {
  // dump-keychain lists all generic passwords; filter to our totp- prefix.
  const { stdout } = await run("/usr/bin/security", ["dump-keychain"]);
  const names = new Set<string>();
  for (const line of stdout.split("\n")) {
    // service attribute lines look like:  "svce"<blob>="totp-auth0"
    const m = line.match(/"svce"<blob>="(totp-[^"]+)"/);
    if (m) names.add(m[1]);
  }
  return [...names].sort().map((key) => ({ key, name: key.replace(/^totp-/, "") }));
}

async function getSecret(key: string): Promise<string> {
  const { stdout } = await run("/usr/bin/security", ["find-generic-password", "-s", key, "-w"]);
  return stdout.trim();
}

async function generateCode(key: string): Promise<string> {
  const secret = await getSecret(key);
  const { stdout } = await run(OATHTOOL, ["--totp", "-b", secret]);
  return stdout.trim();
}

function EditTotpForm({
  service,
  onUpdated,
}: {
  service: Service;
  onUpdated: (oldKey: string, updated: Service) => void;
}) {
  const { pop } = useNavigation();
  const [appError, setAppError] = useState<string | undefined>();
  const [secretError, setSecretError] = useState<string | undefined>();
  const [currentSecret, setCurrentSecret] = useState<string>("");
  const [secretFieldValue, setSecretFieldValue] = useState<string>("");
  const [loadingSecret, setLoadingSecret] = useState(true);

  useEffect(() => {
    getSecret(service.key)
      .then((s) => {
        setCurrentSecret(s);
        setSecretFieldValue(s);
      })
      .catch(() => {})
      .finally(() => setLoadingSecret(false));
  }, [service.key]);

  async function handleSubmit(values: { app: string; secret: string }) {
    const app = values.app.trim();
    // Use whatever was typed; fall back to the fetched secret if field was left blank
    const secret = (values.secret ?? "").trim() || currentSecret;

    let valid = true;
    if (!app) {
      setAppError("App name is required");
      valid = false;
    } else setAppError(undefined);
    if (!secret) {
      setSecretError("Secret is required");
      valid = false;
    } else setSecretError(undefined);
    if (!valid) return;

    const newKey = `totp-${app}`;
    try {
      // Delete old entry then add new one (handles both name and secret changes)
      await run("/usr/bin/security", ["delete-generic-password", "-s", service.key]);
      await run("/usr/bin/security", [
        "add-generic-password",
        "-a",
        process.env.USER ?? "",
        "-s",
        newKey,
        "-w",
        secret,
      ]);
      onUpdated(service.key, { name: app, key: newKey });
      await showHUD(`✅ Updated "${app}"`);
      pop();
    } catch (e) {
      const msg = (e as Error & { stderr?: string }).stderr?.trim() || (e as Error).message;
      await showHUD(`❌ Failed: ${msg}`);
    }
  }

  return (
    <Form
      isLoading={loadingSecret}
      actions={
        <ActionPanel>
          <Action.SubmitForm title="Save Changes" onSubmit={handleSubmit} />
        </ActionPanel>
      }
    >
      <Form.TextField
        id="app"
        title="App Name"
        defaultValue={service.name}
        error={appError}
        onChange={() => setAppError(undefined)}
      />
      <Form.PasswordField
        id="secret"
        title="TOTP Secret"
        placeholder={loadingSecret ? "Loading…" : "Leave blank to keep current secret"}
        value={secretFieldValue}
        error={secretError}
        onChange={(v) => {
          setSecretFieldValue(v);
          setSecretError(undefined);
        }}
      />
    </Form>
  );
}

export default function Command() {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listServices()
      .then(setServices)
      .catch(async (e) => {
        await showHUD(`Error listing services: ${e.message}`);
      })
      .finally(() => setLoading(false));
  }, []);

  function handleUpdated(oldKey: string, updated: Service) {
    setServices((prev) => prev.map((s) => (s.key === oldKey ? updated : s)).sort((a, b) => a.key.localeCompare(b.key)));
  }

  async function deleteService(service: Service) {
    const confirmed = await confirmAlert({
      title: `Delete "${service.name}"?`,
      message: "This will remove the TOTP secret from your Keychain. This cannot be undone.",
      primaryAction: { title: "Delete", style: Alert.ActionStyle.Destructive },
    });
    if (!confirmed) return;
    try {
      await run("/usr/bin/security", ["delete-generic-password", "-s", service.key]);
      setServices((prev) => prev.filter((s) => s.key !== service.key));
      await showHUD(`Deleted "${service.name}"`);
    } catch (e) {
      await showHUD(`Failed to delete: ${(e as Error).message}`);
    }
  }

  async function copyCode(service: Service) {
    try {
      const code = await generateCode(service.key);
      await Clipboard.copy(code, { transient: true });
      await showHUD(`Copied ${service.name}: ${code}`);
    } catch (e) {
      await showHUD(`Failed: ${(e as Error).message}`);
    }
  }

  async function pasteCode(service: Service) {
    try {
      const code = await generateCode(service.key);
      await Clipboard.paste(code);
    } catch (e) {
      await showHUD(`Failed: ${(e as Error).message}`);
    }
  }

  return (
    <List isLoading={loading} searchBarPlaceholder="Search TOTP service...">
      {services.map((s) => (
        <List.Item
          key={s.key}
          icon={Icon.Key}
          title={s.name}
          actions={
            <ActionPanel>
              <Action title="Paste Code" icon={Icon.Text} onAction={() => pasteCode(s)} />
              <Action title="Copy Code" icon={Icon.Clipboard} onAction={() => copyCode(s)} />
              <Action.Push
                title="Edit"
                icon={Icon.Pencil}
                target={<EditTotpForm service={s} onUpdated={handleUpdated} />}
              />
              <Action
                title="Delete"
                icon={Icon.Trash}
                style={Action.Style.Destructive}
                onAction={() => deleteService(s)}
              />
            </ActionPanel>
          }
        />
      ))}
    </List>
  );
}
