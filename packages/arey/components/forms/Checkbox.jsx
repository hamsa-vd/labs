import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-checkbox', `
.arey-check{display:inline-flex;align-items:flex-start;gap:var(--space-3);cursor:pointer;
  font:var(--type-body);color:var(--text-body)}
.arey-check input{position:absolute;opacity:0;width:0;height:0}
.arey-check__box{position:relative;flex:none;width:18px;height:18px;margin-top:1px;border-radius:var(--radius-sm);
  border:1px solid var(--border-strong);background:var(--bg-base);box-shadow:var(--shadow-xs);
  transition:var(--transition-control)}
.arey-check:hover .arey-check__box{border-color:var(--accent-solid)}
.arey-check:active .arey-check__box{transform:scale(var(--press-scale))}
.arey-check__box::after{content:"";position:absolute;left:5px;top:2px;width:5px;height:9px;
  border:solid #fff;border-width:0 2px 2px 0;transform:rotate(45deg) scale(.4);opacity:0;
  transition:opacity var(--duration-fast) var(--ease-out),transform var(--duration-fast) var(--ease-spring)}
.arey-check input:checked + .arey-check__box{background:var(--accent-solid);border-color:var(--accent-solid)}
.arey-check input:checked + .arey-check__box::after{opacity:1;transform:rotate(45deg) scale(1)}
.arey-check input:indeterminate + .arey-check__box{background:var(--accent-solid);border-color:var(--accent-solid)}
.arey-check input:indeterminate + .arey-check__box::after{opacity:1;left:3px;top:7px;width:10px;height:0;
  border-width:0 0 2px 0;transform:none}
.arey-check input:focus-visible + .arey-check__box{box-shadow:var(--ring-focus);border-color:var(--accent-solid)}
.arey-check input:disabled ~ *{opacity:.4}
.arey-check__text{display:grid;gap:2px}
.arey-check__desc{font:var(--type-caption);color:var(--text-secondary)}
`);

/** Multi-select control. Label sits to the right, always clickable. */
export function Checkbox({ label, description, indeterminate = false, className, ...rest }) {
  const ref = React.useRef(null);
  React.useEffect(function () { if (ref.current) ref.current.indeterminate = indeterminate; }, [indeterminate]);
  return (
    <label className={cx('arey-check', className)}>
      <input ref={ref} type="checkbox" {...rest} />
      <span className="arey-check__box" />
      {(label || description) && (
        <span className="arey-check__text">
          {label}
          {description && <span className="arey-check__desc">{description}</span>}
        </span>
      )}
    </label>
  );
}
