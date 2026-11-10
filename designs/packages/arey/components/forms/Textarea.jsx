import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-textarea', `
.arey-textarea{width:100%;min-height:96px;padding:var(--space-3);resize:vertical;
  background:var(--bg-base);color:var(--text-primary);
  border:1px solid var(--border-default);border-radius:var(--radius-control);
  font:var(--type-body);letter-spacing:var(--tracking-body);
  transition:var(--transition-control);box-shadow:var(--shadow-xs)}
.arey-textarea::placeholder{color:var(--text-tertiary)}
.arey-textarea:hover:not(:disabled){border-color:var(--border-strong)}
.arey-textarea:focus{outline:none;border-color:var(--border-focus);box-shadow:var(--ring-focus)}
.arey-textarea:disabled{opacity:.4;cursor:not-allowed}
.arey-textarea--mono{font-family:var(--font-mono);letter-spacing:0;line-height:var(--leading-normal)}
.arey-textarea--invalid{border-color:var(--danger-solid)}
`);

/** Multi-line text. Mono variant for env vars and config. */
export function Textarea({ mono = false, invalid = false, rows = 4, className, ...rest }) {
  return (
    <textarea
      rows={rows}
      className={cx('arey-textarea', mono && 'arey-textarea--mono', invalid && 'arey-textarea--invalid', className)}
      aria-invalid={invalid || undefined}
      {...rest}
    />
  );
}
