const { SidebarNav, Button, Badge, Icon, Card, Kbd, SegmentedControl, Tabs } = window.AreyDesignSystem_1909f9;

const TOC = [
  { id: 'install', label: 'Install the CLI' },
  { id: 'link', label: 'Link a project' },
  { id: 'deploy', label: 'Your first deployment' },
  { id: 'env', label: 'Environment variables' },
  { id: 'props', label: 'Command reference' },
];

function DocsApp() {
  const [page, setPage] = React.useState('quickstart');
  const [active, setActive] = React.useState('install');
  const [pkg, setPkg] = React.useState('npm');
  const install = { npm: 'npm i -g arey', pnpm: 'pnpm add -g arey', brew: 'brew install arey' };
  return (
    <div style={{ background: 'var(--bg-base)', minHeight: '100vh' }}>
      <DocsHeader />
      <div style={{ display: 'flex', gap: 'var(--space-10)', maxWidth: 1440, margin: '0 auto', padding: '0 var(--space-8)' }}>
        <div style={{ width: 240, flex: 'none', position: 'sticky', top: 'var(--topbar-h)', height: 'calc(100vh - var(--topbar-h))', overflow: 'auto', borderRight: '1px solid var(--border-subtle)', marginLeft: 'calc(var(--space-8) * -1)', paddingLeft: 'var(--space-4)' }}>
          <SidebarNav value={page} onChange={setPage} groups={[
            { label: 'Getting started', items: [
              { value: 'introduction', label: 'Introduction' },
              { value: 'quickstart', label: 'Quickstart' },
              { value: 'projects', label: 'Projects' },
            ] },
            { label: 'Deploying', items: [
              { value: 'builds', label: 'Builds' },
              { value: 'environments', label: 'Environments' },
              { value: 'domains', label: 'Domains' },
              { value: 'rollbacks', label: 'Rollbacks' },
            ] },
            { label: 'Reference', items: [
              { value: 'cli', label: 'CLI' },
              { value: 'config', label: 'arey.json' },
              { value: 'api', label: 'REST API' },
            ] },
          ]} />
        </div>

        <main style={{ flex: 1, minWidth: 0, padding: 'var(--space-10) 0 var(--space-24)' }} className="prose">
          <div style={{ font: 'var(--type-eyebrow)', letterSpacing: 'var(--tracking-eyebrow)', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 'var(--space-4)' }}>Getting started</div>
          <h1 style={{ font: 'var(--type-title-1)', letterSpacing: 'var(--tracking-heading)', margin: 0 }}>Quickstart</h1>
          <p style={{ marginTop: 'var(--space-4)', color: 'var(--text-secondary)' }}>Install the CLI, link a project, and ship it. This takes about four minutes.</p>

          <h2 id="install">Install the CLI</h2>
          <p>The CLI is the fastest way to deploy. It works on macOS, Linux and Windows.</p>
          <div style={{ maxWidth: 300, margin: '0 0 var(--space-4)' }}>
            <SegmentedControl value={pkg} onChange={setPkg} options={[{ value: 'npm', label: 'npm' }, { value: 'pnpm', label: 'pnpm' }, { value: 'brew', label: 'brew' }]} />
          </div>
          <CodeBlock lines={['$ ' + install[pkg], '$ arey --version', 'arey/4.2.0 darwin-arm64 node-20.11.1']} />
          <Callout tone="note" title="Node 18 or newer">The CLI needs Node 18+. Check with <code>node --version</code> before installing.</Callout>

          <h2 id="link">Link a project</h2>
          <p>Run <code>arey link</code> inside your repository. The CLI writes a <code>.arey</code> directory holding the project id — commit it so your team shares the same link.</p>
          <CodeBlock lines={['$ arey link', '? Link to existing project? yes', '? Which project? arey-web', 'Linked to riya/arey-web (created .arey)']} />

          <h2 id="deploy">Your first deployment</h2>
          <p>Deployments are immutable. Every build gets its own URL, and promoting to production only changes which build the production domain points at.</p>
          <CodeBlock lines={['$ arey deploy', 'Uploading 38 files (4.2 MB)', 'Building in iad1 · node-20', 'Ready — https://arey-web-9f2a.arey.app  48 s']} />
          <ul>
            <li><strong>Preview</strong> — every push to a non-production branch.</li>
            <li><strong>Production</strong> — pushes to <code>main</code>, or <code>arey deploy --prod</code>.</li>
            <li><strong>Rollback</strong> — promote any previous build; no rebuild happens.</li>
          </ul>
          <Callout tone="warning" title="Production deploys skip the queue">A <code>--prod</code> deploy is promoted the moment it is ready. Enable <strong>Protect production</strong> in project settings to require a review first.</Callout>

          <h2 id="env">Environment variables</h2>
          <p>Variables are scoped per environment and encrypted at rest. Pull them locally with <code>arey env pull</code>.</p>
          <CodeBlock filename=".env.local" lines={['# Pulled from riya/arey-web · production', 'DATABASE_URL=postgres://…', 'API_KEY=sk_live_9f2a7c41e8']} />

          <h2 id="props">Command reference</h2>
          <PropsTable rows={[
            ['arey deploy', '--prod, --yes', '—'],
            ['arey link', '--project <name>', 'interactive'],
            ['arey env pull', '--environment <env>', 'production'],
            ['arey logs', '--follow, --since <t>', '1h'],
            ['arey rollback', '<deployment>', 'previous'],
          ]} />
          <div style={{ display: 'flex', gap: 'var(--space-4)', marginTop: 'var(--space-12)', maxWidth: 'var(--prose-max)' }}>
            <Card interactive style={{ flex: 1 }}>
              <div style={{ font: 'var(--type-caption)', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 6 }}><Icon name="arrow-left" size={12} />Previous</div>
              <div style={{ font: 'var(--type-title-3)', color: 'var(--text-primary)', marginTop: 6 }}>Introduction</div>
            </Card>
            <Card interactive style={{ flex: 1, textAlign: 'right' }}>
              <div style={{ font: 'var(--type-caption)', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'flex-end' }}>Next<Icon name="arrow-right" size={12} /></div>
              <div style={{ font: 'var(--type-title-3)', color: 'var(--text-primary)', marginTop: 6 }}>Projects</div>
            </Card>
          </div>
        </main>

        <OnThisPage items={TOC} active={active} onSelect={setActive} />
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<DocsApp />);
