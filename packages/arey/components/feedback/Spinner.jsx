import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-spinner', `
.arey-spinner{display:inline-block;flex:none;border-radius:50%;border-style:solid;
  border-color:currentColor;border-right-color:transparent;opacity:.7;
  animation:arey-spin .7s linear infinite}
@keyframes arey-spin{to{transform:rotate(360deg)}}
@media (prefers-reduced-motion:reduce){.arey-spinner{animation-duration:1.6s}}
`);

/** Indeterminate activity. Replaces a control's label rather than sitting beside it. */
export function Spinner({ size = 16, thickness, className, style, ...rest }) {
  return (
    <span
      className={cx('arey-spinner', className)}
      role="status"
      aria-label="Loading"
      style={{ width: size, height: size, borderWidth: thickness || Math.max(1.5, Math.round(size / 9)), ...style }}
      {...rest}
    />
  );
}
