import React from 'react';
import { injectSheet, injectControlBase, cx } from '../internal/sheet.jsx';
import { Icon } from '../core/Icon.jsx';

injectControlBase();
injectSheet('arey-input', `
.arey-input-wrap{position:relative;display:flex;align-items:center}
.arey-input-wrap__icon{position:absolute;left:var(--space-3);color:var(--text-tertiary);pointer-events:none;display:flex}
.arey-input-wrap__suffix{position:absolute;right:var(--space-3);display:flex;align-items:center;gap:var(--space-2);color:var(--text-tertiary)}
`);
/** Single-line text control. */
export function Input({ size = 'md', icon, suffix, mono = false, invalid = false, className, style, ...rest }) {
  const input = (
    <input
      className={cx('arey-input', size !== 'md' && 'arey-input--' + size, icon && 'arey-input--has-icon', mono && 'arey-input--mono', invalid && 'arey-input--invalid', className)}
      aria-invalid={invalid || undefined}
      style={suffix ? { paddingRight: 64, ...style } : style}
      {...rest}
    />
  );
  if (!icon && !suffix) return input;
  return (
    <span className="arey-input-wrap">
      {icon && <span className="arey-input-wrap__icon"><Icon name={icon} size={16} /></span>}
      {input}
      {suffix && <span className="arey-input-wrap__suffix">{suffix}</span>}
    </span>
  );
}
