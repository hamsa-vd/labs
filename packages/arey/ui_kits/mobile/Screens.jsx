const { Icon, IconButton, Badge, ListRow, Switch, SegmentedControl, Button, Avatar, ProgressBar, Input, Tag } = window.AreyDesignSystem_1909f9;

function ProjectsScreen({ onOpen, onNew }) {
  return (
    <>
      <NavBar title="Projects" large trailing={<IconButton icon="plus" label="New project" onClick={onNew} />} />
      <Scroll>
        <div style={{ padding: '8px 16px 16px' }}>
          <Input size="md" icon="magnifying-glass" placeholder="Search projects" />
        </div>
        <div style={{ display: 'flex', gap: 8, padding: '0 16px 20px', overflow: 'auto' }}>
          <Tag icon="funnel" onClick={() => {}} selected>All</Tag>
          <Tag onClick={() => {}}>Ready</Tag>
          <Tag onClick={() => {}}>Building</Tag>
          <Tag onClick={() => {}}>Failed</Tag>
        </div>
        <Group label="Production">
          {window.PROJECTS.slice(0, 3).map((p) => {
            const s = window.STATUS[p.status];
            return <ListRow key={p.name} leading={<Avatar name={p.name.replace('arey-', '')} square tone="accent" />} title={p.name} subtitle={p.branch + ' · ' + p.time} trailing={<Badge tone={s.tone} dot size="sm">{s.label}</Badge>} chevron onClick={() => onOpen(p)} />;
          })}
        </Group>
        <Group label="All projects" footer="Pull to refresh. Deployments update live.">
          {window.PROJECTS.slice(3).map((p) => {
            const s = window.STATUS[p.status];
            return <ListRow key={p.name} leading={<Avatar name={p.name.replace('arey-', '')} square /> } title={p.name} subtitle={p.framework + ' · ' + p.time} trailing={<Badge tone={s.tone} dot size="sm">{s.label}</Badge>} chevron onClick={() => onOpen(p)} />;
          })}
        </Group>
      </Scroll>
    </>
  );
}

