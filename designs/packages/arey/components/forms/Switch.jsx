import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-switch', `
.arey-switch{display:inline-flex;align-items:center;gap:var(--space-3);cursor:pointer;font:var(--type-body);color:var(--text-body)}
.arey-switch input{position:absolute;opacity:0;width:0;height:0}
.arey-switch__track{position:relative;flex:none;width:42px;height:26px;border-radius:var(--radius-full);
  background:var(--switch-track-off);transition:background-color var(--duration-normal) var(--ease-out),box-shadow var(--duration-fast) var(--ease-out)}
.arey-switch__track::after{content:"";position:absolute;top:2px;left:2px;width:22px;height:22px;border-radius:50%;
  background:var(--switch-knob);box-shadow:0 1px 3px rgba(0,0,0,.25);
  transition:transform var(--duration-normal) var(--ease-spring)}
.arey-switch input:checked + .arey-switch__track{background:var(--success-solid)}
.arey-switch--accent input:checked + .arey-switch__track{background:var(--accent-solid)}
.arey-switch input:checked + .arey-switch__track::after{transform:translateX(16px)}
.arey-switch:active .arey-switch__track::after{width:24px}
.arey-switch input:focus-visible + .arey-switch__track{box-shadow:var(--ring-focus)}
.arey-switch input:disabled ~ *{opacity:.4}
.arey-switch--sm .arey-switch__track{width:34px;height:20px}
.arey-switch--sm .arey-switch__track::after{width:16px;height:16px}
.arey-switch--sm input:checked + .arey-switch__track::after{transform:translateX(14px)}
.arey-switch__text{display:grid;gap:2px}
.arey-switch__desc{font:var(--type-caption);color:var(--text-secondary)}
`);

/** Immediate on/off. Never needs a Save button. */
export function Switch({ label, description, tone = 'success', size = 'md', className, ...rest }) {
  return (
    <label className={cx('arey-switch', tone === 'accent' && 'arey-switch--accent', size === 'sm' && 'arey-switch--sm', className)}>
      <input type="checkbox" role="switch" {...rest} />
      <span className="arey-switch__track" />
      {(label || description) && (
        <span className="arey-switch__text">
          {label}
          {description && <span className="arey-switch__desc">{description}</span>}
        </span>
      )}
    </label>
  );
}
