const { Icon, IconButton, Badge, List, ListRow, Switch, SegmentedControl, Button, Avatar, ProgressBar, Card } = window.AreyDesignSystem_1909f9;

/* A neutral phone shell — bezel, status bar, home indicator. No vendor branding. */
function Phone({ children, label }) {
  return (
    <div style={{ display: 'grid', gap: 'var(--space-4)', justifyItems: 'center' }}>
      <div style={{ width: 375, height: 720, borderRadius: 46, padding: 10, background: 'var(--grey-1000)', boxShadow: 'var(--shadow-xl)', flex: 'none' }}>
        <div style={{ position: 'relative', width: '100%', height: '100%', borderRadius: 36, overflow: 'hidden', background: 'var(--bg-canvas)', display: 'flex', flexDirection: 'column' }}>
          {children}
        </div>
      </div>
      {label && <div style={{ font: 'var(--type-eyebrow)', letterSpacing: 'var(--tracking-eyebrow)', textTransform: 'uppercase', color: 'var(--text-tertiary)' }}>{label}</div>}
    </div>
  );
}

function StatusBar() {
  return (
    <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 44, display: 'flex', alignItems: 'center', padding: '0 24px', zIndex: 20, pointerEvents: 'none' }}>
      <span style={{ font: 'var(--weight-semibold) 13px var(--font-sans)', color: 'var(--text-primary)', letterSpacing: 0 }}>9:41</span>
      <div style={{ flex: 1 }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--text-primary)' }}>
        <Icon name="cell-signal-full" size={15} weight="fill" />
        <Icon name="wifi-high" size={15} weight="bold" />
        <Icon name="battery-full" size={17} weight="fill" />
      </div>
    </div>
  );
}

function HomeIndicator() {
  return <div style={{ position: 'absolute', bottom: 7, left: 0, right: 0, display: 'grid', placeItems: 'center', zIndex: 30, pointerEvents: 'none' }}><div style={{ width: 134, height: 5, borderRadius: 3, background: 'var(--text-primary)', opacity: .85 }} /></div>;
}

