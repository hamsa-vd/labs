const { SidebarNav, Input, Kbd, IconButton, Button, Badge, Icon, Card, Tabs, SegmentedControl } = window.AreyDesignSystem_1909f9;

function DocsHeader() {
  const [dark, setDark] = React.useState(false);
  React.useEffect(() => { document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light'); }, [dark]);
  return (
    <header style={{ position: 'sticky', top: 0, zIndex: 40, height: 'var(--topbar-h)', display: 'flex', alignItems: 'center', gap: 'var(--space-6)', padding: '0 var(--space-8)', background: 'var(--surface-glass)', backdropFilter: 'var(--backdrop-glass)', WebkitBackdropFilter: 'var(--backdrop-glass)', borderBottom: '1px solid var(--border-subtle)' }}>
      <a href="#" style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-primary)' }}>
        <img src="../../assets/logo-mark.svg" style={{ height: 20 }} />
        <span style={{ font: 'var(--weight-semibold) 15px var(--font-sans)', letterSpacing: '-.03em' }}>arey</span>
        <span style={{ width: 1, height: 14, background: 'var(--border-default)' }} />
        <span style={{ font: 'var(--type-label)', color: 'var(--text-secondary)' }}>Docs</span>
      </a>
      <nav style={{ display: 'flex', gap: 'var(--space-5)' }}>
        {['Guides', 'Reference', 'CLI', 'Changelog'].map((n, i) => (
          <a key={n} href="#" style={{ font: 'var(--type-label)', color: i === 0 ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{n}</a>
        ))}
      </nav>
      <div style={{ flex: 1 }} />
      <div style={{ width: 260 }}><Input size="sm" icon="magnifying-glass" placeholder="Search docs" suffix={<Kbd keys="cmd+k" />} /></div>
      <IconButton icon={dark ? 'sun' : 'moon'} label="Toggle theme" onClick={() => setDark(!dark)} />
      <IconButton icon="github-logo" label="GitHub" />
    </header>
  );
}

function CodeBlock({ lang = 'bash', filename, lines }) {
  const [copied, setCopied] = React.useState(false);
  return (
    <div style={{ border: '1px solid var(--border-default)', borderRadius: 'var(--radius-card)', overflow: 'hidden', background: 'var(--bg-base)', margin: '0 0 var(--space-6)', maxWidth: 'var(--prose-max)', boxShadow: 'var(--shadow-sm)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', padding: 'var(--space-2) var(--space-2) var(--space-2) var(--space-4)', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-subtle)' }}>
        <Icon name={filename ? 'file-code' : 'terminal-window'} size={14} color="var(--text-tertiary)" />
        <span style={{ font: 'var(--type-code)', fontSize: 'var(--text-12)', color: 'var(--text-secondary)' }}>{filename || lang}</span>
        <div style={{ flex: 1 }} />
        <IconButton icon={copied ? 'check' : 'copy'} label="Copy code" size="sm" onClick={() => { setCopied(true); setTimeout(() => setCopied(false), 1200); }} />
      </div>
      <pre style={{ margin: 0, padding: 'var(--space-4) var(--space-5)', overflow: 'auto' }}>
        <code style={{ font: 'var(--type-code)', display: 'grid', gap: 2 }}>
          {lines.map((l, i) => (
            <span key={i} style={{ color: l.startsWith('#') || l.startsWith('//') ? 'var(--text-tertiary)' : 'var(--text-body)', whiteSpace: 'pre' }}>
              {l.startsWith('$') ? <><span style={{ color: 'var(--text-tertiary)', userSelect: 'none' }}>$ </span>{l.slice(2)}</> : l}
            </span>
          ))}
        </code>
      </pre>
    </div>
  );
}

const CALLOUT = {
  note: { icon: 'info', color: 'var(--accent-solid)', wash: 'var(--accent-wash)', border: 'var(--accent-border)' },
  warning: { icon: 'warning', color: 'var(--warning-solid)', wash: 'var(--warning-wash)', border: 'var(--warning-solid)' },
  danger: { icon: 'warning-octagon', color: 'var(--danger-solid)', wash: 'var(--danger-wash)', border: 'var(--danger-solid)' },
};

function Callout({ tone = 'note', title, children }) {
  const c = CALLOUT[tone];
  return (
    <div style={{ display: 'flex', gap: 'var(--space-3)', padding: 'var(--space-4) var(--space-5)', background: c.wash, border: '1px solid ' + c.border, borderRadius: 'var(--radius-card)', margin: '0 0 var(--space-6)', maxWidth: 'var(--prose-max)' }}>
      <span style={{ color: c.color, marginTop: 1, display: 'flex' }}><Icon name={c.icon} size={17} weight="fill" /></span>
      <div>
        {title && <div style={{ font: 'var(--type-label)', color: 'var(--text-primary)', marginBottom: 4 }}>{title}</div>}
        <div style={{ font: 'var(--type-body)', color: 'var(--text-body)' }}>{children}</div>
      </div>
    </div>
  );
}

function PropsTable({ rows }) {
  return (
    <div style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-card)', overflow: 'hidden', maxWidth: 'var(--prose-max)', margin: '0 0 var(--space-6)', boxShadow: 'var(--shadow-sm)', background: 'var(--surface-card)' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead><tr>{['Prop', 'Type', 'Default'].map((h) => (
          <th key={h} style={{ textAlign: 'left', font: 'var(--type-eyebrow)', letterSpacing: 'var(--tracking-eyebrow)', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 'var(--weight-medium)', padding: 'var(--space-3) var(--space-4)', background: 'var(--bg-subtle)', borderBottom: '1px solid var(--border-subtle)' }}>{h}</th>
        ))}</tr></thead>
        <tbody>{rows.map((r, i) => (
          <tr key={i}>
            <td style={{ padding: 'var(--space-3) var(--space-4)', borderTop: i ? '1px solid var(--border-subtle)' : 0, font: 'var(--type-code)', color: 'var(--text-primary)' }}>{r[0]}</td>
            <td style={{ padding: 'var(--space-3) var(--space-4)', borderTop: i ? '1px solid var(--border-subtle)' : 0, font: 'var(--type-code)', color: 'var(--text-accent)' }}>{r[1]}</td>
            <td style={{ padding: 'var(--space-3) var(--space-4)', borderTop: i ? '1px solid var(--border-subtle)' : 0, font: 'var(--type-code)', color: 'var(--text-tertiary)' }}>{r[2]}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function OnThisPage({ items, active, onSelect }) {
  return (
    <aside style={{ width: 216, flex: 'none', position: 'sticky', top: 'calc(var(--topbar-h) + var(--space-10))', alignSelf: 'flex-start', display: 'grid', gap: 'var(--space-3)' }}>
      <div style={{ font: 'var(--type-eyebrow)', letterSpacing: 'var(--tracking-eyebrow)', textTransform: 'uppercase', color: 'var(--text-tertiary)' }}>On this page</div>
      <div style={{ display: 'grid', gap: 'var(--space-2)', borderLeft: '1px solid var(--border-subtle)' }}>
        {items.map((it) => (
          <a key={it.id} href={'#' + it.id} onClick={() => onSelect(it.id)}
            style={{ font: 'var(--type-label)', paddingLeft: 'var(--space-4)', marginLeft: -1, borderLeft: '1px solid ' + (active === it.id ? 'var(--text-primary)' : 'transparent'), color: active === it.id ? 'var(--text-primary)' : 'var(--text-secondary)', paddingTop: 2, paddingBottom: 2 }}>{it.label}</a>
        ))}
      </div>
      <div style={{ marginTop: 'var(--space-4)', display: 'grid', gap: 'var(--space-2)' }}>
        <a href="#" style={{ font: 'var(--type-caption)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}><Icon name="pencil-simple" size={13} />Edit this page</a>
        <a href="#" style={{ font: 'var(--type-caption)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}><Icon name="chat-circle" size={13} />Send feedback</a>
      </div>
    </aside>
  );
}

Object.assign(window, { DocsHeader, CodeBlock, Callout, PropsTable, OnThisPage });
