const { Card, Button, IconButton, Field, Input, Textarea, Select, Switch, Checkbox, RadioGroup, List, ListRow, Badge, Avatar, Dialog, SegmentedControl, Tabs, Kbd, Tag } = window.AreyDesignSystem_1909f9;

function Section({ title, description, children, footer, danger }) {
  return (
    <Card
      title={title}
      description={description}
      footer={footer}
      style={danger ? { borderColor: 'var(--danger-solid)' } : undefined}
    >
      {children}
    </Card>
  );
}

function Settings() {
  const [tab, setTab] = React.useState('general');
  const [theme, setTheme] = React.useState('system');
  const [confirm, setConfirm] = React.useState(false);
  const [vis, setVis] = React.useState('private');
  return (
    <Page>
      <PageHead eyebrow="arey-web" title="Settings" description="Project configuration. Changes apply to the next deployment." />
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <Tabs value={tab} onChange={setTab} items={[{ value: 'general', label: 'General' }, { value: 'env', label: 'Environment', count: 6 }, { value: 'members', label: 'Members', count: 4 }, { value: 'advanced', label: 'Advanced', icon: 'sliders-horizontal' }]} />
      </div>
      <div style={{ display: 'grid', gap: 'var(--space-6)' }}>
        <Section title="Project" description="Names and identifiers other people see." footer={<><span style={{ font: 'var(--type-caption)', color: 'var(--text-secondary)', marginRight: 'auto' }}>Renaming does not change existing deployment URLs.</span><Button variant="primary" size="sm">Save</Button></>}>
          <div style={{ display: 'grid', gap: 'var(--space-6)' }}>
            <Field layout="row" label="Project name" hint="Lowercase letters, numbers and dashes" htmlFor="pn"><Input id="pn" defaultValue="arey-web" /></Field>
            <Field layout="row" label="Production branch" hint="Pushes here deploy to production"><Select options={['main', 'release/4.2']} /></Field>
            <Field layout="row" label="Description" optional><Textarea rows={3} defaultValue="Marketing site and console shell for arey." /></Field>
            <Field layout="row" label="Visibility">
              <RadioGroup name="vis" value={vis} onChange={setVis} options={[
                { value: 'private', label: 'Private', description: 'Only members can view deployments' },
                { value: 'public', label: 'Public', description: 'Anyone with the link can view' },
              ]} />
            </Field>
          </div>
        </Section>

        <Section title="Build & deploy" description="How arey builds this project.">
          <div style={{ display: 'grid', gap: 'var(--space-5)' }}>
            <List>
              <ListRow icon="lightning" title="Automatic deployments" subtitle="Deploy every push to a tracked branch" trailing={<Switch defaultChecked aria-label="Automatic deployments" />} />
              <ListRow icon="chat-circle-dots" title="Preview comments" subtitle="Let reviewers comment on preview URLs" trailing={<Switch tone="accent" defaultChecked aria-label="Preview comments" />} />
              <ListRow icon="shield-check" title="Protect production" subtitle="Require a review before promoting" trailing={<Switch aria-label="Protect production" />} />
            </List>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-5)' }}>
              <Field label="Install command"><Input mono defaultValue="npm install" /></Field>
              <Field label="Build command"><Input mono defaultValue="npm run build" /></Field>
              <Field label="Output directory"><Input mono defaultValue=".arey/output" /></Field>
              <Field label="Node version"><Select options={['node-20', 'node-18']} /></Field>
            </div>
          </div>
        </Section>

        <Section title="Appearance" description="Applies to your account across every project.">
          <div style={{ display: 'grid', gap: 'var(--space-5)', maxWidth: 420 }}>
            <Field label="Theme"><SegmentedControl value={theme} onChange={setTheme} options={[{ value: 'light', label: 'Light', icon: 'sun' }, { value: 'dark', label: 'Dark', icon: 'moon' }, { value: 'system', label: 'System', icon: 'desktop' }]} /></Field>
            <Field label="Density" hint="arey defaults to the roomy scale"><SegmentedControl value="roomy" onChange={() => {}} options={[{ value: 'roomy', label: 'Roomy' }, { value: 'compact', label: 'Compact' }]} /></Field>
            <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
              <Checkbox label="Show relative timestamps" defaultChecked description="Absolute times still appear on hover" />
              <Checkbox label="Reduce motion" />
            </div>
          </div>
        </Section>

        <Section title="API keys" description="Server-side keys. Rotating a key invalidates it immediately." padded>
          <List inset>
            <ListRow icon="key" title="Production" value="sk_live_9f2a7c41e8" mono trailing={<div style={{ display: 'flex', gap: 4 }}><IconButton icon="copy" label="Copy key" size="sm" /><IconButton icon="arrows-clockwise" label="Rotate key" size="sm" /></div>} />
            <ListRow icon="key" title="Preview" value="sk_test_41b8e2c04d" mono trailing={<div style={{ display: 'flex', gap: 4 }}><IconButton icon="copy" label="Copy key" size="sm" /><IconButton icon="arrows-clockwise" label="Rotate key" size="sm" /></div>} />
          </List>
        </Section>

        <Section
          title="Delete project"
          description="This removes all deployments, domains and logs. It cannot be undone."
          footer={<><span style={{ marginRight: 'auto' }} /><Button variant="danger" size="sm" onClick={() => setConfirm(true)}>Delete project</Button></>}
        />
      </div>

      <Dialog
        open={confirm}
        onClose={() => setConfirm(false)}
        title="Delete arey-web"
        description="This removes 24 deployments, 2 domains and all logs. It cannot be undone."
        footer={<><Button onClick={() => setConfirm(false)}>Cancel</Button><Button variant="danger" onClick={() => setConfirm(false)}>Delete project</Button></>}
      >
        <Field label="Type the project name to confirm"><Input placeholder="arey-web" /></Field>
      </Dialog>
    </Page>
  );
}

Object.assign(window, { Settings });
