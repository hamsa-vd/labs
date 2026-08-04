import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-icon', `
.arey-icon{display:inline-flex;align-items:center;justify-content:center;flex:none;line-height:1;color:inherit}
`);

/** Phosphor glyph. Regular is default; Fill marks a selected state only. */
export function Icon({ name, size = 16, weight = 'regular', color, className, style, label, ...rest }) {
  const cls = weight === 'regular' ? 'ph' : 'ph-' + weight;
  return (
    <span
      className={cx('arey-icon', className)}
      style={{ width: size, height: size, fontSize: size, color, ...style }}
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      {...rest}
    >
      <i className={cls + ' ph-' + name} />
    </span>
  );
}
