const { Card, Badge, Button, IconButton, Tag, Avatar, AvatarStack, ProgressBar, SegmentedControl, Tooltip, EmptyState, Icon } = window.AreyDesignSystem_1909f9;

function MetricCard({ label, value, unit, delta, sub, children }) {
  return (
    <Card>
      <div style={{ font: 'var(--type-eyebrow)', letterSpacing: 'var(--tracking-eyebrow)', textTransform: 'uppercase', color: 'var(--text-tertiary)' }}>{label}</div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 'var(--space-3)' }}>
        <span style={{ font: 'var(--weight-semibold) var(--text-36)/1 var(--font-sans)', letterSpacing: 'var(--tracking-heading)', color: 'var(--text-primary)' }}>{value}</span>
        {unit && <span style={{ font: 'var(--type-body)', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>{unit}</span>}
        {delta && <span style={{ marginLeft: 'auto', font: 'var(--type-caption)', fontFamily: 'var(--font-mono)', color: delta[0] === '-' ? 'var(--danger-text)' : 'var(--success-text)' }}>{delta}</span>}
      </div>
      {sub && <div style={{ font: 'var(--type-caption)', color: 'var(--text-secondary)', marginTop: 'var(--space-2)' }}>{sub}</div>}
      {children && <div style={{ marginTop: 'var(--space-4)' }}>{children}</div>}
    </Card>
  );
}

function Sparkline({ points, tone = 'var(--accent-solid)' }) {
  const max = Math.max(...points);
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, height: 44 }}>
      {points.map((p, i) => (
        <div key={i} style={{ flex: 1, height: Math.max(3, (p / max) * 44), background: i === points.length - 1 ? tone : 'var(--bg-inset)', borderRadius: 2, transition: 'height var(--duration-slow) var(--ease-out)' }} />
      ))}
    </div>
  );
}

function ProjectCard({ p, onOpen }) {
  const s = window.STATUS[p.status];
  return (
    <Card interactive onClick={onOpen} padded={false} style={{ display: 'grid' }}>
      <div style={{ padding: 'var(--space-5)', display: 'grid', gap: 'var(--space-4)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <Avatar name={p.name.replace('arey-', '')} square tone="accent" />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ font: 'var(--type-title-3)', letterSpacing: 'var(--tracking-heading)', color: 'var(--text-primary)' }}>{p.name}</div>
            <div style={{ font: 'var(--type-caption)', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>{p.name}.arey.app</div>
          </div>
          <Badge tone={s.tone} dot size="sm">{s.label}</Badge>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', font: 'var(--type-caption)', color: 'var(--text-secondary)' }}>
          <Icon name="git-branch" size={13} />
          <span style={{ fontFamily: 'var(--font-mono)' }}>{p.branch}</span>
          <span style={{ color: 'var(--border-strong)' }}>·</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{p.sha}</span>
          <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)' }}>{p.time}</span>
        </div>
      </div>
    </Card>
  );
}

function Overview({ onOpenProject }) {
  const [range, setRange] = React.useState('7d');
  return (
    <Page>
      <PageHead
        eyebrow="Team riya"
        title="Overview"
        description="Six projects, four members. Everything is deploying from main."
        actions={[
          <Button key="a" variant="secondary" iconLeft="arrow-square-out">Visit site</Button>,
          <Button key="b" variant="primary" iconLeft="plus">New project</Button>,
        ]}
      />
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
        <div style={{ font: 'var(--type-title-3)', letterSpacing: 'var(--tracking-heading)', color: 'var(--text-primary)' }}>Usage</div>
        <div style={{ width: 220, marginLeft: 'auto' }}>
          <SegmentedControl value={range} onChange={setRange} options={[{ value: '24h', label: 'Day' }, { value: '7d', label: 'Week' }, { value: '30d', label: 'Month' }]} />
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 'var(--space-5)', marginBottom: 'var(--space-12)' }}>
        <MetricCard label="Bandwidth" value="412" unit="GB" delta="+8.2 %" sub="of 1 TB included">
          <ProgressBar value={41} />
        </MetricCard>
        <MetricCard label="Requests" value="2.4" unit="M" delta="+12.6 %" sub="Edge and function calls">
          <Sparkline points={[12, 18, 14, 22, 26, 21, 34]} />
        </MetricCard>
        <MetricCard label="p95 latency" value="184" unit="ms" delta="-6.1 %" sub="Across 18 regions">
          <Sparkline points={[30, 28, 32, 24, 22, 20, 18]} tone="var(--success-solid)" />
        </MetricCard>
        <MetricCard label="Build minutes" value="1 240" unit="min" delta="+3.4 %" sub="94 % of the monthly limit">
          <ProgressBar value={94} tone="warning" />
        </MetricCard>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-5)' }}>
        <div style={{ font: 'var(--type-title-3)', letterSpacing: 'var(--tracking-heading)', color: 'var(--text-primary)' }}>Projects</div>
        <Badge mono size="sm">6</Badge>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 'var(--space-2)' }}>
          <Tag icon="funnel" onClick={() => {}} selected>Production</Tag>
          <Tag onClick={() => {}}>All branches</Tag>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-5)' }}>
        {window.PROJECTS.map((p) => <ProjectCard key={p.name} p={p} onOpen={onOpenProject} />)}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-5)', marginTop: 'var(--space-12)' }}>
        <Card title="Activity" description="Last 24 hours" padded={false} action={<Button variant="link">View all</Button>}>
          <div style={{ display: 'grid' }}>
            {window.DEPLOYMENTS.slice(0, 4).map((d, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', padding: 'var(--space-4) var(--space-6)', borderTop: '1px solid var(--border-subtle)' }}>
                <Avatar name={d.author} size="sm" />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ font: 'var(--type-label)', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.msg}</div>
                  <div style={{ font: 'var(--type-caption)', color: 'var(--text-secondary)' }}>{d.author} pushed to <span style={{ fontFamily: 'var(--font-mono)' }}>{d.branch}</span></div>
                </div>
                <Tooltip mono label="2026-07-31 14:02 UTC"><span style={{ font: 'var(--type-code)', color: 'var(--text-tertiary)' }}>{d.time}</span></Tooltip>
              </div>
            ))}
          </div>
        </Card>
        <Card title="Members" action={<Button variant="link">Invite</Button>} padded={false}>
          <div style={{ display: 'grid' }}>
            {window.MEMBERS.map((m) => (
              <div key={m.email} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', padding: 'var(--space-3) var(--space-6)', borderTop: '1px solid var(--border-subtle)' }}>
                <Avatar name={m.name} size="sm" />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ font: 'var(--type-label)', color: 'var(--text-primary)' }}>{m.name}</div>
                  <div style={{ font: 'var(--type-caption)', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>{m.email}</div>
                </div>
                <Badge tone={m.role === 'Owner' ? 'accent' : 'outline'} size="sm">{m.role}</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </Page>
  );
}

Object.assign(window, { Overview, MetricCard, Sparkline });
