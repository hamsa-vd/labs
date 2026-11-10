import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { Icon } from '../core/Icon.jsx';

injectSheet('arey-empty', `
.arey-empty{display:grid;justify-items:center;text-align:center;gap:var(--space-3);
  padding:var(--space-16) var(--space-8);color:var(--text-secondary)}
.arey-empty__glyph{display:grid;place-items:center;width:56px;height:56px;border-radius:var(--radius-card);
  background:var(--bg-inset);color:var(--text-tertiary);margin-bottom:var(--space-2)}
.arey-empty__title{font:var(--type-title-3);letter-spacing:var(--tracking-heading);color:var(--text-primary)}
.arey-empty__desc{font:var(--type-body);color:var(--text-secondary);max-width:44ch}
.arey-empty--compact{padding:var(--space-10) var(--space-6)}
`);

/** One line of what's missing, one action. Centred — the only place arey centres body copy. */
export function EmptyState({ icon = 'folder-open', title, description, action, compact = false, className, ...rest }) {
  return (
    <div className={cx('arey-empty', compact && 'arey-empty--compact', className)} {...rest}>
      <div className="arey-empty__glyph"><Icon name={icon} size={24} /></div>
      <div className="arey-empty__title">{title}</div>
      {description && <div className="arey-empty__desc">{description}</div>}
      {action && <div style={{ marginTop: 'var(--space-3)' }}>{action}</div>}
    </div>
  );
}
