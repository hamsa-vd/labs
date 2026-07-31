import React from 'react';
import { injectSheet, injectControlBase, cx } from '../internal/sheet.jsx';
import { Icon } from '../core/Icon.jsx';

injectControlBase();
injectSheet('arey-select', `
.arey-select-wrap{position:relative;display:flex;align-items:center}
.arey-select{appearance:none;-webkit-appearance:none;padding-right:34px;cursor:pointer}
.arey-select-wrap__caret{position:absolute;right:var(--space-3);color:var(--text-tertiary);pointer-events:none;display:flex}
`);
/** Native select in arey clothing. */
export function Select({ options = [], size = 'md', placeholder, invalid = false, className, ...rest }) {
  return (
    <span className="arey-select-wrap">
      <select
        className={cx('arey-input', 'arey-select', size !== 'md' && 'arey-input--' + size, invalid && 'arey-input--invalid', className)}
        aria-invalid={invalid || undefined}
        {...rest}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(function (o, i) {
          const opt = typeof o === 'string' ? { value: o, label: o } : o;
          return <option key={i} value={opt.value} disabled={opt.disabled}>{opt.label}</option>;
        })}
      </select>
      <span className="arey-select-wrap__caret"><Icon name="caret-up-down" size={14} /></span>
    </span>
  );
}
