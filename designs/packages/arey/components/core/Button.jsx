import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { Icon } from './Icon.jsx';
import { Spinner } from '../feedback/Spinner.jsx';

injectSheet('arey-button', `
.arey-btn{--_h:var(--control-h-md);display:inline-flex;align-items:center;justify-content:center;gap:var(--space-2);
  height:var(--_h);padding:0 var(--pad-control-x);border-radius:var(--radius-control);border:1px solid transparent;
  font:var(--type-label);letter-spacing:var(--tracking-body);white-space:nowrap;cursor:pointer;
  background:transparent;color:var(--text-body);transition:var(--transition-control);
  -webkit-tap-highlight-color:transparent;text-decoration:none}
.arey-btn:active:not(:disabled){transform:scale(var(--press-scale))}
.arey-btn:disabled,.arey-btn[aria-disabled="true"]{opacity:.4;cursor:not-allowed;transform:none}
.arey-btn:focus-visible{outline:none;box-shadow:var(--ring-focus)}
.arey-btn--sm{--_h:var(--control-h-sm);padding:0 var(--space-3);font:var(--type-caption);font-weight:var(--weight-medium)}
.arey-btn--lg{--_h:var(--control-h-lg);padding:0 var(--space-5);font:var(--type-body);font-weight:var(--weight-medium)}
.arey-btn--block{width:100%}

.arey-btn--primary{background:var(--accent-solid);color:var(--accent-text-on);box-shadow:var(--shadow-xs)}
.arey-btn--primary:hover:not(:disabled){background:var(--accent-solid-hover)}
.arey-btn--primary:active:not(:disabled){background:var(--accent-solid-active)}

.arey-btn--secondary{background:var(--surface-card);color:var(--text-primary);border-color:var(--border-default);box-shadow:var(--shadow-xs)}
.arey-btn--secondary:hover:not(:disabled){border-color:var(--border-strong);background:var(--bg-subtle)}
.arey-btn--secondary:active:not(:disabled){background:var(--bg-inset)}

.arey-btn--ghost{background:transparent;color:var(--text-body)}
.arey-btn--ghost:hover:not(:disabled){background:var(--bg-hover);color:var(--text-primary)}
.arey-btn--ghost:active:not(:disabled){background:var(--bg-active)}

.arey-btn--inverse{background:var(--bg-inverse);color:var(--text-inverse)}
.arey-btn--inverse:hover:not(:disabled){opacity:.86}

.arey-btn--danger{background:var(--danger-solid);color:#fff}
.arey-btn--danger:hover:not(:disabled){filter:brightness(1.08)}
.arey-btn--danger:focus-visible{box-shadow:var(--ring-danger)}

.arey-btn--link{height:auto;padding:0;color:var(--text-link);border-radius:var(--radius-xs)}
.arey-btn--link:hover:not(:disabled){opacity:.7}
.arey-btn--link:active:not(:disabled){transform:none;opacity:.55}
`);

/** The system's primary action control. Label is sentence case, verb first. */
export function Button({
  variant = 'secondary', size = 'md', iconLeft, iconRight, loading = false,
  block = false, disabled, as = 'button', className, children, ...rest
}) {
  const Tag = as;
  return (
    <Tag
      className={cx('arey-btn', 'arey-btn--' + variant, size !== 'md' && 'arey-btn--' + size, block && 'arey-btn--block', className)}
      disabled={Tag === 'button' ? disabled || loading : undefined}
      aria-disabled={Tag !== 'button' && (disabled || loading) ? true : undefined}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner size={size === 'sm' ? 12 : 14} /> : iconLeft ? <Icon name={iconLeft} size={size === 'lg' ? 18 : 16} /> : null}
      {children}
      {iconRight && !loading ? <Icon name={iconRight} size={size === 'lg' ? 18 : 16} /> : null}
    </Tag>
  );
}
