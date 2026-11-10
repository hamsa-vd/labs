import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-avatar', `
.arey-avatar{--_s:32px;position:relative;display:inline-grid;place-items:center;flex:none;width:var(--_s);height:var(--_s);
  border-radius:var(--radius-full);background:var(--bg-inset);color:var(--text-secondary);overflow:hidden;
  font:var(--weight-medium) calc(var(--_s) * .38)/1 var(--font-sans);letter-spacing:0;
  box-shadow:0 0 0 1px var(--border-subtle) inset;user-select:none}
.arey-avatar img{width:100%;height:100%;object-fit:cover;display:block}
.arey-avatar--xs{--_s:20px}.arey-avatar--sm{--_s:24px}.arey-avatar--lg{--_s:40px}.arey-avatar--xl{--_s:56px}
.arey-avatar--square{border-radius:var(--radius-md)}
.arey-avatar--accent{background:var(--accent-wash);color:var(--text-accent)}
.arey-avatar-stack{display:inline-flex}
.arey-avatar-stack > .arey-avatar{box-shadow:0 0 0 2px var(--surface-card)}
.arey-avatar-stack > .arey-avatar + .arey-avatar{margin-left:-8px}
`);

function initials(name) {
  return String(name || '').trim().split(/\s+/).slice(0, 2).map(function (p) { return p[0]; }).join('').toUpperCase();
}

/** Person or project identity. Pill by default, square for projects. */
export function Avatar({ name, src, size = 'md', square = false, tone = 'neutral', className, ...rest }) {
  return (
    <span
      className={cx('arey-avatar', size !== 'md' && 'arey-avatar--' + size, square && 'arey-avatar--square', tone === 'accent' && 'arey-avatar--accent', className)}
      title={name}
      {...rest}
    >
      {src ? <img src={src} alt={name || ''} /> : initials(name)}
    </span>
  );
}

/** Overlapping row of avatars. */
export function AvatarStack({ people = [], max = 4, size = 'sm' }) {
  const shown = people.slice(0, max);
  const rest = people.length - shown.length;
  return (
    <span className="arey-avatar-stack">
      {shown.map(function (p, i) { return <Avatar key={i} size={size} name={p.name} src={p.src} />; })}
      {rest > 0 && <Avatar size={size} name={'+' + rest} />}
    </span>
  );
}
