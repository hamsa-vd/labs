import React from 'react';
import { injectFont, injectSheet, cx } from '../internal/sheet.jsx';

const CDN = 'https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src';
injectFont(CDN + '/regular/style.css', 'ph-regular');
injectFont(CDN + '/bold/style.css', 'ph-bold');
injectFont(CDN + '/fill/style.css', 'ph-fill');
injectFont(CDN + '/duotone/style.css', 'ph-duotone');

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
