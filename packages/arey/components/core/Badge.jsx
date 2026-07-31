import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { Icon } from './Icon.jsx';

injectSheet('arey-badge', `
.arey-badge{display:inline-flex;align-items:center;gap:var(--space-2);height:24px;padding:0 var(--space-3);
  border-radius:var(--radius-full);font:var(--type-caption);font-weight:var(--weight-medium);
  background:var(--bg-inset);color:var(--text-secondary);white-space:nowrap;border:1px solid transparent}
.arey-badge--sm{height:20px;padding:0 var(--space-2);font-size:var(--text-11)}
.arey-badge__dot{width:6px;height:6px;border-radius:50%;background:currentColor;flex:none}
.arey-badge--accent{background:var(--accent-wash);color:var(--text-accent)}
.arey-badge--success{background:var(--success-wash);color:var(--success-text)}
.arey-badge--danger{background:var(--danger-wash);color:var(--danger-text)}
.arey-badge--warning{background:var(--warning-wash);color:var(--warning-text)}
.arey-badge--outline{background:transparent;border-color:var(--border-default);color:var(--text-secondary)}
.arey-badge--mono{font-family:var(--font-mono);letter-spacing:0}
`);

/** Status pill. Wash + text pair, optional 6px dot. */
export function Badge({ tone = 'neutral', dot = false, icon, size = 'md', mono = false, className, children, ...rest }) {
  return (
    <span className={cx('arey-badge', tone !== 'neutral' && 'arey-badge--' + tone, size === 'sm' && 'arey-badge--sm', mono && 'arey-badge--mono', className)} {...rest}>
      {dot && <span className="arey-badge__dot" />}
      {icon && <Icon name={icon} size={12} weight="bold" />}
      {children}
    </span>
  );
}