/* Glass nav bar. Compact form shows a centred title; large form shows the 34px title below. */
function NavBar({ title, large, back, trailing, onBack }) {
  return (
    <div style={{ position: 'sticky', top: 0, zIndex: 15, background: 'var(--surface-glass)', backdropFilter: 'var(--backdrop-glass)', WebkitBackdropFilter: 'var(--backdrop-glass)', borderBottom: '1px solid var(--border-subtle)' }}>
      <div style={{ height: 44 }} />
      <div style={{ height: 44, display: 'flex', alignItems: 'center', padding: '0 8px' }}>
        {back ? (
          <button onClick={onBack} style={{ display: 'flex', alignItems: 'center', gap: 2, height: 44, padding: '0 8px', border: 0, background: 'none', color: 'var(--accent-solid)', font: 'var(--weight-regular) 17px var(--font-sans)', letterSpacing: '-.01em', cursor: 'pointer' }}>
            <Icon name="caret-left" size={20} weight="bold" />{back}
          </button>
        ) : <div style={{ width: 60 }} />}
        <div style={{ flex: 1, textAlign: 'center', font: 'var(--weight-semibold) 17px var(--font-sans)', letterSpacing: '-.02em', color: 'var(--text-primary)', opacity: large ? 0 : 1, transition: 'opacity var(--duration-fast) var(--ease-out)' }}>{title}</div>
        <div style={{ minWidth: 60, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>{trailing}</div>
      </div>
      {large && (
        <div style={{ padding: '0 20px 8px' }}>
          <div style={{ font: 'var(--weight-bold) 34px/1.1 var(--font-sans)', letterSpacing: '-.032em', color: 'var(--text-primary)' }}>{title}</div>
        </div>
      )}
    </div>
  );
}

function TabBar({ value, onChange }) {
  const items = [
    { value: 'projects', label: 'Projects', icon: 'squares-four' },
    { value: 'activity', label: 'Activity', icon: 'pulse' },
    { value: 'search', label: 'Search', icon: 'magnifying-glass' },
    { value: 'settings', label: 'Settings', icon: 'gear-six' },
  ];
  return (
    <div style={{ position: 'sticky', bottom: 0, zIndex: 25, background: 'var(--surface-glass)', backdropFilter: 'var(--backdrop-glass)', WebkitBackdropFilter: 'var(--backdrop-glass)', borderTop: '1px solid var(--border-subtle)', paddingBottom: 22 }}>
      <div style={{ display: 'grid', gridAutoFlow: 'column', gridAutoColumns: '1fr', paddingTop: 8 }}>
        {items.map((it) => {
          const on = value === it.value;
          return (
            <button key={it.value} onClick={() => onChange(it.value)} style={{ display: 'grid', justifyItems: 'center', gap: 3, border: 0, background: 'none', cursor: 'pointer', padding: '2px 0', color: on ? 'var(--accent-solid)' : 'var(--text-tertiary)', transition: 'color var(--duration-fast) var(--ease-out)' }}>
              <Icon name={it.icon} size={24} weight={on ? 'fill' : 'regular'} />
              <span style={{ font: 'var(--weight-medium) 10px var(--font-sans)', letterSpacing: 0 }}>{it.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Scroll({ children }) {
  return <div style={{ flex: 1, overflow: 'auto', WebkitOverflowScrolling: 'touch' }}>{children}</div>;
}

function GroupLabel({ children }) {
  return <div style={{ font: 'var(--type-eyebrow)', letterSpacing: 'var(--tracking-eyebrow)', textTransform: 'uppercase', color: 'var(--text-tertiary)', padding: '0 20px var(--space-2)' }}>{children}</div>;
}

function Group({ label, children, footer }) {
  return (
    <div style={{ display: 'grid', gap: 'var(--space-2)', margin: '0 0 var(--space-6)' }}>
      {label && <GroupLabel>{label}</GroupLabel>}
      <div style={{ margin: '0 16px' }}><List inset>{children}</List></div>
      {footer && <div style={{ font: 'var(--type-caption)', color: 'var(--text-secondary)', padding: '0 20px' }}>{footer}</div>}
    </div>
  );
}

/* Bottom sheet — 20px top radius, rises with a spring. */
function Sheet({ open, title, onClose, children, actions }) {
  if (!open) return null;
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 40, display: 'flex', alignItems: 'flex-end', background: 'var(--surface-scrim)', animation: 'arey-fade var(--duration-normal) var(--ease-out)' }} onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: '100%', background: 'var(--surface-raised)', borderRadius: 'var(--radius-sheet) var(--radius-sheet) 0 0', boxShadow: 'var(--shadow-xl)', paddingBottom: 34, animation: 'arey-rise var(--duration-slow) var(--ease-out)' }}>
        <div style={{ display: 'grid', placeItems: 'center', padding: '8px 0 4px' }}><div style={{ width: 36, height: 5, borderRadius: 3, background: 'var(--border-strong)' }} /></div>
        <div style={{ display: 'flex', alignItems: 'center', padding: '4px 16px 12px' }}>
          <div style={{ flex: 1, font: 'var(--weight-semibold) 17px var(--font-sans)', letterSpacing: '-.02em', color: 'var(--text-primary)' }}>{title}</div>
          <IconButton icon="x" label="Close" size="sm" onClick={onClose} />
        </div>
        <div style={{ padding: '0 16px' }}>{children}</div>
        {actions && <div style={{ display: 'grid', gap: 'var(--space-2)', padding: '16px 16px 0' }}>{actions}</div>}
      </div>
    </div>
  );
}

Object.assign(window, { Phone, StatusBar, HomeIndicator, NavBar, TabBar, Scroll, Group, GroupLabel, Sheet });
