import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { Icon } from '../core/Icon.jsx';

injectSheet('arey-tabs', `
.arey-tabs{display:flex;align-items:center;gap:var(--space-6);
  border-bottom:1px solid var(--border-subtle)}
.arey-tab{position:relative;display:inline-flex;align-items:center;gap:var(--space-2);
  padding:0 0 var(--space-3);border:0;background:none;cursor:pointer;
  font:var(--type-label);color:var(--text-secondary);transition:color var(--duration-fast) var(--ease-out)}
.arey-tab:hover{color:var(--text-primary)}
.arey-tab:focus-visible{outline:none;box-shadow:var(--ring-focus);border-radius:var(--radius-xs)}
.arey-tab::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:2px;border-radius:2px 2px 0 0;
  background:var(--text-primary);opacity:0;transform:scaleX(.6);
  transition:opacity var(--duration-fast) var(--ease-out),transform var(--duration-normal) var(--ease-out)}
.arey-tab[aria-selected="true"]{color:var(--text-primary)}
.arey-tab[aria-selected="true"]::after{opacity:1;transform:none}
.arey-tab__count{font:var(--type-caption);font-family:var(--font-mono);color:var(--text-tertiary)}
.arey-tabs--pill{border-bottom:0;gap:var(--space-1);padding:3px;background:var(--bg-inset);
  border-radius:var(--radius-control);display:inline-flex}
.arey-tabs--pill .arey-tab{padding:0 var(--space-4);height:30px;border-radius:var(--radius-md)}
.arey-tabs--pill .arey-tab::after{display:none}
.arey-tabs--pill .arey-tab[aria-selected="true"]{background:var(--surface-card);box-shadow:var(--shadow-xs)}
`);

/** Section switcher. Underline by default; pill inside cards and toolbars. */
export function Tabs({ items = [], value, onChange, variant = 'underline', className, ...rest }) {
  return (
    <div className={cx('arey-tabs', variant === 'pill' && 'arey-tabs--pill', className)} role="tablist" {...rest}>
      {items.map(function (it) {
        const t = typeof it === 'string' ? { value: it, label: it } : it;
        return (
          <button
            key={t.value}
            type="button"
            role="tab"
            className="arey-tab"
            aria-selected={value === t.value}
            onClick={function () { if (onChange) onChange(t.value); }}
          >
            {t.icon && <Icon name={t.icon} size={16} />}
            {t.label}
            {t.count != null && <span className="arey-tab__count">{t.count}</span>}
          </button>
        );
      })}
    </div>
  );
}
