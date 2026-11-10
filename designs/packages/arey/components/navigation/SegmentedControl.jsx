import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { Icon } from '../core/Icon.jsx';

injectSheet('arey-segmented', `
.arey-seg{display:inline-grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:2px;padding:2px;
  background:var(--bg-inset);border-radius:var(--radius-control);width:100%}
.arey-seg__item{display:inline-flex;align-items:center;justify-content:center;gap:var(--space-2);
  height:30px;padding:0 var(--space-3);border:0;background:none;border-radius:var(--radius-md);cursor:pointer;
  font:var(--type-label);color:var(--text-secondary);transition:var(--transition-control)}
.arey-seg__item:hover{color:var(--text-primary)}
.arey-seg__item:active{transform:scale(.98)}
.arey-seg__item:focus-visible{outline:none;box-shadow:var(--ring-focus)}
.arey-seg__item[aria-checked="true"]{background:var(--surface-card);color:var(--text-primary);box-shadow:var(--shadow-xs)}
.arey-seg--lg .arey-seg__item{height:38px}
.arey-seg--inline{width:auto;grid-auto-columns:auto}
`);

/** iOS-flavoured 2–4 option switch. Above four options use Select. */
export function SegmentedControl({ options = [], value, onChange, size = 'md', inline = false, className, ...rest }) {
  return (
    <div className={cx('arey-seg', size === 'lg' && 'arey-seg--lg', inline && 'arey-seg--inline', className)} role="radiogroup" {...rest}>
      {options.map(function (o) {
        const t = typeof o === 'string' ? { value: o, label: o } : o;
        return (
          <button
            key={t.value}
            type="button"
            role="radio"
            className="arey-seg__item"
            aria-checked={value === t.value}
            onClick={function () { if (onChange) onChange(t.value); }}
          >
            {t.icon && <Icon name={t.icon} size={15} weight={value === t.value ? 'fill' : 'regular'} />}
            {t.label}
          </button>
        );
      })}
    </div>
  );
}
