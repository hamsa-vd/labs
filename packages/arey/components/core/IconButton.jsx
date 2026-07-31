import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { Icon } from './Icon.jsx';

injectSheet('arey-iconbutton', `
.arey-iconbtn{--_s:36px;display:inline-flex;align-items:center;justify-content:center;flex:none;
  width:var(--_s);height:var(--_s);border-radius:var(--radius-control);border:1px solid transparent;
  background:transparent;color:var(--text-secondary);cursor:pointer;transition:var(--transition-control);
  -webkit-tap-highlight-color:transparent}
.arey-iconbtn:hover:not(:disabled){background:var(--bg-hover);color:var(--text-primary)}
.arey-iconbtn:active:not(:disabled){background:var(--bg-active);transform:scale(var(--press-scale))}
.arey-iconbtn:focus-visible{outline:none;box-shadow:var(--ring-focus)}
.arey-iconbtn:disabled{opacity:.4;cursor:not-allowed}
.arey-iconbtn--sm{--_s:28px;border-radius:var(--radius-md)}
.arey-iconbtn--lg{--_s:44px}
.arey-iconbtn--bordered{border-color:var(--border-default);background:var(--surface-card);color:var(--text-primary);box-shadow:var(--shadow-xs)}
.arey-iconbtn--bordered:hover:not(:disabled){border-color:var(--border-strong);background:var(--bg-subtle)}
.arey-iconbtn--round{border-radius:var(--radius-full)}
.arey-iconbtn[aria-pressed="true"]{background:var(--bg-selected);color:var(--text-accent)}
`);

/** Square, icon-only control. Always ≥36px on web, ≥44px on mobile. */
export function IconButton({ icon, label, size = 'md', variant = 'ghost', round = false, weight = 'regular', className, ...rest }) {
  return (
    <button
      type="button"
      aria-label={label}
      className={cx('arey-iconbtn', size !== 'md' && 'arey-iconbtn--' + size, variant === 'bordered' && 'arey-iconbtn--bordered', round && 'arey-iconbtn--round', className)}
      {...rest}
    >
      <Icon name={icon} weight={weight} size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />
    </button>
  );
}
