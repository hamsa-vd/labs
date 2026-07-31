import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-tooltip', `
.arey-tooltip{position:relative;display:inline-flex}
.arey-tooltip__pop{position:absolute;z-index:60;pointer-events:none;
  padding:6px var(--space-3);border-radius:var(--radius-md);
  background:var(--surface-overlay);border:1px solid var(--border-glass);
  backdrop-filter:var(--backdrop-glass);-webkit-backdrop-filter:var(--backdrop-glass);
  box-shadow:var(--shadow-lg);color:var(--text-primary);
  font:var(--type-caption);white-space:nowrap;
  opacity:0;transform:translateY(2px) scale(.97);
  transition:opacity var(--duration-fast) var(--ease-out),transform var(--duration-fast) var(--ease-out)}
.arey-tooltip__pop[data-open="true"]{opacity:1;transform:translateY(0) scale(1)}
.arey-tooltip__pop[data-side="top"]{bottom:calc(100% + 8px);left:50%;margin-left:-50%;
  display:flex;justify-content:center;width:100%}
.arey-tooltip__pop--mono{font-family:var(--font-mono);font-size:var(--text-11)}
`);

/** Hover / focus hint. Glass surface, 8px offset, never contains an action. */
export function Tooltip({ label, mono = false, children, className, ...rest }) {
  const [open, setOpen] = React.useState(false);
  return (
    <span
      className={cx('arey-tooltip', className)}
      onMouseEnter={function () { setOpen(true); }}
      onMouseLeave={function () { setOpen(false); }}
      onFocus={function () { setOpen(true); }}
      onBlur={function () { setOpen(false); }}
      {...rest}
    >
      {children}
      <span className={cx('arey-tooltip__pop', mono && 'arey-tooltip__pop--mono')} data-side="top" data-open={open} role="tooltip">
        <span style={{ background: 'inherit' }}>{label}</span>
      </span>
    </span>
  );
}
