import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { Icon } from './Icon.jsx';

injectSheet('arey-tag', `
.arey-tag{display:inline-flex;align-items:center;gap:var(--space-2);height:28px;padding:0 var(--space-3);
  border-radius:var(--radius-full);border:1px solid var(--border-default);background:var(--surface-card);
  color:var(--text-body);font:var(--type-label);transition:var(--transition-control)}
.arey-tag--selectable{cursor:pointer}
.arey-tag--selectable:hover{background:var(--bg-hover);border-color:var(--border-strong)}
.arey-tag--selectable:active{transform:scale(var(--press-scale))}
.arey-tag--selectable:focus-visible{outline:none;box-shadow:var(--ring-focus)}
.arey-tag[aria-pressed="true"]{background:var(--bg-selected);border-color:var(--accent-border);color:var(--text-accent)}
.arey-tag__x{display:inline-flex;margin-right:calc(var(--space-1) * -1);padding:2px;border:0;background:none;
  color:var(--text-tertiary);cursor:pointer;border-radius:var(--radius-full);transition:var(--transition-control)}
.arey-tag__x:hover{background:var(--bg-active);color:var(--text-primary)}
`);

/** Filter chip / removable token. Selectable renders a button. */
export function Tag({ icon, selected, onRemove, onClick, className, children, ...rest }) {
  const selectable = !!onClick;
  const Tag_ = selectable ? 'button' : 'span';
  return (
    <Tag_
      className={cx('arey-tag', selectable && 'arey-tag--selectable', className)}
      aria-pressed={selectable ? !!selected : undefined}
      onClick={onClick}
      {...rest}
    >
      {icon && <Icon name={icon} size={14} />}
      {children}
      {onRemove && (
        <span className="arey-tag__x" role="button" tabIndex={0} aria-label="Remove" onClick={function (e) { e.stopPropagation(); onRemove(e); }}>
          <Icon name="x" size={12} weight="bold" />
        </span>
      )}
    </Tag_>
  );
}