function ProjectScreen({ p, onBack, onDeploy }) {
  const s = window.STATUS[p.status];
  const [range, setRange] = React.useState('7d');
  return (
    <>
      <NavBar title={p.name} back="Projects" onBack={onBack} trailing={<IconButton icon="dots-three" label="Options" />} />
      <Scroll>
        <div style={{ padding: '20px 16px', display: 'grid', gap: 'var(--space-5)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Avatar name={p.name.replace('arey-', '')} square tone="accent" size="xl" />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ font: 'var(--weight-semibold) 22px var(--font-sans)', letterSpacing: '-.028em', color: 'var(--text-primary)' }}>{p.name}</div>
              <div style={{ font: 'var(--type-code)', color: 'var(--text-tertiary)', marginTop: 2 }}>{p.name}.arey.app</div>
            </div>
            <Badge tone={s.tone} dot>{s.label}</Badge>
          </div>
          <div style={{ display: 'grid', gridAutoFlow: 'column', gap: 8 }}>
            <Button variant="primary" size="lg" iconLeft="rocket-launch" onClick={onDeploy}>Deploy</Button>
            <Button variant="secondary" size="lg" iconLeft="arrow-square-out">Visit</Button>
          </div>
          <SegmentedControl size="lg" value={range} onChange={setRange} options={[{ value: '24h', label: 'Day' }, { value: '7d', label: 'Week' }, { value: '30d', label: 'Month' }]} />
        </div>
        <Group label="Latest deployment">
          <ListRow icon="git-commit" title={window.DEPLOYMENTS[0].msg} subtitle={window.DEPLOYMENTS[0].sha + ' · ' + window.DEPLOYMENTS[0].author} chevron onClick={() => {}} />
          <ListRow icon="timer" title="Duration" value={p.dur} mono />
          <ListRow icon="globe-hemisphere-west" title="Region" value="iad1" mono />
        </Group>
        <Group label="Usage" footer="68 % of the 1 TB included in the Hobby plan.">
          <ListRow icon="gauge" title="Bandwidth" value="412 GB" mono />
          <ListRow icon="lightning" title="Requests" value="2.4 M" mono />
          <ListRow icon="clock-countdown" title="Build minutes" value="1 240" mono />
        </Group>
        <div style={{ padding: '0 20px 24px' }}><ProgressBar value={68} /></div>
      </Scroll>
    </>
  );
}

function SettingsScreen() {
  const [theme, setTheme] = React.useState('system');
  React.useEffect(() => {
    if (theme === 'system') return;
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);
  return (
    <>
      <NavBar title="Settings" large />
      <Scroll>
        <div style={{ margin: '8px 16px 24px', display: 'flex', alignItems: 'center', gap: 14, padding: 16, background: 'var(--surface-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-card)', boxShadow: 'var(--shadow-sm)' }}>
          <Avatar name="Riya Menon" size="xl" />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ font: 'var(--weight-semibold) 17px var(--font-sans)', letterSpacing: '-.02em', color: 'var(--text-primary)' }}>Riya Menon</div>
            <div style={{ font: 'var(--type-code)', color: 'var(--text-tertiary)' }}>riya@arey.dev</div>
          </div>
          <Icon name="caret-right" size={16} color="var(--text-tertiary)" />
        </div>
        <div style={{ padding: '0 16px 24px', display: 'grid', gap: 8 }}>
          <GroupLabel>Appearance</GroupLabel>
          <SegmentedControl size="lg" value={theme} onChange={setTheme} options={[{ value: 'light', label: 'Light', icon: 'sun' }, { value: 'dark', label: 'Dark', icon: 'moon' }, { value: 'system', label: 'Auto', icon: 'circle-half' }]} />
        </div>
        <Group label="Notifications" footer="Push notifications are sent for projects you own.">
          <ListRow icon="bell" title="Deployment ready" trailing={<Switch defaultChecked aria-label="Deployment ready" />} />
          <ListRow icon="warning-octagon" title="Build failed" trailing={<Switch defaultChecked aria-label="Build failed" />} />
          <ListRow icon="chat-circle-dots" title="Comments" trailing={<Switch aria-label="Comments" />} />
        </Group>
        <Group label="Account">
          <ListRow icon="users-three" title="Team" value="riya" chevron onClick={() => {}} />
          <ListRow icon="credit-card" title="Plan" value="Hobby" chevron onClick={() => {}} />
          <ListRow icon="key" title="API keys" chevron onClick={() => {}} />
          <ListRow icon="shield-check" title="Two-factor auth" value="On" chevron onClick={() => {}} />
        </Group>
        <Group label="About">
          <ListRow icon="book-open" title="Documentation" chevron onClick={() => {}} />
          <ListRow icon="info" title="Version" value="4.2.0 (812)" mono />
        </Group>
        <div style={{ padding: '0 16px 32px' }}><Button variant="secondary" size="lg" block>Sign out</Button></div>
      </Scroll>
    </>
  );
}

function ActivityScreen() {
  return (
    <>
      <NavBar title="Activity" large trailing={<IconButton icon="funnel" label="Filter" />} />
      <Scroll>
        <Group label="Today">
          {window.DEPLOYMENTS.slice(0, 4).map((d, i) => {
            const s = window.STATUS[d.status];
            return <ListRow key={i} leading={<Avatar name={d.author} size="sm" />} title={d.msg} subtitle={d.author + ' · ' + d.branch} trailing={<Badge tone={s.tone} dot size="sm">{s.label}</Badge>} chevron onClick={() => {}} />;
          })}
        </Group>
        <Group label="Yesterday">
          {window.DEPLOYMENTS.slice(4).map((d, i) => {
            const s = window.STATUS[d.status];
            return <ListRow key={i} leading={<Avatar name={d.author} size="sm" />} title={d.msg} subtitle={d.author + ' · ' + d.branch} trailing={<Badge tone={s.tone} dot size="sm">{s.label}</Badge>} chevron onClick={() => {}} />;
          })}
        </Group>
      </Scroll>
    </>
  );
}

Object.assign(window, { ProjectsScreen, ProjectScreen, SettingsScreen, ActivityScreen });
