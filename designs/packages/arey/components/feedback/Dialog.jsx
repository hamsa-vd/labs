import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { IconButton } from '../core/IconButton.jsx';

injectSheet('arey-dialog', `
.arey-dialog__scrim{position:fixed;inset:0;z-index:100;display:grid;place-items:center;padding:var(--space-6);
  background:var(--surface-scrim);animation:arey-fade var(--duration-normal) var(--ease-out)}
.arey-dialog{position:relative;width:100%;max-width:440px;max-height:88vh;overflow:auto;
  background:var(--surface-raised);border:1px solid var(--border-default);border-radius:var(--radius-sheet);
  box-shadow:var(--shadow-xl);animation:arey-rise var(--duration-normal) var(--ease-out)}
.arey-dialog--lg{max-width:640px}
.arey-dialog--sheet{align-self:end;max-width:none;border-radius:var(--radius-sheet) var(--radius-sheet) 0 0}
.arey-dialog__head{display:flex;align-items:flex-start;gap:var(--space-4);padding:var(--space-6) var(--space-6) 0}
.arey-dialog__title{font:var(--type-title-2);letter-spacing:var(--tracking-heading);color:var(--text-primary)}
.arey-dialog__desc{font:var(--type-body);color:var(--text-secondary);margin-top:var(--space-2)}
.arey-dialog__body{padding:var(--space-6)}
.arey-dialog__foot{display:flex;justify-content:flex-end;gap:var(--space-3);
  padding:var(--space-4) var(--space-6);border-top:1px solid var(--border-subtle);background:var(--bg-subtle)}
@keyframes arey-fade{from{opacity:0}to{opacity:1}}
@keyframes arey-rise{from{opacity:0;transform:translateY(8px) scale(.98)}to{opacity:1;transform:none}}
`);

/** Modal. Scrim has no blur so the sheet's own material stays legible. */
export function Dialog({ open = true, title, description, footer, size = 'md', onClose, className, children }) {
  React.useEffect(function () {
    if (!open || !onClose) return;
    function onKey(e) { if (e.key === 'Escape') onClose(); }
    document.addEventListener('keydown', onKey);
    return function () { document.removeEventListener('keydown', onKey); };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="arey-dialog__scrim" onClick={function (e) { if (e.target === e.currentTarget && onClose) onClose(); }}>
      <div className={cx('arey-dialog', size !== 'md' && 'arey-dialog--' + size, className)} role="dialog" aria-modal="true" aria-label={typeof title === 'string' ? title : undefined}>
        {(title || onClose) && (
          <div className="arey-dialog__head">
            <div style={{ flex: 1, minWidth: 0 }}>
              {title && <div className="arey-dialog__title">{title}</div>}
              {description && <div className="arey-dialog__desc">{description}</div>}
            </div>
            {onClose && <IconButton icon="x" label="Close" size="sm" onClick={onClose} />}
          </div>
        )}
        {children != null && <div className="arey-dialog__body">{children}</div>}
        {footer && <div className="arey-dialog__foot">{footer}</div>}
      </div>
    </div>
  );
}
