import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';
import { Icon } from '../core/Icon.jsx';

injectSheet('arey-listrow', `
.arey-row{display:flex;align-items:center;gap:var(--space-3);width:100%;
  padding:var(--space-3) var(--space-4);border:0;background:transparent;text-align:left;
  color:var(--text-body);font:var(--type-body);transition:var(--transition-control)}
.arey-row--interactive{cursor:pointer}
.arey-row--interactive:hover{background:var(--bg-hover)}
.arey-row--interactive:active{background:var(--bg-active)}
.arey-row--interactive:focus-visible{outline:none;box-shadow:var(--ring-focus);border-radius:var(--radius-md)}
.arey-row__lead{color:var(--text-secondary);display:flex;flex:none}
.arey-row__main{flex:1;min-width:0;display:grid;gap:2px}
.arey-row__title{font:var(--type-label);color:var(--text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.arey-row__sub{font:var(--type-caption);color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.arey-row__value{font:var(--type-body);color:var(--text-secondary);flex:none}
.arey-row__value--mono{font-family:var(--font-mono);font-size:var(--text-13)}
.arey-row__chev{color:var(--text-tertiary);display:flex;flex:none}
.arey-list{display:grid}
.arey-list--divided > * + *{border-top:1px solid var(--border-subtle)}
.arey-list--inset{background:var(--surface-card);border:1px solid var(--border-subtle);
  border-radius:var(--radius-card);overflow:hidden;box-shadow:var(--shadow-sm)}
`);

/** The list primitive behind settings rows, mobile grouped lists, and result lists. */
export function ListRow({ icon, leading, title, subtitle, value, mono = false, trailing, chevron = false, onClick, as, className, ...rest }) {
  const interactive = !!onClick;
  const Tag = as || (interactive ? 'button' : 'div');
  return (
    <Tag className={cx('arey-row', interactive && 'arey-row--interactive', className)} onClick={onClick} type={Tag === 'button' ? 'button' : undefined} {...rest}>
      {leading ? <span className="arey-row__lead">{leading}</span> : icon ? <span className="arey-row__lead"><Icon name={icon} size={17} /></span> : null}
      <span className="arey-row__main">
        <span className="arey-row__title">{title}</span>
        {subtitle && <span className="arey-row__sub">{subtitle}</span>}
      </span>
      {value != null && <span className={cx('arey-row__value', mono && 'arey-row__value--mono')}>{value}</span>}
      {trailing}
      {chevron && <span className="arey-row__chev"><Icon name="caret-right" size={14} /></span>}
    </Tag>
  );
}

/** Container for ListRows. `inset` gives the iOS grouped-card look. */
export function List({ divided = true, inset = false, className, children, ...rest }) {
  return <div className={cx('arey-list', divided && 'arey-list--divided', inset && 'arey-list--inset', className)} {...rest}>{children}</div>;
}
