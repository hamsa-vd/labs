import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-field', `
.arey-field{display:grid;gap:var(--space-2)}
.arey-field__label{display:flex;align-items:center;gap:var(--space-2);font:var(--type-label);color:var(--text-primary)}
.arey-field__opt{font:var(--type-caption);color:var(--text-tertiary);font-weight:var(--weight-regular)}
.arey-field__hint{font:var(--type-caption);color:var(--text-secondary)}
.arey-field__error{display:flex;align-items:center;gap:var(--space-2);font:var(--type-caption);color:var(--danger-text)}
.arey-field--row{grid-template-columns:200px 1fr;gap:var(--space-6);align-items:start}
`);

/** Label + helper + error wrapper shared by every form control. */
export function Field({ label, hint, error, optional = false, htmlFor, layout = 'stack', className, children, ...rest }) {
  return (
    <div className={cx('arey-field', layout === 'row' && 'arey-field--row', className)} {...rest}>
      {label && (
        <label className="arey-field__label" htmlFor={htmlFor}>
          {label}
          {optional && <span className="arey-field__opt">Optional</span>}
        </label>
      )}
      <div style={{ display: 'grid', gap: 'var(--space-2)' }}>
        {children}
        {error ? <div className="arey-field__error">{error}</div> : hint ? <div className="arey-field__hint">{hint}</div> : null}
      </div>
    </div>
  );
}
