import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-progress', `
.arey-progress{position:relative;width:100%;height:6px;border-radius:var(--radius-full);
  background:var(--bg-inset);overflow:hidden}
.arey-progress--thin{height:2px;border-radius:0}
.arey-progress__fill{height:100%;border-radius:inherit;background:var(--accent-solid);
  transition:width var(--duration-slow) var(--ease-out)}
.arey-progress__fill--success{background:var(--success-solid)}
.arey-progress__fill--danger{background:var(--danger-solid)}
.arey-progress__fill--warning{background:var(--warning-solid)}
.arey-progress--indeterminate .arey-progress__fill{width:40%;animation:arey-slide 1.4s var(--ease-in-out) infinite}
@keyframes arey-slide{0%{transform:translateX(-100%)}100%{transform:translateX(250%)}}
`);

/** Determinate or indeterminate progress. `thin` is the 2px page-loading bar. */
export function ProgressBar({ value = 0, tone = 'accent', thin = false, indeterminate = false, className, ...rest }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div
      className={cx('arey-progress', thin && 'arey-progress--thin', indeterminate && 'arey-progress--indeterminate', className)}
      role="progressbar"
      aria-valuenow={indeterminate ? undefined : pct}
      aria-valuemin={0}
      aria-valuemax={100}
      {...rest}
    >
      <div className={cx('arey-progress__fill', tone !== 'accent' && 'arey-progress__fill--' + tone)} style={{ width: indeterminate ? undefined : pct + '%' }} />
    </div>
  );
}
