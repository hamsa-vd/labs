const { Card, Badge, Button, IconButton, Tabs, Input, Select, Tooltip, Avatar, Dialog, Field, Icon, Kbd, EmptyState, Spinner } = window.AreyDesignSystem_1909f9;

function Th({ children, align }) {
  return <th style={{ textAlign: align || 'left', font: 'var(--type-eyebrow)', letterSpacing: 'var(--tracking-eyebrow)', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 'var(--weight-medium)', padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-subtle)', whiteSpace: 'nowrap' }}>{children}</th>;
}
function Td({ children, align, mono }) {
  return <td style={{ textAlign: align || 'left', padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-subtle)', font: mono ? 'var(--type-code)' : 'var(--type-body)', color: 'var(--text-body)', whiteSpace: 'nowrap' }}>{children}</td>;
}

function DeploymentsTable({ rows, onSelect }) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead><tr>
        <Th>Status</Th><Th>Deployment</Th><Th>Environment</Th><Th>Branch</Th><Th>Author</Th><Th align="right">Duration</Th><Th align="right">Created</Th><Th />
      </tr></thead>
      <tbody>
        {rows.map((d, i) => {
          const s = window.STATUS[d.status];
          return (
            <tr key={i} onClick={() => onSelect(d)} style={{ cursor: 'pointer', transition: 'background-color var(--duration-fast) var(--ease-out)' }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-hover)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}>
              <Td><Badge tone={s.tone} dot size="sm">{s.label}</Badge></Td>
              <Td>
                <div style={{ display: 'grid', gap: 2 }}>
                  <span style={{ font: 'var(--type-label)', color: 'var(--text-primary)' }}>{d.msg}</span>
                  <span style={{ font: 'var(--type-code)', fontSize: 'var(--text-11)', color: 'var(--text-tertiary)' }}>{d.sha}</span>
                </div>
              </Td>
              <Td><Badge tone={d.env === 'Production' ? 'accent' : 'outline'} size="sm">{d.env}</Badge></Td>
              <Td mono>{d.branch}</Td>
              <Td><span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Avatar name={d.author} size="xs" />{d.author}</span></Td>
              <Td mono align="right">{d.dur}</Td>
              <Td align="right"><Tooltip mono label="2026-07-31 14:02 UTC"><span style={{ font: 'var(--type-code)', color: 'var(--text-secondary)' }}>{d.time}</span></Tooltip></Td>
              <Td align="right"><IconButton icon="dots-three" label="Options" size="sm" /></Td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

const LOG = [
  ['14:02:11', 'Cloning github.com/riya/arey-web (branch: main, sha: a3f91c8)'],
  ['14:02:13', 'Restored build cache in 412 ms'],
  ['14:02:13', 'Running "npm install"'],
  ['14:02:29', 'added 284 packages in 15 s'],
  ['14:02:30', 'Running "npm run build"'],
  ['14:02:52', 'Compiled successfully in 21.4 s'],
  ['14:02:54', 'Uploading 38 static assets (4.2 MB)'],
  ['14:02:58', 'Deployment ready — https://arey-web.arey.app'],
];

function DeploymentDetail({ d, onBack }) {
  const s = window.STATUS[d.status];
  return (
    <Page>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-6)' }}>
        <Button variant="ghost" size="sm" iconLeft="arrow-left" onClick={onBack}>Deployments</Button>
      </div>
      <PageHead
        eyebrow={d.env}
        title={d.msg}
        description={<span>Commit <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{d.sha}</span> on <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{d.branch}</span>, by {d.author}.</span>}
        actions={[
          <Button key="1" variant="secondary" iconLeft="arrow-counter-clockwise">Redeploy</Button>,
          <Button key="2" variant="primary" iconLeft="arrow-up-right" as="a" href="#">Visit</Button>,
        ]}
      />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 'var(--space-5)', alignItems: 'start' }}>
        <Card title="Build log" description="Retained for 30 days" padded={false} action={<IconButton icon="download-simple" label="Download log" size="sm" />}>
          <div style={{ borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-inset)', padding: 'var(--space-4) var(--space-5)', display: 'grid', gap: 6, borderRadius: '0 0 15px 15px' }}>
            {LOG.map(([t, l], i) => (
              <div key={i} style={{ display: 'flex', gap: 'var(--space-4)', font: 'var(--type-code)' }}>
                <span style={{ color: 'var(--text-tertiary)', flex: 'none' }}>{t}</span>
                <span style={{ color: i === LOG.length - 1 ? 'var(--success-text)' : 'var(--text-body)' }}>{l}</span>
              </div>
            ))}
            {d.status === 'building' && <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'center', font: 'var(--type-code)', color: 'var(--text-secondary)' }}><Spinner size={12} /> Building…</div>}
          </div>
        </Card>
        <div style={{ display: 'grid', gap: 'var(--space-5)' }}>
          <Card title="Status">
            <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
              {[['State', <Badge tone={s.tone} dot size="sm">{s.label}</Badge>], ['Duration', d.dur], ['Created', d.time], ['Region', 'iad1'], ['Runtime', 'node-20']].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-4)' }}>
                  <span style={{ font: 'var(--type-caption)', color: 'var(--text-secondary)' }}>{k}</span>
                  <span style={{ font: 'var(--type-code)', color: 'var(--text-primary)' }}>{v}</span>
                </div>
              ))}
            </div>
          </Card>
          <Card variant="inset">
            <div style={{ font: 'var(--type-eyebrow)', letterSpacing: 'var(--tracking-eyebrow)', textTransform: 'uppercase', color: 'var(--text-tertiary)' }}>Domain</div>
            <div style={{ font: 'var(--type-code)', color: 'var(--text-primary)', marginTop: 'var(--space-3)', wordBreak: 'break-all' }}>arey-web.arey.app</div>
            <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-4)' }}>
              <Button size="sm" iconLeft="copy">Copy</Button>
              <Button size="sm" variant="ghost" iconLeft="arrow-square-out">Open</Button>
            </div>
          </Card>
        </div>
      </div>
    </Page>
  );
}

