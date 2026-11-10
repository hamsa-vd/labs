import React from 'react';
import { injectSheet, cx } from '../internal/sheet.jsx';

injectSheet('arey-kbd', `
.arey-kbd{display:inline-flex;align-items:center;gap:2px;font:var(--weight-medium) var(--text-11)/1 var(--font-mono);font-family:var(--font-mono),"Helvetica Neue",system-ui,sans-serif;color:var(--text-tertiary)}
.arey-kbd kbd{display:inline-grid;place-items:center;min-width:20px;height:20px;padding:0 5px;
  border:1px solid var(--border-default);border-bottom-width:2px;border-radius:var(--radius-sm);
  background:var(--surface-card);color:var(--text-secondary);font:inherit}
`);

const GLYPH = { cmd: '\u2318', meta: '\u2318', alt: '\u2325', option: '\u2325', shift: '\u21E7', ctrl: '\u2303', enter: '\u21B5', esc: 'esc', tab: '\u21E5', up: '\u2191', down: '\u2193', backspace: '\u232B' };

/** Keyboard shortcut. The one place unicode glyphs are correct typography. */
export function Kbd({ keys, className, ...rest }) {
  const list = Array.isArray(keys) ? keys : String(keys).split('+');
  return (
    <span className={cx('arey-kbd', className)} {...rest}>
      {list.map(function (k, i) {
        const t = String(k).trim();
        return <kbd key={i}>{GLYPH[t.toLowerCase()] || t.toUpperCase()}</kbd>;
      })}
    </span>
  );
}
