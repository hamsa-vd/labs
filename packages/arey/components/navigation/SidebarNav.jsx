import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { Icon } from '../core/Icon.jsx';

injectSheet('arey-sidebarnav', `
.arey-nav{display:grid;gap:var(--space-6);padding:var(--space-4);align-content:start}
.arey-nav__group{display:grid;gap:2px}
.arey-nav__label{font:var(--type-eyebrow);letter-spacing:var(--tracking-eyebrow);text-transform:uppercase;
  color:var(--text-tertiary);padding:0 var(--space-3) var(--space-2)}
.arey-nav__item{display:flex;align-items:center;gap:var(--space-3);height:34px;padding:0 var(--space-3);
  border:0;background:none;border-radius:var(--radius-md);cursor:pointer;width:100%;text-align:left;
  font:var(--type-label);color:var(--text-secondary);transition:var(--transition-control);text-decoration:none}
.arey-nav__item:hover{background:var(--bg-hover);color:var(--text-primary)}
.arey-nav__item:active{background:var(--bg-active)}
.arey-nav__item:focus-visible{outline:none;box-shadow:var(--ring-focus)}
.arey-nav__item[aria-current="page"]{background:var(--bg-selected);color:var(--text-accent)}
.arey-nav__text{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.arey-nav__count{flex:none;font:var(--type-caption);font-family:var(--font-mono);color:var(--text-tertiary)}
.arey-nav__item[aria-current="page"] .arey-nav__count{color:var(--text-accent)}
`);

/** Product sidebar navigation. Active row is an accent wash — never a left border stripe. */
export function SidebarNav({ groups = [], value, onChange, className, ...rest }) {
  return (
    <nav className={cx('arey-nav', className)} {...rest}>
      {groups.map(function (g, gi) {
        return (
          <div className="arey-nav__group" key={gi}>
            {g.label && <div className="arey-nav__label">{g.label}</div>}
            {g.items.map(function (it) {
              const active = value === it.value;
              return (
                <a
                  key={it.value}
                  href={it.href || '#'}
                  className="arey-nav__item"
                  aria-current={active ? 'page' : undefined}
                  onClick={function (e) { if (onChange) { e.preventDefault(); onChange(it.value); } }}
                >
                  {it.icon && <Icon name={it.icon} size={16} weight={active ? 'fill' : 'regular'} />}
                  <span className="arey-nav__text">{it.label}</span>
                  {it.count != null && <span className="arey-nav__count">{it.count}</span>}
                </a>
              );
            })}
          </div>
        );
      })}
    </nav>
  );
}
