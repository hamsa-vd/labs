import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { Icon } from '../core/Icon.jsx';

injectSheet('arey-breadcrumbs', `
.arey-crumbs{display:flex;align-items:center;gap:var(--space-2);font:var(--type-label);color:var(--text-secondary);min-width:0}
.arey-crumbs a,.arey-crumbs__item{color:var(--text-secondary);text-decoration:none;white-space:nowrap;
  transition:color var(--duration-fast) var(--ease-out)}
.arey-crumbs a:hover{color:var(--text-primary);opacity:1}
.arey-crumbs__sep{color:var(--border-strong);display:flex}
.arey-crumbs__item--current{color:var(--text-primary)}
`);

/** Ancestry trail. Phosphor caret separator — never a slash character. */
export function Breadcrumbs({ items = [], className, ...rest }) {
  return (
    <nav className={cx('arey-crumbs', className)} aria-label="Breadcrumb" {...rest}>
      {items.map(function (it, i) {
        const last = i === items.length - 1;
        return (
          <React.Fragment key={i}>
            {i > 0 && <span className="arey-crumbs__sep"><Icon name="caret-right" size={12} /></span>}
            {it.href && !last
              ? <a href={it.href}>{it.label}</a>
              : <span className={cx('arey-crumbs__item', last && 'arey-crumbs__item--current')} aria-current={last ? 'page' : undefined}>{it.label}</span>}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
