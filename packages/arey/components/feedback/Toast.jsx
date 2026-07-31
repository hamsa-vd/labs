import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { Icon } from '../core/Icon.jsx';
import { IconButton } from '../core/IconButton.jsx';

injectSheet('arey-toast', `
.arey-toast{display:flex;align-items:flex-start;gap:var(--space-3);min-width:280px;max-width:400px;
  padding:var(--space-4);border-radius:var(--radius-card);
  background:var(--surface-overlay);border:1px solid var(--border-glass);
  backdrop-filter:var(--backdrop-glass);-webkit-backdrop-filter:var(--backdrop-glass);
  box-shadow:var(--shadow-lg);color:var(--text-body);
  animation:arey-toast-in var(--duration-normal) var(--ease-out)}
.arey-toast__icon{margin-top:1px;color:var(--text-tertiary)}
.arey-toast--success .arey-toast__icon{color:var(--success-solid)}
.arey-toast--danger .arey-toast__icon{color:var(--danger-solid)}
.arey-toast--warning .arey-toast__icon{color:var(--warning-solid)}
.arey-toast__title{font:var(--type-label);color:var(--text-primary)}
.arey-toast__desc{font:var(--type-caption);color:var(--text-secondary);margin-top:2px}
.arey-toast-region{position:fixed;z-index:120;right:var(--space-6);bottom:var(--space-6);
  display:flex;flex-direction:column;gap:var(--space-3);align-items:flex-end}
@keyframes arey-toast-in{from{opacity:0;transform:translateY(8px) scale(.98)}to{opacity:1;transform:none}}
`);

const ICONS = { neutral: 'info', success: 'check-circle', danger: 'warning-octagon', warning: 'warning' };

/** Transient confirmation on a glass surface. One line of what happened. */
export function Toast({ tone = 'neutral', title, description, action, onDismiss, className, ...rest }) {
  return (
    <div className={cx('arey-toast', tone !== 'neutral' && 'arey-toast--' + tone, className)} role="status" {...rest}>
      <span className="arey-toast__icon"><Icon name={ICONS[tone]} size={16} weight="fill" /></span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="arey-toast__title">{title}</div>
        {description && <div className="arey-toast__desc">{description}</div>}
        {action && <div style={{ marginTop: 'var(--space-3)' }}>{action}</div>}
      </div>
      {onDismiss && <IconButton icon="x" label="Dismiss" size="sm" onClick={onDismiss} />}
    </div>
  );
}

/** Bottom-right stack. */
export function ToastRegion({ children }) {
  return <div className="arey-toast-region">{children}</div>;
}
