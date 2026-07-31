const { Button, Field, Input, Select, Toast, EmptyState, Switch, ListRow, List } = window.AreyDesignSystem_1909f9;

const PROJECTS = window.PROJECTS, STATUS = window.STATUS;

function Device() {
  const [tab, setTab] = React.useState('projects');
  const [project, setProject] = React.useState(null);
  const [sheet, setSheet] = React.useState(null);

  let screen;
  if (tab === 'projects') {
    screen = project
      ? <ProjectScreen p={project} onBack={() => setProject(null)} onDeploy={() => setSheet('deploy')} />
      : <ProjectsScreen onOpen={setProject} onNew={() => setSheet('new')} />;
  } else if (tab === 'settings') screen = <SettingsScreen />;
  else if (tab === 'activity') screen = <ActivityScreen />;
  else screen = <><NavBar title="Search" large /><Scroll><EmptyState icon="magnifying-glass" title="Search everything" description="Projects, deployments, domains and logs." /></Scroll></>;

  return (
    <>
      <StatusBar />
      {screen}
      <TabBar value={tab} onChange={(t) => { setProject(null); setTab(t); }} />
      <HomeIndicator />
      <Sheet
        open={sheet === 'deploy'}
        title="Deploy arey-web"
        onClose={() => setSheet(null)}
        actions={<><Button variant="primary" size="lg" block onClick={() => setSheet(null)}>Deploy to production</Button><Button variant="ghost" size="lg" block onClick={() => setSheet(null)}>Cancel</Button></>}
      >
        <List inset>
          <ListRow icon="git-branch" title="Branch" value="main" mono />
          <ListRow icon="git-commit" title="Commit" value="a3f91c8" mono />
          <ListRow icon="globe-hemisphere-west" title="Region" value="iad1" mono />
          <ListRow icon="bell" title="Notify me when ready" trailing={<Switch defaultChecked aria-label="Notify me" />} />
        </List>
      </Sheet>
      <Sheet
        open={sheet === 'new'}
        title="New project"
        onClose={() => setSheet(null)}
        actions={<Button variant="primary" size="lg" block onClick={() => setSheet(null)}>Create project</Button>}
      >
        <div style={{ display: 'grid', gap: 'var(--space-5)', paddingBottom: 4 }}>
          <Field label="Project name" hint="Lowercase letters, numbers and dashes"><Input size="lg" placeholder="arey-web" /></Field>
          <Field label="Framework"><Select size="lg" options={['Next.js', 'Astro', 'Vite', 'Expo']} /></Field>
          <Field label="Region"><Select size="lg" options={['Washington, D.C. (iad1)', 'Mumbai (bom1)']} /></Field>
        </div>
      </Sheet>
    </>
  );
}

function StaticPhone({ children, label }) {
  return <Phone label={label}>{children}</Phone>;
}

function MobileApp() {
  return (
    <div style={{ background: 'var(--bg-canvas)', minHeight: '100vh', padding: 'var(--space-10) var(--space-8)' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 'var(--space-6)', marginBottom: 'var(--space-8)' }}>
          <div style={{ flex: 1 }}>
            <div style={{ font: 'var(--type-eyebrow)', letterSpacing: 'var(--tracking-eyebrow)', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 'var(--space-3)' }}>arey Mobile</div>
            <h1 style={{ font: 'var(--type-title-1)', letterSpacing: 'var(--tracking-heading)' }}>iOS screens</h1>
            <p style={{ font: 'var(--type-body-lg)', color: 'var(--text-secondary)', marginTop: 'var(--space-2)' }}>The left device is live — tap through projects, open a deployment sheet, switch tabs.</p>
          </div>
          <ThemeSwitch />
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-10)', flexWrap: 'wrap' }}>
          <Phone label="Live"><Device /></Phone>
          <Phone label="Settings"><StatusBar /><SettingsScreen /><TabBar value="settings" onChange={() => {}} /><HomeIndicator /></Phone>
          <Phone label="Activity"><StatusBar /><ActivityScreen /><TabBar value="activity" onChange={() => {}} /><HomeIndicator /></Phone>
        </div>
      </div>
    </div>
  );
}

function ThemeSwitch() {
  const { SegmentedControl } = window.AreyDesignSystem_1909f9;
  const [t, setT] = React.useState('light');
  React.useEffect(() => { document.documentElement.setAttribute('data-theme', t); }, [t]);
  return <div style={{ width: 200 }}><SegmentedControl value={t} onChange={setT} options={[{ value: 'light', label: 'Light', icon: 'sun' }, { value: 'dark', label: 'Dark', icon: 'moon' }]} /></div>;
}

ReactDOM.createRoot(document.getElementById('root')).render(<MobileApp />);
