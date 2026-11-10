import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-card', `
.arey-card{background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-card);
  box-shadow:var(--shadow-md);color:var(--text-body);transition:var(--transition-surface),border-color var(--duration-fast) var(--ease-out)}
.arey-card--flat{box-shadow:none;border-color:var(--border-default)}
.arey-card--inset{background:var(--bg-inset);box-shadow:none;border-color:transparent}
.arey-card--glass{background:var(--surface-glass);border-color:var(--border-glass);
  backdrop-filter:var(--backdrop-glass);-webkit-backdrop-filter:var(--backdrop-glass);box-shadow:var(--shadow-lg)}
.arey-card--interactive{cursor:pointer;text-align:left;display:block;width:100%}
.arey-card--interactive:hover{box-shadow:var(--shadow-lg);transform:translateY(-1px);border-color:var(--border-default)}
.arey-card--interactive:active{transform:scale(.995)}
.arey-card--interactive:focus-visible{outline:none;box-shadow:var(--ring-focus)}
.arey-card__head{display:flex;align-items:flex-start;gap:var(--space-4);padding:var(--pad-card);padding-bottom:0}
.arey-card__title{font:var(--type-title-3);letter-spacing:var(--tracking-heading);color:var(--text-primary)}
.arey-card__desc{font:var(--type-caption);color:var(--text-secondary);margin-top:var(--space-1)}
.arey-card__body{padding:var(--pad-card)}
.arey-card__foot{display:flex;align-items:center;gap:var(--space-3);padding:var(--space-4) var(--pad-card);
  border-top:1px solid var(--border-subtle);background:var(--bg-subtle);
  border-radius:0 0 calc(var(--radius-card) - 1px) calc(var(--radius-card) - 1px)}
`);

/** The standard surface: hairline border + soft shadow, both always. */
export function Card({ variant = 'default', interactive = false, title, description, action, footer, padded = true, as, className, children, ...rest }) {
  const Tag = as || (interactive ? 'button' : 'div');
  return (
    <Tag className={cx('arey-card', variant !== 'default' && 'arey-card--' + variant, interactive && 'arey-card--interactive', className)} {...rest}>
      {(title || action) && (
        <div className="arey-card__head">
          <div style={{ flex: 1, minWidth: 0 }}>
            {title && <div className="arey-card__title">{title}</div>}
            {description && <div className="arey-card__desc">{description}</div>}
          </div>
          {action}
        </div>
      )}
      {children != null && (padded ? <div className="arey-card__body">{children}</div> : children)}
      {footer && <div className="arey-card__foot">{footer}</div>}
    </Tag>
  );
}
