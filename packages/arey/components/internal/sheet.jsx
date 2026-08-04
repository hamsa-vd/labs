// Injects a component's CSS rules once per document. Lets components use real
// :hover / :active / :focus-visible / :disabled states instead of JS state juggling,
// while every value still comes from the design-system custom properties.
const seen = new Set();
export function injectSheet(id, css) {
  if (typeof document === 'undefined' || seen.has(id)) return;
  seen.add(id);
  const el = document.createElement('style');
  el.setAttribute('data-arey', id);
  el.textContent = css;
  document.head.appendChild(el);
}
export function cx() {
  return Array.prototype.filter.call(arguments, Boolean).join(' ');
}

// Shared text-control base. Injected once so Input and Select can't clobber each
// other's modifiers by re-declaring .arey-input in a later stylesheet.
export function injectControlBase() {
  injectSheet('arey-control-base', `
.arey-input{width:100%;height:var(--control-h-md);padding:0 var(--space-3);
  background:var(--bg-base);color:var(--text-primary);
  border:1px solid var(--border-default);border-radius:var(--radius-control);
  font:var(--type-body);letter-spacing:var(--tracking-body);
  transition:var(--transition-control);box-shadow:var(--shadow-xs)}
.arey-input::placeholder{color:var(--text-tertiary)}
.arey-input:hover:not(:disabled){border-color:var(--border-strong)}
.arey-input:focus{outline:none;border-color:var(--border-focus);box-shadow:var(--ring-focus)}
.arey-input:disabled{opacity:.4;cursor:not-allowed}
.arey-input--sm{height:var(--control-h-sm);font:var(--type-caption)}
.arey-input--lg{height:var(--control-h-lg);padding:0 var(--space-4);font:var(--type-body-lg)}
.arey-input--mono{font-family:var(--font-mono);letter-spacing:0}
.arey-input--invalid{border-color:var(--danger-solid)}
.arey-input--invalid:focus{box-shadow:var(--ring-danger)}
.arey-input--has-icon{padding-left:34px}
.arey-input--has-icon.arey-input--lg{padding-left:40px}
`);
}
