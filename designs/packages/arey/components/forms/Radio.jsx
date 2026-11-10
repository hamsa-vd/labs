import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-radio', `
.arey-radio{display:inline-flex;align-items:flex-start;gap:var(--space-3);cursor:pointer;font:var(--type-body);color:var(--text-body)}
.arey-radio input{position:absolute;opacity:0;width:0;height:0}
.arey-radio__dot{position:relative;flex:none;width:18px;height:18px;margin-top:1px;border-radius:50%;
  border:1px solid var(--border-strong);background:var(--bg-base);box-shadow:var(--shadow-xs);transition:var(--transition-control)}
.arey-radio:hover .arey-radio__dot{border-color:var(--accent-solid)}
.arey-radio:active .arey-radio__dot{transform:scale(var(--press-scale))}
.arey-radio__dot::after{content:"";position:absolute;inset:0;margin:auto;width:7px;height:7px;border-radius:50%;
  background:#fff;transform:scale(.3);opacity:0;transition:opacity var(--duration-fast) var(--ease-out),transform var(--duration-fast) var(--ease-spring)}
.arey-radio input:checked + .arey-radio__dot{background:var(--accent-solid);border-color:var(--accent-solid)}
.arey-radio input:checked + .arey-radio__dot::after{opacity:1;transform:scale(1)}
.arey-radio input:focus-visible + .arey-radio__dot{box-shadow:var(--ring-focus);border-color:var(--accent-solid)}
.arey-radio input:disabled ~ *{opacity:.4}
.arey-radio__text{display:grid;gap:2px}
.arey-radio__desc{font:var(--type-caption);color:var(--text-secondary)}
.arey-radio-group{display:grid;gap:var(--space-4)}
.arey-radio-group--row{grid-auto-flow:column;justify-content:start;gap:var(--space-6)}
`);

/** Single choice among 2–4 visible options. */
export function Radio({ label, description, className, ...rest }) {
  return (
    <label className={cx('arey-radio', className)}>
      <input type="radio" {...rest} />
      <span className="arey-radio__dot" />
      {(label || description) && (
        <span className="arey-radio__text">
          {label}
          {description && <span className="arey-radio__desc">{description}</span>}
        </span>
      )}
    </label>
  );
}

/** Layout wrapper that shares a name across its radios. */
export function RadioGroup({ name, value, onChange, options = [], direction = 'column', className }) {
  return (
    <div className={cx('arey-radio-group', direction === 'row' && 'arey-radio-group--row', className)} role="radiogroup">
      {options.map(function (o, i) {
        return (
          <Radio
            key={i}
            name={name}
            value={o.value}
            label={o.label}
            description={o.description}
            checked={value === o.value}
            onChange={function () { if (onChange) onChange(o.value); }}
          />
        );
      })}
    </div>
  );
}