function Deployments({ onSelect }) {
  const [tab, setTab] = React.useState('all');
  const [q, setQ] = React.useState('');
  const [showNew, setShowNew] = React.useState(false);
  const rows = window.DEPLOYMENTS
    .filter((d) => tab === 'all' || (tab === 'prod' ? d.env === 'Production' : d.env === 'Preview'))
    .filter((d) => d.msg.toLowerCase().includes(q.toLowerCase()) || d.branch.includes(q));
  return (
    <Page>
      <PageHead
        eyebrow="arey-web"
        title="Deployments"
        description="Every build for this project, newest first."
        actions={[<Button key="1" variant="secondary" iconLeft="funnel">Filters</Button>, <Button key="2" variant="primary" iconLeft="plus" onClick={() => setShowNew(true)}>New deployment</Button>]}
      />
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
        <Tabs value={tab} onChange={setTab} items={[{ value: 'all', label: 'All', count: window.DEPLOYMENTS.length }, { value: 'prod', label: 'Production' }, { value: 'preview', label: 'Preview' }]} />
        <div style={{ flex: 1 }} />
        <div style={{ width: 260 }}><Input size="sm" icon="magnifying-glass" placeholder="Search deployments" value={q} onChange={(e) => setQ(e.target.value)} /></div>
        <div style={{ width: 150 }}><Select size="sm" options={['All branches', 'main', 'feat/usage']} /></div>
      </div>
      <Card padded={false} variant="flat">
        {rows.length ? <DeploymentsTable rows={rows} onSelect={onSelect} /> : <EmptyState compact icon="magnifying-glass" title="No deployments match" description="Try a different branch or search term." action={<Button onClick={() => setQ('')}>Clear search</Button>} />}
      </Card>
      <Dialog
        open={showNew}
        onClose={() => setShowNew(false)}
        title="New deployment"
        description="Deploy the current head of a branch to a preview URL."
        footer={<><Button onClick={() => setShowNew(false)}>Cancel</Button><Button variant="primary" onClick={() => setShowNew(false)}>Deploy</Button></>}
      >
        <div style={{ display: 'grid', gap: 'var(--space-5)' }}>
          <Field label="Branch"><Select options={['main', 'feat/usage', 'fix/focus']} /></Field>
          <Field label="Commit" hint="Leave empty to use the branch head"><Input mono placeholder="a3f91c8" /></Field>
        </div>
      </Dialog>
    </Page>
  );
}

Object.assign(window, { Deployments, DeploymentDetail, DeploymentsTable, Th, Td });
