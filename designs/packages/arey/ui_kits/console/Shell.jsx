const { SidebarNav, IconButton, Breadcrumbs, Avatar, Badge, Kbd, Input, Button, Icon, ProgressBar } = window.AreyDesignSystem_1909f9;

function ThemeToggle() {
  const [dark, setDark] = React.useState(document.documentElement.getAttribute('data-theme') === 'dark');
  React.useEffect(() => { document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light'); }, [dark]);
  return <IconButton icon={dark ? 'sun' : 'moon'} label="Toggle theme" onClick={() => setDark(!dark)} />;
}

function Sidebar({ page, setPage }) {
  return (
    <aside style={{ width: 'var(--sidebar-w)', flex: 'none', borderRight: '1px solid var(--border-subtle)', background: 'var(--bg-base)', display: 'flex', flexDirection: 'column', position: 'sticky', top: 0, height: '100vh' }}>
      <div style={{ height: 'var(--topbar-h)', display: 'flex', alignItems: 'center', gap: 10, padding: '0 var(--space-4)', borderBottom: '1px solid var(--border-subtle)' }}>
        <img src="../../assets/logo-mark.svg" style={{ height: 20, color: 'var(--text-primary)' }} />
        <span style={{ font: 'var(--weight-semibold) 15px var(--font-sans)', letterSpacing: '-.03em', color: 'var(--text-primary)' }}>arey</span>
        <span style={{ width: 1, height: 14, background: 'var(--border-default)' }} />
        <span style={{ font: 'var(--type-label)', color: 'var(--text-secondary)' }}>Console</span>
      </div>
      <div style={{ padding: 'var(--space-4) var(--space-4) 0' }}>
        <button style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: 'var(--space-2) var(--space-3)', background: 'var(--bg-subtle)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-control)', cursor: 'pointer', textAlign: 'left' }}>
          <Avatar name="Riya Menon" size="sm" />
          <span style={{ flex: 1, font: 'var(--type-label)', color: 'var(--text-primary)' }}>riya</span>
          <Icon name="caret-up-down" size={13} color="var(--text-tertiary)" />
        </button>
      </div>
      <div style={{ flex: 1, overflow: 'auto', maskImage: 'linear-gradient(to bottom, #000 calc(100% - 24px), transparent)' }}>
        <SidebarNav value={page} onChange={setPage} groups={[
          { items: [
            { value: 'overview', label: 'Overview', icon: 'squares-four' },
            { value: 'deployments', label: 'Deployments', icon: 'rocket-launch', count: 24 },
            { value: 'analytics', label: 'Analytics', icon: 'chart-line' },
            { value: 'logs', label: 'Logs', icon: 'terminal-window' },
          ] },
          { label: 'Project', items: [
            { value: 'domains', label: 'Domains', icon: 'globe-hemisphere-west' },
            { value: 'storage', label: 'Storage', icon: 'database' },
            { value: 'env', label: 'Environment', icon: 'sliders-horizontal' },
          ] },
          { label: 'Team', items: [
            { value: 'members', label: 'Members', icon: 'users-three', count: 4 },
            { value: 'usage', label: 'Usage', icon: 'gauge' },
            { value: 'settings', label: 'Settings', icon: 'gear-six' },
          ] },
        ]} />
      </div>
      <div style={{ padding: 'var(--space-4)', borderTop: '1px solid var(--border-subtle)', display: 'grid', gap: 'var(--space-2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', font: 'var(--type-caption)', color: 'var(--text-secondary)' }}>
          <span>Hobby plan</span><span style={{ fontFamily: 'var(--font-mono)' }}>68 %</span>
        </div>
        <ProgressBar value={68} />
        <Button size="sm" variant="secondary" block iconLeft="lightning">Upgrade</Button>
      </div>
    </aside>
  );
}

function TopBar({ crumbs, actions }) {
  return (
    <header style={{ position: 'sticky', top: 0, zIndex: 30, height: 'var(--topbar-h)', display: 'flex', alignItems: 'center', gap: 'var(--space-4)', padding: '0 var(--space-8)', background: 'var(--surface-glass)', backdropFilter: 'var(--backdrop-glass)', WebkitBackdropFilter: 'var(--backdrop-glass)', borderBottom: '1px solid var(--border-subtle)' }}>
      <div style={{ flex: '0 0 auto' }}><Breadcrumbs items={crumbs} /></div>
      <div style={{ flex: 1, minWidth: 'var(--space-4)' }} />
      <div style={{ width: 240, minWidth: 120, flexShrink: 1 }}>
        <Input size="sm" icon="magnifying-glass" placeholder="Search" suffix={<Kbd keys="cmd+k" />} />
      </div>
      {actions}
      <ThemeToggle />
      <IconButton icon="bell" label="Notifications" />
      <Avatar name="Riya Menon" size="sm" />
    </header>
  );
}

function PageHead({ eyebrow, title, description, actions }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 'var(--space-6)', marginBottom: 'var(--space-8)' }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        {eyebrow && <div style={{ font: 'var(--type-eyebrow)', letterSpacing: 'var(--tracking-eyebrow)', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 'var(--space-3)' }}>{eyebrow}</div>}
        <h1 style={{ font: 'var(--type-title-1)', letterSpacing: 'var(--tracking-heading)' }}>{title}</h1>
        {description && <p style={{ font: 'var(--type-body-lg)', color: 'var(--text-secondary)', marginTop: 'var(--space-2)', maxWidth: '60ch' }}>{description}</p>}
      </div>
      <div style={{ display: 'flex', gap: 'var(--space-3)', flex: 'none' }}>{actions}</div>
    </div>
  );
}

function Page({ children }) {
  return <div style={{ maxWidth: 'var(--content-max)', margin: '0 auto', padding: 'var(--space-12) var(--space-8) var(--space-20)' }}>{children}</div>;
}

function StatusDot({ status }) {
  const map = { ready: 'var(--success-solid)', building: 'var(--warning-solid)', failed: 'var(--danger-solid)', queued: 'var(--grey-400)' };
  return <span style={{ width: 7, height: 7, borderRadius: 9, background: map[status], flex: 'none', boxShadow: status === 'building' ? '0 0 0 3px var(--warning-wash)' : undefined }} />;
}

Object.assign(window, { Sidebar, TopBar, PageHead, Page, StatusDot, ThemeToggle });
