import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-table', `
.arey-table-wrap{width:100%;overflow:auto;border-radius:inherit}
.arey-table{width:100%;border-collapse:collapse;border-spacing:0;color:var(--text-body)}
.arey-table__head{font:var(--type-eyebrow);letter-spacing:var(--tracking-eyebrow);text-transform:uppercase;
  color:var(--text-tertiary);font-weight:var(--weight-medium);padding:var(--space-3) var(--space-4);
  border-bottom:1px solid var(--border-subtle);white-space:nowrap;background:var(--bg-subtle)}
.arey-table__cell{padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--border-subtle);
  font:var(--type-body);color:var(--text-body);vertical-align:middle}
.arey-table__cell--mono{font:var(--type-code)}
.arey-table__row:last-child .arey-table__cell{border-bottom:0}
.arey-table__row--interactive{cursor:pointer;transition:background-color var(--duration-fast) var(--ease-out)}
.arey-table__row--interactive:hover{background:var(--bg-hover)}
.arey-table__row--interactive:focus-visible{outline:none;box-shadow:inset var(--ring-focus)}
`);

export function Table({ className, children, ...rest }) {
  return <div className="arey-table-wrap"><table className={cx('arey-table', className)} {...rest}>{children}</table></div>;
}

export function TableHead({ align = 'left', className, children, ...rest }) {
  return <th className={cx('arey-table__head', className)} style={{ textAlign: align }} {...rest}>{children}</th>;
}

export function TableCell({ align = 'left', mono = false, className, children, ...rest }) {
  return <td className={cx('arey-table__cell', mono && 'arey-table__cell--mono', className)} style={{ textAlign: align }} {...rest}>{children}</td>;
}

export function TableRow({ interactive = false, className, children, ...rest }) {
  return <tr className={cx('arey-table__row', interactive && 'arey-table__row--interactive', className)} tabIndex={interactive ? 0 : undefined} {...rest}>{children}</tr>;
}
