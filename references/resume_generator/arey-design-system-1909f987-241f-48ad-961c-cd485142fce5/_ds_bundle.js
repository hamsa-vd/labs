/* @ds-bundle: {"format":4,"namespace":"AreyDesignSystem_1909f9","components":[{"name":"Avatar","sourcePath":"components/core/Avatar.jsx"},{"name":"AvatarStack","sourcePath":"components/core/Avatar.jsx"},{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"Icon","sourcePath":"components/core/Icon.jsx"},{"name":"IconButton","sourcePath":"components/core/IconButton.jsx"},{"name":"Kbd","sourcePath":"components/core/Kbd.jsx"},{"name":"Tag","sourcePath":"components/core/Tag.jsx"},{"name":"Dialog","sourcePath":"components/feedback/Dialog.jsx"},{"name":"EmptyState","sourcePath":"components/feedback/EmptyState.jsx"},{"name":"ProgressBar","sourcePath":"components/feedback/ProgressBar.jsx"},{"name":"Spinner","sourcePath":"components/feedback/Spinner.jsx"},{"name":"Toast","sourcePath":"components/feedback/Toast.jsx"},{"name":"ToastRegion","sourcePath":"components/feedback/Toast.jsx"},{"name":"Tooltip","sourcePath":"components/feedback/Tooltip.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"Field","sourcePath":"components/forms/Field.jsx"},{"name":"Input","sourcePath":"components/forms/Input.jsx"},{"name":"Radio","sourcePath":"components/forms/Radio.jsx"},{"name":"RadioGroup","sourcePath":"components/forms/Radio.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Switch","sourcePath":"components/forms/Switch.jsx"},{"name":"Textarea","sourcePath":"components/forms/Textarea.jsx"},{"name":"Breadcrumbs","sourcePath":"components/navigation/Breadcrumbs.jsx"},{"name":"ListRow","sourcePath":"components/navigation/ListRow.jsx"},{"name":"List","sourcePath":"components/navigation/ListRow.jsx"},{"name":"SegmentedControl","sourcePath":"components/navigation/SegmentedControl.jsx"},{"name":"SidebarNav","sourcePath":"components/navigation/SidebarNav.jsx"},{"name":"Tabs","sourcePath":"components/navigation/Tabs.jsx"}],"sourceHashes":{"components/core/Avatar.jsx":"4e55def2d211","components/core/Badge.jsx":"0a74bdb8b6f6","components/core/Button.jsx":"ad07f5a197f0","components/core/Card.jsx":"a8427aeef3d4","components/core/Icon.jsx":"d241d5e02791","components/core/IconButton.jsx":"a2b6ad8b353d","components/core/Kbd.jsx":"1d0d522cd826","components/core/Tag.jsx":"6e739817e2ac","components/feedback/Dialog.jsx":"fd12cb1a0a7a","components/feedback/EmptyState.jsx":"8658c0b17c42","components/feedback/ProgressBar.jsx":"6810c2716e5f","components/feedback/Spinner.jsx":"ec3922f5190f","components/feedback/Toast.jsx":"086e75591860","components/feedback/Tooltip.jsx":"5d124d58368b","components/forms/Checkbox.jsx":"b9f7d81609cf","components/forms/Field.jsx":"9faa8369f08d","components/forms/Input.jsx":"32f8e9cdba9b","components/forms/Radio.jsx":"cebc4d3ed518","components/forms/Select.jsx":"06fd39dec562","components/forms/Switch.jsx":"c4ea80892482","components/forms/Textarea.jsx":"830d34bd9418","components/internal/sheet.jsx":"cc1794feaf09","components/navigation/Breadcrumbs.jsx":"16385a0f37d8","components/navigation/ListRow.jsx":"dd63da0a9bda","components/navigation/SegmentedControl.jsx":"c7c0b5bb4bf5","components/navigation/SidebarNav.jsx":"bd3b57f90d2f","components/navigation/Tabs.jsx":"c2218e17f08b","ui_kits/console/App.jsx":"12158086ceed","ui_kits/console/Deployments.jsx":"3e695a395ea3","ui_kits/console/Overview.jsx":"d22ed918330d","ui_kits/console/Settings.jsx":"4f78411e097e","ui_kits/console/Shell.jsx":"c4996d025aae","ui_kits/console/data.jsx":"39994e9698fb","ui_kits/docs/DocsApp.jsx":"220cdfd8a1a6","ui_kits/docs/DocsParts.jsx":"2b9c233b33d3","ui_kits/mobile/MobileApp.jsx":"418bcbe91b80","ui_kits/mobile/Phone.jsx":"54bf0963183c","ui_kits/mobile/Screens.jsx":"27d4a0b1e9a5","ui_kits/mobile/data.jsx":"39994e9698fb"},"inlinedExternals":[],"unexposedExports":[{"name":"cx","sourcePath":"components/internal/sheet.jsx"},{"name":"injectControlBase","sourcePath":"components/internal/sheet.jsx"},{"name":"injectFont","sourcePath":"components/internal/sheet.jsx"},{"name":"injectSheet","sourcePath":"components/internal/sheet.jsx"}]} */

(() => {

const __ds_ns = (window.AreyDesignSystem_1909f9 = window.AreyDesignSystem_1909f9 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/internal/sheet.jsx
try { (() => {
// Injects a component's CSS rules once per document. Lets components use real
// :hover / :active / :focus-visible / :disabled states instead of JS state juggling,
// while every value still comes from the design-system custom properties.
const seen = new Set();
function injectSheet(id, css) {
  if (typeof document === 'undefined' || seen.has(id)) return;
  seen.add(id);
  const el = document.createElement('style');
  el.setAttribute('data-arey', id);
  el.textContent = css;
  document.head.appendChild(el);
}
function injectFont(href, id) {
  if (typeof document === 'undefined' || seen.has(id)) return;
  seen.add(id);
  const l = document.createElement('link');
  l.rel = 'stylesheet';
  l.href = href;
  l.setAttribute('data-arey', id);
  document.head.appendChild(l);
}
function cx() {
  return Array.prototype.filter.call(arguments, Boolean).join(' ');
}

// Shared text-control base. Injected once so Input and Select can't clobber each
// other's modifiers by re-declaring .arey-input in a later stylesheet.
function injectControlBase() {
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
Object.assign(__ds_scope, { injectSheet, injectFont, cx, injectControlBase });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/internal/sheet.jsx", error: String((e && e.message) || e) }); }

// components/core/Avatar.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-avatar', `
.arey-avatar{--_s:32px;position:relative;display:inline-grid;place-items:center;flex:none;width:var(--_s);height:var(--_s);
  border-radius:var(--radius-full);background:var(--bg-inset);color:var(--text-secondary);overflow:hidden;
  font:var(--weight-medium) calc(var(--_s) * .38)/1 var(--font-sans);letter-spacing:0;
  box-shadow:0 0 0 1px var(--border-subtle) inset;user-select:none}
.arey-avatar img{width:100%;height:100%;object-fit:cover;display:block}
.arey-avatar--xs{--_s:20px}.arey-avatar--sm{--_s:24px}.arey-avatar--lg{--_s:40px}.arey-avatar--xl{--_s:56px}
.arey-avatar--square{border-radius:var(--radius-md)}
.arey-avatar--accent{background:var(--accent-wash);color:var(--text-accent)}
.arey-avatar-stack{display:inline-flex}
.arey-avatar-stack > .arey-avatar{box-shadow:0 0 0 2px var(--surface-card)}
.arey-avatar-stack > .arey-avatar + .arey-avatar{margin-left:-8px}
`);
function initials(name) {
  return String(name || '').trim().split(/\s+/).slice(0, 2).map(function (p) {
    return p[0];
  }).join('').toUpperCase();
}

/** Person or project identity. Pill by default, square for projects. */
function Avatar({
  name,
  src,
  size = 'md',
  square = false,
  tone = 'neutral',
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("span", _extends({
    className: __ds_scope.cx('arey-avatar', size !== 'md' && 'arey-avatar--' + size, square && 'arey-avatar--square', tone === 'accent' && 'arey-avatar--accent', className),
    title: name
  }, rest), src ? /*#__PURE__*/React.createElement("img", {
    src: src,
    alt: name || ''
  }) : initials(name));
}

/** Overlapping row of avatars. */
function AvatarStack({
  people = [],
  max = 4,
  size = 'sm'
}) {
  const shown = people.slice(0, max);
  const rest = people.length - shown.length;
  return /*#__PURE__*/React.createElement("span", {
    className: "arey-avatar-stack"
  }, shown.map(function (p, i) {
    return /*#__PURE__*/React.createElement(Avatar, {
      key: i,
      size: size,
      name: p.name,
      src: p.src
    });
  }), rest > 0 && /*#__PURE__*/React.createElement(Avatar, {
    size: size,
    name: '+' + rest
  }));
}
Object.assign(__ds_scope, { Avatar, AvatarStack });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Avatar.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-card', `
.arey-card{background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-card);
  box-shadow:var(--shadow-md);color:var(--text-body);transition:var(--transition-surface),border-color var(--duration-fast) var(--ease-out)}
.arey-card--flat{box-shadow:none;border-color:var(--border-default)}
.arey-card--inset{background:var(--bg-inset);box-shadow:none;border-color:transparent}
.arey-card--glass{background:var(--surface-glass);border-color:var(--border-glass);
  backdrop-filter:var(--backdrop-glass);-webkit-backdrop-filter:var(--backdrop-glass);box-shadow:var(--shadow-lg)}
.arey-card--interactive{cursor:pointer;text-align:left;display:block;width:100%}
.arey-card--interactive:hover{box-shadow:var(--shadow-lg);transform:translateY(-1px);border-color:var(--border-default)}
.arey-card--interactive:active{transform:scale(.995)}
.arey-card--interactive:focus-visible{outline:none;box-shadow:var(--ring-focus)}
.arey-card__head{display:flex;align-items:flex-start;gap:var(--space-4);padding:var(--pad-card);padding-bottom:0}
.arey-card__title{font:var(--type-title-3);letter-spacing:var(--tracking-heading);color:var(--text-primary)}
.arey-card__desc{font:var(--type-caption);color:var(--text-secondary);margin-top:var(--space-1)}
.arey-card__body{padding:var(--pad-card)}
.arey-card__foot{display:flex;align-items:center;gap:var(--space-3);padding:var(--space-4) var(--pad-card);
  border-top:1px solid var(--border-subtle);background:var(--bg-subtle);
  border-radius:0 0 calc(var(--radius-card) - 1px) calc(var(--radius-card) - 1px)}
`);

/** The standard surface: hairline border + soft shadow, both always. */
function Card({
  variant = 'default',
  interactive = false,
  title,
  description,
  action,
  footer,
  padded = true,
  as,
  className,
  children,
  ...rest
}) {
  const Tag = as || (interactive ? 'button' : 'div');
  return /*#__PURE__*/React.createElement(Tag, _extends({
    className: __ds_scope.cx('arey-card', variant !== 'default' && 'arey-card--' + variant, interactive && 'arey-card--interactive', className)
  }, rest), (title || action) && /*#__PURE__*/React.createElement("div", {
    className: "arey-card__head"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, title && /*#__PURE__*/React.createElement("div", {
    className: "arey-card__title"
  }, title), description && /*#__PURE__*/React.createElement("div", {
    className: "arey-card__desc"
  }, description)), action), children != null && (padded ? /*#__PURE__*/React.createElement("div", {
    className: "arey-card__body"
  }, children) : children), footer && /*#__PURE__*/React.createElement("div", {
    className: "arey-card__foot"
  }, footer));
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/Icon.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const CDN = 'https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src';
__ds_scope.injectFont(CDN + '/regular/style.css', 'ph-regular');
__ds_scope.injectFont(CDN + '/bold/style.css', 'ph-bold');
__ds_scope.injectFont(CDN + '/fill/style.css', 'ph-fill');
__ds_scope.injectFont(CDN + '/duotone/style.css', 'ph-duotone');
__ds_scope.injectSheet('arey-icon', `
.arey-icon{display:inline-flex;align-items:center;justify-content:center;flex:none;line-height:1;color:inherit}
`);

/** Phosphor glyph. Regular is default; Fill marks a selected state only. */
function Icon({
  name,
  size = 16,
  weight = 'regular',
  color,
  className,
  style,
  label,
  ...rest
}) {
  const cls = weight === 'regular' ? 'ph' : 'ph-' + weight;
  return /*#__PURE__*/React.createElement("span", _extends({
    className: __ds_scope.cx('arey-icon', className),
    style: {
      width: size,
      height: size,
      fontSize: size,
      color,
      ...style
    },
    role: label ? 'img' : undefined,
    "aria-label": label,
    "aria-hidden": label ? undefined : true
  }, rest), /*#__PURE__*/React.createElement("i", {
    className: cls + ' ph-' + name
  }));
}
Object.assign(__ds_scope, { Icon });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Icon.jsx", error: String((e && e.message) || e) }); }

// components/core/Badge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-badge', `
.arey-badge{display:inline-flex;align-items:center;gap:var(--space-2);height:24px;padding:0 var(--space-3);
  border-radius:var(--radius-full);font:var(--type-caption);font-weight:var(--weight-medium);
  background:var(--bg-inset);color:var(--text-secondary);white-space:nowrap;border:1px solid transparent}
.arey-badge--sm{height:20px;padding:0 var(--space-2);font-size:var(--text-11)}
.arey-badge__dot{width:6px;height:6px;border-radius:50%;background:currentColor;flex:none}
.arey-badge--accent{background:var(--accent-wash);color:var(--text-accent)}
.arey-badge--success{background:var(--success-wash);color:var(--success-text)}
.arey-badge--danger{background:var(--danger-wash);color:var(--danger-text)}
.arey-badge--warning{background:var(--warning-wash);color:var(--warning-text)}
.arey-badge--outline{background:transparent;border-color:var(--border-default);color:var(--text-secondary)}
.arey-badge--mono{font-family:var(--font-mono);letter-spacing:0}
`);

/** Status pill. Wash + text pair, optional 6px dot. */
function Badge({
  tone = 'neutral',
  dot = false,
  icon,
  size = 'md',
  mono = false,
  className,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("span", _extends({
    className: __ds_scope.cx('arey-badge', tone !== 'neutral' && 'arey-badge--' + tone, size === 'sm' && 'arey-badge--sm', mono && 'arey-badge--mono', className)
  }, rest), dot && /*#__PURE__*/React.createElement("span", {
    className: "arey-badge__dot"
  }), icon && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: 12,
    weight: "bold"
  }), children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/IconButton.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-iconbutton', `
.arey-iconbtn{--_s:36px;display:inline-flex;align-items:center;justify-content:center;flex:none;
  width:var(--_s);height:var(--_s);border-radius:var(--radius-control);border:1px solid transparent;
  background:transparent;color:var(--text-secondary);cursor:pointer;transition:var(--transition-control);
  -webkit-tap-highlight-color:transparent}
.arey-iconbtn:hover:not(:disabled){background:var(--bg-hover);color:var(--text-primary)}
.arey-iconbtn:active:not(:disabled){background:var(--bg-active);transform:scale(var(--press-scale))}
.arey-iconbtn:focus-visible{outline:none;box-shadow:var(--ring-focus)}
.arey-iconbtn:disabled{opacity:.4;cursor:not-allowed}
.arey-iconbtn--sm{--_s:28px;border-radius:var(--radius-md)}
.arey-iconbtn--lg{--_s:44px}
.arey-iconbtn--bordered{border-color:var(--border-default);background:var(--surface-card);color:var(--text-primary);box-shadow:var(--shadow-xs)}
.arey-iconbtn--bordered:hover:not(:disabled){border-color:var(--border-strong);background:var(--bg-subtle)}
.arey-iconbtn--round{border-radius:var(--radius-full)}
.arey-iconbtn[aria-pressed="true"]{background:var(--bg-selected);color:var(--text-accent)}
`);

/** Square, icon-only control. Always ≥36px on web, ≥44px on mobile. */
function IconButton({
  icon,
  label,
  size = 'md',
  variant = 'ghost',
  round = false,
  weight = 'regular',
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    "aria-label": label,
    className: __ds_scope.cx('arey-iconbtn', size !== 'md' && 'arey-iconbtn--' + size, variant === 'bordered' && 'arey-iconbtn--bordered', round && 'arey-iconbtn--round', className)
  }, rest), /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    weight: weight,
    size: size === 'sm' ? 14 : size === 'lg' ? 20 : 16
  }));
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/core/Kbd.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-kbd', `
.arey-kbd{display:inline-flex;align-items:center;gap:2px;font:var(--weight-medium) var(--text-11)/1 var(--font-mono);font-family:var(--font-mono),"Helvetica Neue",system-ui,sans-serif;color:var(--text-tertiary)}
.arey-kbd kbd{display:inline-grid;place-items:center;min-width:20px;height:20px;padding:0 5px;
  border:1px solid var(--border-default);border-bottom-width:2px;border-radius:var(--radius-sm);
  background:var(--surface-card);color:var(--text-secondary);font:inherit}
`);
const GLYPH = {
  cmd: '\u2318',
  meta: '\u2318',
  alt: '\u2325',
  option: '\u2325',
  shift: '\u21E7',
  ctrl: '\u2303',
  enter: '\u21B5',
  esc: 'esc',
  tab: '\u21E5',
  up: '\u2191',
  down: '\u2193',
  backspace: '\u232B'
};

/** Keyboard shortcut. The one place unicode glyphs are correct typography. */
function Kbd({
  keys,
  className,
  ...rest
}) {
  const list = Array.isArray(keys) ? keys : String(keys).split('+');
  return /*#__PURE__*/React.createElement("span", _extends({
    className: __ds_scope.cx('arey-kbd', className)
  }, rest), list.map(function (k, i) {
    const t = String(k).trim();
    return /*#__PURE__*/React.createElement("kbd", {
      key: i
    }, GLYPH[t.toLowerCase()] || t.toUpperCase());
  }));
}
Object.assign(__ds_scope, { Kbd });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Kbd.jsx", error: String((e && e.message) || e) }); }

// components/core/Tag.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-tag', `
.arey-tag{display:inline-flex;align-items:center;gap:var(--space-2);height:28px;padding:0 var(--space-3);
  border-radius:var(--radius-full);border:1px solid var(--border-default);background:var(--surface-card);
  color:var(--text-body);font:var(--type-label);transition:var(--transition-control)}
.arey-tag--selectable{cursor:pointer}
.arey-tag--selectable:hover{background:var(--bg-hover);border-color:var(--border-strong)}
.arey-tag--selectable:active{transform:scale(var(--press-scale))}
.arey-tag--selectable:focus-visible{outline:none;box-shadow:var(--ring-focus)}
.arey-tag[aria-pressed="true"]{background:var(--bg-selected);border-color:var(--accent-border);color:var(--text-accent)}
.arey-tag__x{display:inline-flex;margin-right:calc(var(--space-1) * -1);padding:2px;border:0;background:none;
  color:var(--text-tertiary);cursor:pointer;border-radius:var(--radius-full);transition:var(--transition-control)}
.arey-tag__x:hover{background:var(--bg-active);color:var(--text-primary)}
`);

/** Filter chip / removable token. Selectable renders a button. */
function Tag({
  icon,
  selected,
  onRemove,
  onClick,
  className,
  children,
  ...rest
}) {
  const selectable = !!onClick;
  const Tag_ = selectable ? 'button' : 'span';
  return /*#__PURE__*/React.createElement(Tag_, _extends({
    className: __ds_scope.cx('arey-tag', selectable && 'arey-tag--selectable', className),
    "aria-pressed": selectable ? !!selected : undefined,
    onClick: onClick
  }, rest), icon && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: 14
  }), children, onRemove && /*#__PURE__*/React.createElement("span", {
    className: "arey-tag__x",
    role: "button",
    tabIndex: 0,
    "aria-label": "Remove",
    onClick: function (e) {
      e.stopPropagation();
      onRemove(e);
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "x",
    size: 12,
    weight: "bold"
  })));
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Tag.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Dialog.jsx
try { (() => {
__ds_scope.injectSheet('arey-dialog', `
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
function Dialog({
  open = true,
  title,
  description,
  footer,
  size = 'md',
  onClose,
  className,
  children
}) {
  React.useEffect(function () {
    if (!open || !onClose) return;
    function onKey(e) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKey);
    return function () {
      document.removeEventListener('keydown', onKey);
    };
  }, [open, onClose]);
  if (!open) return null;
  return /*#__PURE__*/React.createElement("div", {
    className: "arey-dialog__scrim",
    onClick: function (e) {
      if (e.target === e.currentTarget && onClose) onClose();
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: __ds_scope.cx('arey-dialog', size !== 'md' && 'arey-dialog--' + size, className),
    role: "dialog",
    "aria-modal": "true",
    "aria-label": typeof title === 'string' ? title : undefined
  }, (title || onClose) && /*#__PURE__*/React.createElement("div", {
    className: "arey-dialog__head"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, title && /*#__PURE__*/React.createElement("div", {
    className: "arey-dialog__title"
  }, title), description && /*#__PURE__*/React.createElement("div", {
    className: "arey-dialog__desc"
  }, description)), onClose && /*#__PURE__*/React.createElement(__ds_scope.IconButton, {
    icon: "x",
    label: "Close",
    size: "sm",
    onClick: onClose
  })), children != null && /*#__PURE__*/React.createElement("div", {
    className: "arey-dialog__body"
  }, children), footer && /*#__PURE__*/React.createElement("div", {
    className: "arey-dialog__foot"
  }, footer)));
}
Object.assign(__ds_scope, { Dialog });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Dialog.jsx", error: String((e && e.message) || e) }); }

// components/feedback/EmptyState.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-empty', `
.arey-empty{display:grid;justify-items:center;text-align:center;gap:var(--space-3);
  padding:var(--space-16) var(--space-8);color:var(--text-secondary)}
.arey-empty__glyph{display:grid;place-items:center;width:56px;height:56px;border-radius:var(--radius-card);
  background:var(--bg-inset);color:var(--text-tertiary);margin-bottom:var(--space-2)}
.arey-empty__title{font:var(--type-title-3);letter-spacing:var(--tracking-heading);color:var(--text-primary)}
.arey-empty__desc{font:var(--type-body);color:var(--text-secondary);max-width:44ch}
.arey-empty--compact{padding:var(--space-10) var(--space-6)}
`);

/** One line of what's missing, one action. Centred — the only place arey centres body copy. */
function EmptyState({
  icon = 'folder-open',
  title,
  description,
  action,
  compact = false,
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: __ds_scope.cx('arey-empty', compact && 'arey-empty--compact', className)
  }, rest), /*#__PURE__*/React.createElement("div", {
    className: "arey-empty__glyph"
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: 24
  })), /*#__PURE__*/React.createElement("div", {
    className: "arey-empty__title"
  }, title), description && /*#__PURE__*/React.createElement("div", {
    className: "arey-empty__desc"
  }, description), action && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 'var(--space-3)'
    }
  }, action));
}
Object.assign(__ds_scope, { EmptyState });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/EmptyState.jsx", error: String((e && e.message) || e) }); }

// components/feedback/ProgressBar.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-progress', `
.arey-progress{position:relative;width:100%;height:6px;border-radius:var(--radius-full);
  background:var(--bg-inset);overflow:hidden}
.arey-progress--thin{height:2px;border-radius:0}
.arey-progress__fill{height:100%;border-radius:inherit;background:var(--accent-solid);
  transition:width var(--duration-slow) var(--ease-out)}
.arey-progress__fill--success{background:var(--success-solid)}
.arey-progress__fill--danger{background:var(--danger-solid)}
.arey-progress__fill--warning{background:var(--warning-solid)}
.arey-progress--indeterminate .arey-progress__fill{width:40%;animation:arey-slide 1.4s var(--ease-in-out) infinite}
@keyframes arey-slide{0%{transform:translateX(-100%)}100%{transform:translateX(250%)}}
`);

/** Determinate or indeterminate progress. `thin` is the 2px page-loading bar. */
function ProgressBar({
  value = 0,
  tone = 'accent',
  thin = false,
  indeterminate = false,
  className,
  ...rest
}) {
  const pct = Math.max(0, Math.min(100, value));
  return /*#__PURE__*/React.createElement("div", _extends({
    className: __ds_scope.cx('arey-progress', thin && 'arey-progress--thin', indeterminate && 'arey-progress--indeterminate', className),
    role: "progressbar",
    "aria-valuenow": indeterminate ? undefined : pct,
    "aria-valuemin": 0,
    "aria-valuemax": 100
  }, rest), /*#__PURE__*/React.createElement("div", {
    className: __ds_scope.cx('arey-progress__fill', tone !== 'accent' && 'arey-progress__fill--' + tone),
    style: {
      width: indeterminate ? undefined : pct + '%'
    }
  }));
}
Object.assign(__ds_scope, { ProgressBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/ProgressBar.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Spinner.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-spinner', `
.arey-spinner{display:inline-block;flex:none;border-radius:50%;border-style:solid;
  border-color:currentColor;border-right-color:transparent;opacity:.7;
  animation:arey-spin .7s linear infinite}
@keyframes arey-spin{to{transform:rotate(360deg)}}
@media (prefers-reduced-motion:reduce){.arey-spinner{animation-duration:1.6s}}
`);

/** Indeterminate activity. Replaces a control's label rather than sitting beside it. */
function Spinner({
  size = 16,
  thickness,
  className,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("span", _extends({
    className: __ds_scope.cx('arey-spinner', className),
    role: "status",
    "aria-label": "Loading",
    style: {
      width: size,
      height: size,
      borderWidth: thickness || Math.max(1.5, Math.round(size / 9)),
      ...style
    }
  }, rest));
}
Object.assign(__ds_scope, { Spinner });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Spinner.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-button', `
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
function Button({
  variant = 'secondary',
  size = 'md',
  iconLeft,
  iconRight,
  loading = false,
  block = false,
  disabled,
  as = 'button',
  className,
  children,
  ...rest
}) {
  const Tag = as;
  return /*#__PURE__*/React.createElement(Tag, _extends({
    className: __ds_scope.cx('arey-btn', 'arey-btn--' + variant, size !== 'md' && 'arey-btn--' + size, block && 'arey-btn--block', className),
    disabled: Tag === 'button' ? disabled || loading : undefined,
    "aria-disabled": Tag !== 'button' && (disabled || loading) ? true : undefined,
    "aria-busy": loading || undefined
  }, rest), loading ? /*#__PURE__*/React.createElement(__ds_scope.Spinner, {
    size: size === 'sm' ? 12 : 14
  }) : iconLeft ? /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: iconLeft,
    size: size === 'lg' ? 18 : 16
  }) : null, children, iconRight && !loading ? /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: iconRight,
    size: size === 'lg' ? 18 : 16
  }) : null);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Toast.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-toast', `
.arey-toast{display:flex;align-items:flex-start;gap:var(--space-3);min-width:280px;max-width:400px;
  padding:var(--space-4);border-radius:var(--radius-card);
  background:var(--surface-overlay);border:1px solid var(--border-glass);
  backdrop-filter:var(--backdrop-glass);-webkit-backdrop-filter:var(--backdrop-glass);
  box-shadow:var(--shadow-lg);color:var(--text-body);
  animation:arey-toast-in var(--duration-normal) var(--ease-out)}
.arey-toast__icon{margin-top:1px;color:var(--text-tertiary)}
.arey-toast--success .arey-toast__icon{color:var(--success-solid)}
.arey-toast--danger .arey-toast__icon{color:var(--danger-solid)}
.arey-toast--warning .arey-toast__icon{color:var(--warning-solid)}
.arey-toast__title{font:var(--type-label);color:var(--text-primary)}
.arey-toast__desc{font:var(--type-caption);color:var(--text-secondary);margin-top:2px}
.arey-toast-region{position:fixed;z-index:120;right:var(--space-6);bottom:var(--space-6);
  display:flex;flex-direction:column;gap:var(--space-3);align-items:flex-end}
@keyframes arey-toast-in{from{opacity:0;transform:translateY(8px) scale(.98)}to{opacity:1;transform:none}}
`);
const ICONS = {
  neutral: 'info',
  success: 'check-circle',
  danger: 'warning-octagon',
  warning: 'warning'
};

/** Transient confirmation on a glass surface. One line of what happened. */
function Toast({
  tone = 'neutral',
  title,
  description,
  action,
  onDismiss,
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: __ds_scope.cx('arey-toast', tone !== 'neutral' && 'arey-toast--' + tone, className),
    role: "status"
  }, rest), /*#__PURE__*/React.createElement("span", {
    className: "arey-toast__icon"
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: ICONS[tone],
    size: 16,
    weight: "fill"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "arey-toast__title"
  }, title), description && /*#__PURE__*/React.createElement("div", {
    className: "arey-toast__desc"
  }, description), action && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 'var(--space-3)'
    }
  }, action)), onDismiss && /*#__PURE__*/React.createElement(__ds_scope.IconButton, {
    icon: "x",
    label: "Dismiss",
    size: "sm",
    onClick: onDismiss
  }));
}

/** Bottom-right stack. */
function ToastRegion({
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "arey-toast-region"
  }, children);
}
Object.assign(__ds_scope, { Toast, ToastRegion });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Toast.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Tooltip.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-tooltip', `
.arey-tooltip{position:relative;display:inline-flex}
.arey-tooltip__pop{position:absolute;z-index:60;pointer-events:none;
  padding:6px var(--space-3);border-radius:var(--radius-md);
  background:var(--surface-overlay);border:1px solid var(--border-glass);
  backdrop-filter:var(--backdrop-glass);-webkit-backdrop-filter:var(--backdrop-glass);
  box-shadow:var(--shadow-lg);color:var(--text-primary);
  font:var(--type-caption);white-space:nowrap;
  opacity:0;transform:translateY(2px) scale(.97);
  transition:opacity var(--duration-fast) var(--ease-out),transform var(--duration-fast) var(--ease-out)}
.arey-tooltip__pop[data-open="true"]{opacity:1;transform:translateY(0) scale(1)}
.arey-tooltip__pop[data-side="top"]{bottom:calc(100% + 8px);left:50%;margin-left:-50%;
  display:flex;justify-content:center;width:100%}
.arey-tooltip__pop--mono{font-family:var(--font-mono);font-size:var(--text-11)}
`);

/** Hover / focus hint. Glass surface, 8px offset, never contains an action. */
function Tooltip({
  label,
  mono = false,
  children,
  className,
  ...rest
}) {
  const [open, setOpen] = React.useState(false);
  return /*#__PURE__*/React.createElement("span", _extends({
    className: __ds_scope.cx('arey-tooltip', className),
    onMouseEnter: function () {
      setOpen(true);
    },
    onMouseLeave: function () {
      setOpen(false);
    },
    onFocus: function () {
      setOpen(true);
    },
    onBlur: function () {
      setOpen(false);
    }
  }, rest), children, /*#__PURE__*/React.createElement("span", {
    className: __ds_scope.cx('arey-tooltip__pop', mono && 'arey-tooltip__pop--mono'),
    "data-side": "top",
    "data-open": open,
    role: "tooltip"
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      background: 'inherit'
    }
  }, label)));
}
Object.assign(__ds_scope, { Tooltip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Tooltip.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-checkbox', `
.arey-check{display:inline-flex;align-items:flex-start;gap:var(--space-3);cursor:pointer;
  font:var(--type-body);color:var(--text-body)}
.arey-check input{position:absolute;opacity:0;width:0;height:0}
.arey-check__box{position:relative;flex:none;width:18px;height:18px;margin-top:1px;border-radius:var(--radius-sm);
  border:1px solid var(--border-strong);background:var(--bg-base);box-shadow:var(--shadow-xs);
  transition:var(--transition-control)}
.arey-check:hover .arey-check__box{border-color:var(--accent-solid)}
.arey-check:active .arey-check__box{transform:scale(var(--press-scale))}
.arey-check__box::after{content:"";position:absolute;left:5px;top:2px;width:5px;height:9px;
  border:solid #fff;border-width:0 2px 2px 0;transform:rotate(45deg) scale(.4);opacity:0;
  transition:opacity var(--duration-fast) var(--ease-out),transform var(--duration-fast) var(--ease-spring)}
.arey-check input:checked + .arey-check__box{background:var(--accent-solid);border-color:var(--accent-solid)}
.arey-check input:checked + .arey-check__box::after{opacity:1;transform:rotate(45deg) scale(1)}
.arey-check input:indeterminate + .arey-check__box{background:var(--accent-solid);border-color:var(--accent-solid)}
.arey-check input:indeterminate + .arey-check__box::after{opacity:1;left:3px;top:7px;width:10px;height:0;
  border-width:0 0 2px 0;transform:none}
.arey-check input:focus-visible + .arey-check__box{box-shadow:var(--ring-focus);border-color:var(--accent-solid)}
.arey-check input:disabled ~ *{opacity:.4}
.arey-check__text{display:grid;gap:2px}
.arey-check__desc{font:var(--type-caption);color:var(--text-secondary)}
`);

/** Multi-select control. Label sits to the right, always clickable. */
function Checkbox({
  label,
  description,
  indeterminate = false,
  className,
  ...rest
}) {
  const ref = React.useRef(null);
  React.useEffect(function () {
    if (ref.current) ref.current.indeterminate = indeterminate;
  }, [indeterminate]);
  return /*#__PURE__*/React.createElement("label", {
    className: __ds_scope.cx('arey-check', className)
  }, /*#__PURE__*/React.createElement("input", _extends({
    ref: ref,
    type: "checkbox"
  }, rest)), /*#__PURE__*/React.createElement("span", {
    className: "arey-check__box"
  }), (label || description) && /*#__PURE__*/React.createElement("span", {
    className: "arey-check__text"
  }, label, description && /*#__PURE__*/React.createElement("span", {
    className: "arey-check__desc"
  }, description)));
}
Object.assign(__ds_scope, { Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/Field.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-field', `
.arey-field{display:grid;gap:var(--space-2)}
.arey-field__label{display:flex;align-items:center;gap:var(--space-2);font:var(--type-label);color:var(--text-primary)}
.arey-field__opt{font:var(--type-caption);color:var(--text-tertiary);font-weight:var(--weight-regular)}
.arey-field__hint{font:var(--type-caption);color:var(--text-secondary)}
.arey-field__error{display:flex;align-items:center;gap:var(--space-2);font:var(--type-caption);color:var(--danger-text)}
.arey-field--row{grid-template-columns:200px 1fr;gap:var(--space-6);align-items:start}
`);

/** Label + helper + error wrapper shared by every form control. */
function Field({
  label,
  hint,
  error,
  optional = false,
  htmlFor,
  layout = 'stack',
  className,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: __ds_scope.cx('arey-field', layout === 'row' && 'arey-field--row', className)
  }, rest), label && /*#__PURE__*/React.createElement("label", {
    className: "arey-field__label",
    htmlFor: htmlFor
  }, label, optional && /*#__PURE__*/React.createElement("span", {
    className: "arey-field__opt"
  }, "Optional")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-2)'
    }
  }, children, error ? /*#__PURE__*/React.createElement("div", {
    className: "arey-field__error"
  }, error) : hint ? /*#__PURE__*/React.createElement("div", {
    className: "arey-field__hint"
  }, hint) : null));
}
Object.assign(__ds_scope, { Field });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Field.jsx", error: String((e && e.message) || e) }); }

// components/forms/Input.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectControlBase();
__ds_scope.injectSheet('arey-input', `
.arey-input-wrap{position:relative;display:flex;align-items:center}
.arey-input-wrap__icon{position:absolute;left:var(--space-3);color:var(--text-tertiary);pointer-events:none;display:flex}
.arey-input-wrap__suffix{position:absolute;right:var(--space-3);display:flex;align-items:center;gap:var(--space-2);color:var(--text-tertiary)}
`);
/** Single-line text control. */
function Input({
  size = 'md',
  icon,
  suffix,
  mono = false,
  invalid = false,
  className,
  style,
  ...rest
}) {
  const input = /*#__PURE__*/React.createElement("input", _extends({
    className: __ds_scope.cx('arey-input', size !== 'md' && 'arey-input--' + size, icon && 'arey-input--has-icon', mono && 'arey-input--mono', invalid && 'arey-input--invalid', className),
    "aria-invalid": invalid || undefined,
    style: suffix ? {
      paddingRight: 64,
      ...style
    } : style
  }, rest));
  if (!icon && !suffix) return input;
  return /*#__PURE__*/React.createElement("span", {
    className: "arey-input-wrap"
  }, icon && /*#__PURE__*/React.createElement("span", {
    className: "arey-input-wrap__icon"
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: 16
  })), input, suffix && /*#__PURE__*/React.createElement("span", {
    className: "arey-input-wrap__suffix"
  }, suffix));
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Input.jsx", error: String((e && e.message) || e) }); }

// components/forms/Radio.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-radio', `
.arey-radio{display:inline-flex;align-items:flex-start;gap:var(--space-3);cursor:pointer;font:var(--type-body);color:var(--text-body)}
.arey-radio input{position:absolute;opacity:0;width:0;height:0}
.arey-radio__dot{position:relative;flex:none;width:18px;height:18px;margin-top:1px;border-radius:50%;
  border:1px solid var(--border-strong);background:var(--bg-base);box-shadow:var(--shadow-xs);transition:var(--transition-control)}
.arey-radio:hover .arey-radio__dot{border-color:var(--accent-solid)}
.arey-radio:active .arey-radio__dot{transform:scale(var(--press-scale))}
.arey-radio__dot::after{content:"";position:absolute;inset:0;margin:auto;width:7px;height:7px;border-radius:50%;
  background:#fff;transform:scale(.3);opacity:0;transition:opacity var(--duration-fast) var(--ease-out),transform var(--duration-fast) var(--ease-spring)}
.arey-radio input:checked + .arey-radio__dot{background:var(--accent-solid);border-color:var(--accent-solid)}
.arey-radio input:checked + .arey-radio__dot::after{opacity:1;transform:scale(1)}
.arey-radio input:focus-visible + .arey-radio__dot{box-shadow:var(--ring-focus);border-color:var(--accent-solid)}
.arey-radio input:disabled ~ *{opacity:.4}
.arey-radio__text{display:grid;gap:2px}
.arey-radio__desc{font:var(--type-caption);color:var(--text-secondary)}
.arey-radio-group{display:grid;gap:var(--space-4)}
.arey-radio-group--row{grid-auto-flow:column;justify-content:start;gap:var(--space-6)}
`);

/** Single choice among 2–4 visible options. */
function Radio({
  label,
  description,
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("label", {
    className: __ds_scope.cx('arey-radio', className)
  }, /*#__PURE__*/React.createElement("input", _extends({
    type: "radio"
  }, rest)), /*#__PURE__*/React.createElement("span", {
    className: "arey-radio__dot"
  }), (label || description) && /*#__PURE__*/React.createElement("span", {
    className: "arey-radio__text"
  }, label, description && /*#__PURE__*/React.createElement("span", {
    className: "arey-radio__desc"
  }, description)));
}

/** Layout wrapper that shares a name across its radios. */
function RadioGroup({
  name,
  value,
  onChange,
  options = [],
  direction = 'column',
  className
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: __ds_scope.cx('arey-radio-group', direction === 'row' && 'arey-radio-group--row', className),
    role: "radiogroup"
  }, options.map(function (o, i) {
    return /*#__PURE__*/React.createElement(Radio, {
      key: i,
      name: name,
      value: o.value,
      label: o.label,
      description: o.description,
      checked: value === o.value,
      onChange: function () {
        if (onChange) onChange(o.value);
      }
    });
  }));
}
Object.assign(__ds_scope, { Radio, RadioGroup });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Radio.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectControlBase();
__ds_scope.injectSheet('arey-select', `
.arey-select-wrap{position:relative;display:flex;align-items:center}
.arey-select{appearance:none;-webkit-appearance:none;padding-right:34px;cursor:pointer}
.arey-select-wrap__caret{position:absolute;right:var(--space-3);color:var(--text-tertiary);pointer-events:none;display:flex}
`);
/** Native select in arey clothing. */
function Select({
  options = [],
  size = 'md',
  placeholder,
  invalid = false,
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("span", {
    className: "arey-select-wrap"
  }, /*#__PURE__*/React.createElement("select", _extends({
    className: __ds_scope.cx('arey-input', 'arey-select', size !== 'md' && 'arey-input--' + size, invalid && 'arey-input--invalid', className),
    "aria-invalid": invalid || undefined
  }, rest), placeholder && /*#__PURE__*/React.createElement("option", {
    value: ""
  }, placeholder), options.map(function (o, i) {
    const opt = typeof o === 'string' ? {
      value: o,
      label: o
    } : o;
    return /*#__PURE__*/React.createElement("option", {
      key: i,
      value: opt.value,
      disabled: opt.disabled
    }, opt.label);
  })), /*#__PURE__*/React.createElement("span", {
    className: "arey-select-wrap__caret"
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "caret-up-down",
    size: 14
  })));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/Switch.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-switch', `
.arey-switch{display:inline-flex;align-items:center;gap:var(--space-3);cursor:pointer;font:var(--type-body);color:var(--text-body)}
.arey-switch input{position:absolute;opacity:0;width:0;height:0}
.arey-switch__track{position:relative;flex:none;width:42px;height:26px;border-radius:var(--radius-full);
  background:var(--grey-300);transition:background-color var(--duration-normal) var(--ease-out),box-shadow var(--duration-fast) var(--ease-out)}
[data-theme="dark"] .arey-switch__track{background:#39393d}
.arey-switch__track::after{content:"";position:absolute;top:2px;left:2px;width:22px;height:22px;border-radius:50%;
  background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.25);
  transition:transform var(--duration-normal) var(--ease-spring)}
.arey-switch input:checked + .arey-switch__track{background:var(--success-solid)}
.arey-switch--accent input:checked + .arey-switch__track{background:var(--accent-solid)}
.arey-switch input:checked + .arey-switch__track::after{transform:translateX(16px)}
.arey-switch:active .arey-switch__track::after{width:24px}
.arey-switch input:focus-visible + .arey-switch__track{box-shadow:var(--ring-focus)}
.arey-switch input:disabled ~ *{opacity:.4}
.arey-switch--sm .arey-switch__track{width:34px;height:20px}
.arey-switch--sm .arey-switch__track::after{width:16px;height:16px}
.arey-switch--sm input:checked + .arey-switch__track::after{transform:translateX(14px)}
.arey-switch__text{display:grid;gap:2px}
.arey-switch__desc{font:var(--type-caption);color:var(--text-secondary)}
`);

/** Immediate on/off. Never needs a Save button. */
function Switch({
  label,
  description,
  tone = 'success',
  size = 'md',
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("label", {
    className: __ds_scope.cx('arey-switch', tone === 'accent' && 'arey-switch--accent', size === 'sm' && 'arey-switch--sm', className)
  }, /*#__PURE__*/React.createElement("input", _extends({
    type: "checkbox",
    role: "switch"
  }, rest)), /*#__PURE__*/React.createElement("span", {
    className: "arey-switch__track"
  }), (label || description) && /*#__PURE__*/React.createElement("span", {
    className: "arey-switch__text"
  }, label, description && /*#__PURE__*/React.createElement("span", {
    className: "arey-switch__desc"
  }, description)));
}
Object.assign(__ds_scope, { Switch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Switch.jsx", error: String((e && e.message) || e) }); }

// components/forms/Textarea.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-textarea', `
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
function Textarea({
  mono = false,
  invalid = false,
  rows = 4,
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("textarea", _extends({
    rows: rows,
    className: __ds_scope.cx('arey-textarea', mono && 'arey-textarea--mono', invalid && 'arey-textarea--invalid', className),
    "aria-invalid": invalid || undefined
  }, rest));
}
Object.assign(__ds_scope, { Textarea });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Textarea.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Breadcrumbs.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-breadcrumbs', `
.arey-crumbs{display:flex;align-items:center;gap:var(--space-2);font:var(--type-label);color:var(--text-secondary);min-width:0}
.arey-crumbs a,.arey-crumbs__item{color:var(--text-secondary);text-decoration:none;white-space:nowrap;
  transition:color var(--duration-fast) var(--ease-out)}
.arey-crumbs a:hover{color:var(--text-primary);opacity:1}
.arey-crumbs__sep{color:var(--border-strong);display:flex}
.arey-crumbs__item--current{color:var(--text-primary)}
`);

/** Ancestry trail. Phosphor caret separator — never a slash character. */
function Breadcrumbs({
  items = [],
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("nav", _extends({
    className: __ds_scope.cx('arey-crumbs', className),
    "aria-label": "Breadcrumb"
  }, rest), items.map(function (it, i) {
    const last = i === items.length - 1;
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: i
    }, i > 0 && /*#__PURE__*/React.createElement("span", {
      className: "arey-crumbs__sep"
    }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
      name: "caret-right",
      size: 12
    })), it.href && !last ? /*#__PURE__*/React.createElement("a", {
      href: it.href
    }, it.label) : /*#__PURE__*/React.createElement("span", {
      className: __ds_scope.cx('arey-crumbs__item', last && 'arey-crumbs__item--current'),
      "aria-current": last ? 'page' : undefined
    }, it.label));
  }));
}
Object.assign(__ds_scope, { Breadcrumbs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Breadcrumbs.jsx", error: String((e && e.message) || e) }); }

// components/navigation/ListRow.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-listrow', `
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
function ListRow({
  icon,
  leading,
  title,
  subtitle,
  value,
  mono = false,
  trailing,
  chevron = false,
  onClick,
  as,
  className,
  ...rest
}) {
  const interactive = !!onClick;
  const Tag = as || (interactive ? 'button' : 'div');
  return /*#__PURE__*/React.createElement(Tag, _extends({
    className: __ds_scope.cx('arey-row', interactive && 'arey-row--interactive', className),
    onClick: onClick,
    type: Tag === 'button' ? 'button' : undefined
  }, rest), leading ? /*#__PURE__*/React.createElement("span", {
    className: "arey-row__lead"
  }, leading) : icon ? /*#__PURE__*/React.createElement("span", {
    className: "arey-row__lead"
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: 17
  })) : null, /*#__PURE__*/React.createElement("span", {
    className: "arey-row__main"
  }, /*#__PURE__*/React.createElement("span", {
    className: "arey-row__title"
  }, title), subtitle && /*#__PURE__*/React.createElement("span", {
    className: "arey-row__sub"
  }, subtitle)), value != null && /*#__PURE__*/React.createElement("span", {
    className: __ds_scope.cx('arey-row__value', mono && 'arey-row__value--mono')
  }, value), trailing, chevron && /*#__PURE__*/React.createElement("span", {
    className: "arey-row__chev"
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "caret-right",
    size: 14
  })));
}

/** Container for ListRows. `inset` gives the iOS grouped-card look. */
function List({
  divided = true,
  inset = false,
  className,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: __ds_scope.cx('arey-list', divided && 'arey-list--divided', inset && 'arey-list--inset', className)
  }, rest), children);
}
Object.assign(__ds_scope, { ListRow, List });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/ListRow.jsx", error: String((e && e.message) || e) }); }

// components/navigation/SegmentedControl.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-segmented', `
.arey-seg{display:inline-grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:2px;padding:2px;
  background:var(--bg-inset);border-radius:var(--radius-control);width:100%}
.arey-seg__item{display:inline-flex;align-items:center;justify-content:center;gap:var(--space-2);
  height:30px;padding:0 var(--space-3);border:0;background:none;border-radius:var(--radius-md);cursor:pointer;
  font:var(--type-label);color:var(--text-secondary);transition:var(--transition-control)}
.arey-seg__item:hover{color:var(--text-primary)}
.arey-seg__item:active{transform:scale(.98)}
.arey-seg__item:focus-visible{outline:none;box-shadow:var(--ring-focus)}
.arey-seg__item[aria-checked="true"]{background:var(--surface-card);color:var(--text-primary);box-shadow:var(--shadow-xs)}
.arey-seg--lg .arey-seg__item{height:38px}
.arey-seg--inline{width:auto;grid-auto-columns:auto}
`);

/** iOS-flavoured 2–4 option switch. Above four options use Select. */
function SegmentedControl({
  options = [],
  value,
  onChange,
  size = 'md',
  inline = false,
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: __ds_scope.cx('arey-seg', size === 'lg' && 'arey-seg--lg', inline && 'arey-seg--inline', className),
    role: "radiogroup"
  }, rest), options.map(function (o) {
    const t = typeof o === 'string' ? {
      value: o,
      label: o
    } : o;
    return /*#__PURE__*/React.createElement("button", {
      key: t.value,
      type: "button",
      role: "radio",
      className: "arey-seg__item",
      "aria-checked": value === t.value,
      onClick: function () {
        if (onChange) onChange(t.value);
      }
    }, t.icon && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
      name: t.icon,
      size: 15,
      weight: value === t.value ? 'fill' : 'regular'
    }), t.label);
  }));
}
Object.assign(__ds_scope, { SegmentedControl });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/SegmentedControl.jsx", error: String((e && e.message) || e) }); }

// components/navigation/SidebarNav.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-sidebarnav', `
.arey-nav{display:grid;gap:var(--space-6);padding:var(--space-4);align-content:start}
.arey-nav__group{display:grid;gap:2px}
.arey-nav__label{font:var(--type-eyebrow);letter-spacing:var(--tracking-eyebrow);text-transform:uppercase;
  color:var(--text-tertiary);padding:0 var(--space-3) var(--space-2)}
.arey-nav__item{display:flex;align-items:center;gap:var(--space-3);height:34px;padding:0 var(--space-3);
  border:0;background:none;border-radius:var(--radius-md);cursor:pointer;width:100%;text-align:left;
  font:var(--type-label);color:var(--text-secondary);transition:var(--transition-control);text-decoration:none}
.arey-nav__item:hover{background:var(--bg-hover);color:var(--text-primary)}
.arey-nav__item:active{background:var(--bg-active)}
.arey-nav__item:focus-visible{outline:none;box-shadow:var(--ring-focus)}
.arey-nav__item[aria-current="page"]{background:var(--bg-selected);color:var(--text-accent)}
.arey-nav__text{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.arey-nav__count{flex:none;font:var(--type-caption);font-family:var(--font-mono);color:var(--text-tertiary)}
.arey-nav__item[aria-current="page"] .arey-nav__count{color:var(--text-accent)}
`);

/** Product sidebar navigation. Active row is an accent wash — never a left border stripe. */
function SidebarNav({
  groups = [],
  value,
  onChange,
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("nav", _extends({
    className: __ds_scope.cx('arey-nav', className)
  }, rest), groups.map(function (g, gi) {
    return /*#__PURE__*/React.createElement("div", {
      className: "arey-nav__group",
      key: gi
    }, g.label && /*#__PURE__*/React.createElement("div", {
      className: "arey-nav__label"
    }, g.label), g.items.map(function (it) {
      const active = value === it.value;
      return /*#__PURE__*/React.createElement("a", {
        key: it.value,
        href: it.href || '#',
        className: "arey-nav__item",
        "aria-current": active ? 'page' : undefined,
        onClick: function (e) {
          if (onChange) {
            e.preventDefault();
            onChange(it.value);
          }
        }
      }, it.icon && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
        name: it.icon,
        size: 16,
        weight: active ? 'fill' : 'regular'
      }), /*#__PURE__*/React.createElement("span", {
        className: "arey-nav__text"
      }, it.label), it.count != null && /*#__PURE__*/React.createElement("span", {
        className: "arey-nav__count"
      }, it.count));
    }));
  }));
}
Object.assign(__ds_scope, { SidebarNav });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/SidebarNav.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Tabs.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
__ds_scope.injectSheet('arey-tabs', `
.arey-tabs{display:flex;align-items:center;gap:var(--space-6);
  border-bottom:1px solid var(--border-subtle)}
.arey-tab{position:relative;display:inline-flex;align-items:center;gap:var(--space-2);
  padding:0 0 var(--space-3);border:0;background:none;cursor:pointer;
  font:var(--type-label);color:var(--text-secondary);transition:color var(--duration-fast) var(--ease-out)}
.arey-tab:hover{color:var(--text-primary)}
.arey-tab:focus-visible{outline:none;box-shadow:var(--ring-focus);border-radius:var(--radius-xs)}
.arey-tab::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:2px;border-radius:2px 2px 0 0;
  background:var(--text-primary);opacity:0;transform:scaleX(.6);
  transition:opacity var(--duration-fast) var(--ease-out),transform var(--duration-normal) var(--ease-out)}
.arey-tab[aria-selected="true"]{color:var(--text-primary)}
.arey-tab[aria-selected="true"]::after{opacity:1;transform:none}
.arey-tab__count{font:var(--type-caption);font-family:var(--font-mono);color:var(--text-tertiary)}
.arey-tabs--pill{border-bottom:0;gap:var(--space-1);padding:3px;background:var(--bg-inset);
  border-radius:var(--radius-control);display:inline-flex}
.arey-tabs--pill .arey-tab{padding:0 var(--space-4);height:30px;border-radius:var(--radius-md)}
.arey-tabs--pill .arey-tab::after{display:none}
.arey-tabs--pill .arey-tab[aria-selected="true"]{background:var(--surface-card);box-shadow:var(--shadow-xs)}
`);

/** Section switcher. Underline by default; pill inside cards and toolbars. */
function Tabs({
  items = [],
  value,
  onChange,
  variant = 'underline',
  className,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: __ds_scope.cx('arey-tabs', variant === 'pill' && 'arey-tabs--pill', className),
    role: "tablist"
  }, rest), items.map(function (it) {
    const t = typeof it === 'string' ? {
      value: it,
      label: it
    } : it;
    return /*#__PURE__*/React.createElement("button", {
      key: t.value,
      type: "button",
      role: "tab",
      className: "arey-tab",
      "aria-selected": value === t.value,
      onClick: function () {
        if (onChange) onChange(t.value);
      }
    }, t.icon && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
      name: t.icon,
      size: 16
    }), t.label, t.count != null && /*#__PURE__*/React.createElement("span", {
      className: "arey-tab__count"
    }, t.count));
  }));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Tabs.jsx", error: String((e && e.message) || e) }); }

// ui_kits/console/App.jsx
try { (() => {
const {
  ToastRegion,
  Toast,
  Button,
  IconButton,
  EmptyState,
  Card
} = window.AreyDesignSystem_1909f9;
function Placeholder({
  page
}) {
  return /*#__PURE__*/React.createElement(Page, null, /*#__PURE__*/React.createElement(PageHead, {
    eyebrow: "arey-web",
    title: page[0].toUpperCase() + page.slice(1)
  }), /*#__PURE__*/React.createElement(Card, {
    variant: "flat",
    padded: false
  }, /*#__PURE__*/React.createElement(EmptyState, {
    icon: "crosshair",
    title: "Not part of this kit",
    description: "This screen was not defined in the source material, so it is intentionally left blank rather than invented."
  })));
}
function App() {
  const [page, setPage] = React.useState('overview');
  const [detail, setDetail] = React.useState(null);
  const [toast, setToast] = React.useState(true);
  const crumbs = [{
    label: 'riya',
    href: '#'
  }, {
    label: 'arey-web',
    href: '#'
  }, {
    label: detail ? detail.sha : page[0].toUpperCase() + page.slice(1)
  }];
  let body;
  if (detail) body = /*#__PURE__*/React.createElement(DeploymentDetail, {
    d: detail,
    onBack: () => setDetail(null)
  });else if (page === 'overview') body = /*#__PURE__*/React.createElement(Overview, {
    onOpenProject: () => setPage('deployments')
  });else if (page === 'deployments') body = /*#__PURE__*/React.createElement(Deployments, {
    onSelect: setDetail
  });else if (page === 'settings') body = /*#__PURE__*/React.createElement(Settings, null);else body = /*#__PURE__*/React.createElement(Placeholder, {
    page: page
  });
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      minHeight: '100vh',
      background: 'var(--bg-canvas)'
    }
  }, /*#__PURE__*/React.createElement(Sidebar, {
    page: page,
    setPage: p => {
      setDetail(null);
      setPage(p);
    }
  }), /*#__PURE__*/React.createElement("main", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(TopBar, {
    crumbs: crumbs,
    actions: /*#__PURE__*/React.createElement(Button, {
      size: "sm",
      variant: "secondary",
      iconLeft: "terminal-window"
    }, "CLI")
  }), body), toast && /*#__PURE__*/React.createElement(ToastRegion, null, /*#__PURE__*/React.createElement(Toast, {
    tone: "success",
    title: "Deployment promoted to production",
    description: "arey-web \xB7 a3f91c8",
    onDismiss: () => setToast(false)
  })));
}
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/React.createElement(App, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/console/App.jsx", error: String((e && e.message) || e) }); }

// ui_kits/console/Deployments.jsx
try { (() => {
const {
  Card,
  Badge,
  Button,
  IconButton,
  Tabs,
  Input,
  Select,
  Tooltip,
  Avatar,
  Dialog,
  Field,
  Icon,
  Kbd,
  EmptyState,
  Spinner
} = window.AreyDesignSystem_1909f9;
function Th({
  children,
  align
}) {
  return /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: align || 'left',
      font: 'var(--type-eyebrow)',
      letterSpacing: 'var(--tracking-eyebrow)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)',
      fontWeight: 'var(--weight-medium)',
      padding: 'var(--space-3) var(--space-4)',
      borderBottom: '1px solid var(--border-subtle)',
      whiteSpace: 'nowrap'
    }
  }, children);
}
function Td({
  children,
  align,
  mono
}) {
  return /*#__PURE__*/React.createElement("td", {
    style: {
      textAlign: align || 'left',
      padding: 'var(--space-3) var(--space-4)',
      borderBottom: '1px solid var(--border-subtle)',
      font: mono ? 'var(--type-code)' : 'var(--type-body)',
      color: 'var(--text-body)',
      whiteSpace: 'nowrap'
    }
  }, children);
}
function DeploymentsTable({
  rows,
  onSelect
}) {
  return /*#__PURE__*/React.createElement("table", {
    style: {
      width: '100%',
      borderCollapse: 'collapse'
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement(Th, null, "Status"), /*#__PURE__*/React.createElement(Th, null, "Deployment"), /*#__PURE__*/React.createElement(Th, null, "Environment"), /*#__PURE__*/React.createElement(Th, null, "Branch"), /*#__PURE__*/React.createElement(Th, null, "Author"), /*#__PURE__*/React.createElement(Th, {
    align: "right"
  }, "Duration"), /*#__PURE__*/React.createElement(Th, {
    align: "right"
  }, "Created"), /*#__PURE__*/React.createElement(Th, null))), /*#__PURE__*/React.createElement("tbody", null, rows.map((d, i) => {
    const s = window.STATUS[d.status];
    return /*#__PURE__*/React.createElement("tr", {
      key: i,
      onClick: () => onSelect(d),
      style: {
        cursor: 'pointer',
        transition: 'background-color var(--duration-fast) var(--ease-out)'
      },
      onMouseEnter: e => {
        e.currentTarget.style.background = 'var(--bg-hover)';
      },
      onMouseLeave: e => {
        e.currentTarget.style.background = 'transparent';
      }
    }, /*#__PURE__*/React.createElement(Td, null, /*#__PURE__*/React.createElement(Badge, {
      tone: s.tone,
      dot: true,
      size: "sm"
    }, s.label)), /*#__PURE__*/React.createElement(Td, null, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'grid',
        gap: 2
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        font: 'var(--type-label)',
        color: 'var(--text-primary)'
      }
    }, d.msg), /*#__PURE__*/React.createElement("span", {
      style: {
        font: 'var(--type-code)',
        fontSize: 'var(--text-11)',
        color: 'var(--text-tertiary)'
      }
    }, d.sha))), /*#__PURE__*/React.createElement(Td, null, /*#__PURE__*/React.createElement(Badge, {
      tone: d.env === 'Production' ? 'accent' : 'outline',
      size: "sm"
    }, d.env)), /*#__PURE__*/React.createElement(Td, {
      mono: true
    }, d.branch), /*#__PURE__*/React.createElement(Td, null, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 8
      }
    }, /*#__PURE__*/React.createElement(Avatar, {
      name: d.author,
      size: "xs"
    }), d.author)), /*#__PURE__*/React.createElement(Td, {
      mono: true,
      align: "right"
    }, d.dur), /*#__PURE__*/React.createElement(Td, {
      align: "right"
    }, /*#__PURE__*/React.createElement(Tooltip, {
      mono: true,
      label: "2026-07-31 14:02 UTC"
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        font: 'var(--type-code)',
        color: 'var(--text-secondary)'
      }
    }, d.time))), /*#__PURE__*/React.createElement(Td, {
      align: "right"
    }, /*#__PURE__*/React.createElement(IconButton, {
      icon: "dots-three",
      label: "Options",
      size: "sm"
    })));
  })));
}
const LOG = [['14:02:11', 'Cloning github.com/riya/arey-web (branch: main, sha: a3f91c8)'], ['14:02:13', 'Restored build cache in 412 ms'], ['14:02:13', 'Running "npm install"'], ['14:02:29', 'added 284 packages in 15 s'], ['14:02:30', 'Running "npm run build"'], ['14:02:52', 'Compiled successfully in 21.4 s'], ['14:02:54', 'Uploading 38 static assets (4.2 MB)'], ['14:02:58', 'Deployment ready — https://arey-web.arey.app']];
function DeploymentDetail({
  d,
  onBack
}) {
  const s = window.STATUS[d.status];
  return /*#__PURE__*/React.createElement(Page, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-3)',
      marginBottom: 'var(--space-6)'
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    size: "sm",
    iconLeft: "arrow-left",
    onClick: onBack
  }, "Deployments")), /*#__PURE__*/React.createElement(PageHead, {
    eyebrow: d.env,
    title: d.msg,
    description: /*#__PURE__*/React.createElement("span", null, "Commit ", /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: 'var(--font-mono)',
        color: 'var(--text-primary)'
      }
    }, d.sha), " on ", /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: 'var(--font-mono)',
        color: 'var(--text-primary)'
      }
    }, d.branch), ", by ", d.author, "."),
    actions: [/*#__PURE__*/React.createElement(Button, {
      key: "1",
      variant: "secondary",
      iconLeft: "arrow-counter-clockwise"
    }, "Redeploy"), /*#__PURE__*/React.createElement(Button, {
      key: "2",
      variant: "primary",
      iconLeft: "arrow-up-right",
      as: "a",
      href: "#"
    }, "Visit")]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 300px',
      gap: 'var(--space-5)',
      alignItems: 'start'
    }
  }, /*#__PURE__*/React.createElement(Card, {
    title: "Build log",
    description: "Retained for 30 days",
    padded: false,
    action: /*#__PURE__*/React.createElement(IconButton, {
      icon: "download-simple",
      label: "Download log",
      size: "sm"
    })
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: '1px solid var(--border-subtle)',
      background: 'var(--bg-inset)',
      padding: 'var(--space-4) var(--space-5)',
      display: 'grid',
      gap: 6,
      borderRadius: '0 0 15px 15px'
    }
  }, LOG.map(([t, l], i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      gap: 'var(--space-4)',
      font: 'var(--type-code)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-tertiary)',
      flex: 'none'
    }
  }, t), /*#__PURE__*/React.createElement("span", {
    style: {
      color: i === LOG.length - 1 ? 'var(--success-text)' : 'var(--text-body)'
    }
  }, l))), d.status === 'building' && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--space-4)',
      alignItems: 'center',
      font: 'var(--type-code)',
      color: 'var(--text-secondary)'
    }
  }, /*#__PURE__*/React.createElement(Spinner, {
    size: 12
  }), " Building\u2026"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-5)'
    }
  }, /*#__PURE__*/React.createElement(Card, {
    title: "Status"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-4)'
    }
  }, [['State', /*#__PURE__*/React.createElement(Badge, {
    tone: s.tone,
    dot: true,
    size: "sm"
  }, s.label)], ['Duration', d.dur], ['Created', d.time], ['Region', 'iad1'], ['Runtime', 'node-20']].map(([k, v]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 'var(--space-4)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: 'var(--type-caption)',
      color: 'var(--text-secondary)'
    }
  }, k), /*#__PURE__*/React.createElement("span", {
    style: {
      font: 'var(--type-code)',
      color: 'var(--text-primary)'
    }
  }, v))))), /*#__PURE__*/React.createElement(Card, {
    variant: "inset"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-eyebrow)',
      letterSpacing: 'var(--tracking-eyebrow)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)'
    }
  }, "Domain"), /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-code)',
      color: 'var(--text-primary)',
      marginTop: 'var(--space-3)',
      wordBreak: 'break-all'
    }
  }, "arey-web.arey.app"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--space-2)',
      marginTop: 'var(--space-4)'
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    iconLeft: "copy"
  }, "Copy"), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    variant: "ghost",
    iconLeft: "arrow-square-out"
  }, "Open"))))));
}
function Deployments({
  onSelect
}) {
  const [tab, setTab] = React.useState('all');
  const [q, setQ] = React.useState('');
  const [showNew, setShowNew] = React.useState(false);
  const rows = window.DEPLOYMENTS.filter(d => tab === 'all' || (tab === 'prod' ? d.env === 'Production' : d.env === 'Preview')).filter(d => d.msg.toLowerCase().includes(q.toLowerCase()) || d.branch.includes(q));
  return /*#__PURE__*/React.createElement(Page, null, /*#__PURE__*/React.createElement(PageHead, {
    eyebrow: "arey-web",
    title: "Deployments",
    description: "Every build for this project, newest first.",
    actions: [/*#__PURE__*/React.createElement(Button, {
      key: "1",
      variant: "secondary",
      iconLeft: "funnel"
    }, "Filters"), /*#__PURE__*/React.createElement(Button, {
      key: "2",
      variant: "primary",
      iconLeft: "plus",
      onClick: () => setShowNew(true)
    }, "New deployment")]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-4)',
      marginBottom: 'var(--space-5)'
    }
  }, /*#__PURE__*/React.createElement(Tabs, {
    value: tab,
    onChange: setTab,
    items: [{
      value: 'all',
      label: 'All',
      count: window.DEPLOYMENTS.length
    }, {
      value: 'prod',
      label: 'Production'
    }, {
      value: 'preview',
      label: 'Preview'
    }]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 260
    }
  }, /*#__PURE__*/React.createElement(Input, {
    size: "sm",
    icon: "magnifying-glass",
    placeholder: "Search deployments",
    value: q,
    onChange: e => setQ(e.target.value)
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 150
    }
  }, /*#__PURE__*/React.createElement(Select, {
    size: "sm",
    options: ['All branches', 'main', 'feat/usage']
  }))), /*#__PURE__*/React.createElement(Card, {
    padded: false,
    variant: "flat"
  }, rows.length ? /*#__PURE__*/React.createElement(DeploymentsTable, {
    rows: rows,
    onSelect: onSelect
  }) : /*#__PURE__*/React.createElement(EmptyState, {
    compact: true,
    icon: "magnifying-glass",
    title: "No deployments match",
    description: "Try a different branch or search term.",
    action: /*#__PURE__*/React.createElement(Button, {
      onClick: () => setQ('')
    }, "Clear search")
  })), /*#__PURE__*/React.createElement(Dialog, {
    open: showNew,
    onClose: () => setShowNew(false),
    title: "New deployment",
    description: "Deploy the current head of a branch to a preview URL.",
    footer: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Button, {
      onClick: () => setShowNew(false)
    }, "Cancel"), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      onClick: () => setShowNew(false)
    }, "Deploy"))
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-5)'
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Branch"
  }, /*#__PURE__*/React.createElement(Select, {
    options: ['main', 'feat/usage', 'fix/focus']
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Commit",
    hint: "Leave empty to use the branch head"
  }, /*#__PURE__*/React.createElement(Input, {
    mono: true,
    placeholder: "a3f91c8"
  })))));
}
Object.assign(window, {
  Deployments,
  DeploymentDetail,
  DeploymentsTable,
  Th,
  Td
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/console/Deployments.jsx", error: String((e && e.message) || e) }); }

// ui_kits/console/Overview.jsx
try { (() => {
const {
  Card,
  Badge,
  Button,
  IconButton,
  Tag,
  Avatar,
  AvatarStack,
  ProgressBar,
  SegmentedControl,
  Tooltip,
  EmptyState,
  Icon
} = window.AreyDesignSystem_1909f9;
function MetricCard({
  label,
  value,
  unit,
  delta,
  sub,
  children
}) {
  return /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-eyebrow)',
      letterSpacing: 'var(--tracking-eyebrow)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)'
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 8,
      marginTop: 'var(--space-3)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: 'var(--weight-semibold) var(--text-36)/1 var(--font-sans)',
      letterSpacing: 'var(--tracking-heading)',
      color: 'var(--text-primary)'
    }
  }, value), unit && /*#__PURE__*/React.createElement("span", {
    style: {
      font: 'var(--type-body)',
      fontFamily: 'var(--font-mono)',
      color: 'var(--text-tertiary)'
    }
  }, unit), delta && /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      font: 'var(--type-caption)',
      fontFamily: 'var(--font-mono)',
      color: delta[0] === '-' ? 'var(--danger-text)' : 'var(--success-text)'
    }
  }, delta)), sub && /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-caption)',
      color: 'var(--text-secondary)',
      marginTop: 'var(--space-2)'
    }
  }, sub), children && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 'var(--space-4)'
    }
  }, children));
}
function Sparkline({
  points,
  tone = 'var(--accent-solid)'
}) {
  const max = Math.max(...points);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-end',
      gap: 3,
      height: 44
    }
  }, points.map((p, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      flex: 1,
      height: Math.max(3, p / max * 44),
      background: i === points.length - 1 ? tone : 'var(--bg-inset)',
      borderRadius: 2,
      transition: 'height var(--duration-slow) var(--ease-out)'
    }
  })));
}
function ProjectCard({
  p,
  onOpen
}) {
  const s = window.STATUS[p.status];
  return /*#__PURE__*/React.createElement(Card, {
    interactive: true,
    onClick: onOpen,
    padded: false,
    style: {
      display: 'grid'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 'var(--space-5)',
      display: 'grid',
      gap: 'var(--space-4)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-3)'
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    name: p.name.replace('arey-', ''),
    square: true,
    tone: "accent"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-title-3)',
      letterSpacing: 'var(--tracking-heading)',
      color: 'var(--text-primary)'
    }
  }, p.name), /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-caption)',
      color: 'var(--text-tertiary)',
      fontFamily: 'var(--font-mono)'
    }
  }, p.name, ".arey.app")), /*#__PURE__*/React.createElement(Badge, {
    tone: s.tone,
    dot: true,
    size: "sm"
  }, s.label)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-3)',
      font: 'var(--type-caption)',
      color: 'var(--text-secondary)'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "git-branch",
    size: 13
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)'
    }
  }, p.branch), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--border-strong)'
    }
  }, "\xB7"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)'
    }
  }, p.sha), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      fontFamily: 'var(--font-mono)'
    }
  }, p.time))));
}
function Overview({
  onOpenProject
}) {
  const [range, setRange] = React.useState('7d');
  return /*#__PURE__*/React.createElement(Page, null, /*#__PURE__*/React.createElement(PageHead, {
    eyebrow: "Team riya",
    title: "Overview",
    description: "Six projects, four members. Everything is deploying from main.",
    actions: [/*#__PURE__*/React.createElement(Button, {
      key: "a",
      variant: "secondary",
      iconLeft: "arrow-square-out"
    }, "Visit site"), /*#__PURE__*/React.createElement(Button, {
      key: "b",
      variant: "primary",
      iconLeft: "plus"
    }, "New project")]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-4)',
      marginBottom: 'var(--space-5)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-title-3)',
      letterSpacing: 'var(--tracking-heading)',
      color: 'var(--text-primary)'
    }
  }, "Usage"), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 220,
      marginLeft: 'auto'
    }
  }, /*#__PURE__*/React.createElement(SegmentedControl, {
    value: range,
    onChange: setRange,
    options: [{
      value: '24h',
      label: 'Day'
    }, {
      value: '7d',
      label: 'Week'
    }, {
      value: '30d',
      label: 'Month'
    }]
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
      gap: 'var(--space-5)',
      marginBottom: 'var(--space-12)'
    }
  }, /*#__PURE__*/React.createElement(MetricCard, {
    label: "Bandwidth",
    value: "412",
    unit: "GB",
    delta: "+8.2 %",
    sub: "of 1 TB included"
  }, /*#__PURE__*/React.createElement(ProgressBar, {
    value: 41
  })), /*#__PURE__*/React.createElement(MetricCard, {
    label: "Requests",
    value: "2.4",
    unit: "M",
    delta: "+12.6 %",
    sub: "Edge and function calls"
  }, /*#__PURE__*/React.createElement(Sparkline, {
    points: [12, 18, 14, 22, 26, 21, 34]
  })), /*#__PURE__*/React.createElement(MetricCard, {
    label: "p95 latency",
    value: "184",
    unit: "ms",
    delta: "-6.1 %",
    sub: "Across 18 regions"
  }, /*#__PURE__*/React.createElement(Sparkline, {
    points: [30, 28, 32, 24, 22, 20, 18],
    tone: "var(--success-solid)"
  })), /*#__PURE__*/React.createElement(MetricCard, {
    label: "Build minutes",
    value: "1 240",
    unit: "min",
    delta: "+3.4 %",
    sub: "94 % of the monthly limit"
  }, /*#__PURE__*/React.createElement(ProgressBar, {
    value: 94,
    tone: "warning"
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-3)',
      marginBottom: 'var(--space-5)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-title-3)',
      letterSpacing: 'var(--tracking-heading)',
      color: 'var(--text-primary)'
    }
  }, "Projects"), /*#__PURE__*/React.createElement(Badge, {
    mono: true,
    size: "sm"
  }, "6"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginLeft: 'auto',
      display: 'flex',
      gap: 'var(--space-2)'
    }
  }, /*#__PURE__*/React.createElement(Tag, {
    icon: "funnel",
    onClick: () => {},
    selected: true
  }, "Production"), /*#__PURE__*/React.createElement(Tag, {
    onClick: () => {}
  }, "All branches"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
      gap: 'var(--space-5)'
    }
  }, window.PROJECTS.map(p => /*#__PURE__*/React.createElement(ProjectCard, {
    key: p.name,
    p: p,
    onOpen: onOpenProject
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
      gap: 'var(--space-5)',
      marginTop: 'var(--space-12)'
    }
  }, /*#__PURE__*/React.createElement(Card, {
    title: "Activity",
    description: "Last 24 hours",
    padded: false,
    action: /*#__PURE__*/React.createElement(Button, {
      variant: "link"
    }, "View all")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid'
    }
  }, window.DEPLOYMENTS.slice(0, 4).map((d, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-3)',
      padding: 'var(--space-4) var(--space-6)',
      borderTop: '1px solid var(--border-subtle)'
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    name: d.author,
    size: "sm"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-label)',
      color: 'var(--text-primary)',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, d.msg), /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-caption)',
      color: 'var(--text-secondary)'
    }
  }, d.author, " pushed to ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)'
    }
  }, d.branch))), /*#__PURE__*/React.createElement(Tooltip, {
    mono: true,
    label: "2026-07-31 14:02 UTC"
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: 'var(--type-code)',
      color: 'var(--text-tertiary)'
    }
  }, d.time)))))), /*#__PURE__*/React.createElement(Card, {
    title: "Members",
    action: /*#__PURE__*/React.createElement(Button, {
      variant: "link"
    }, "Invite"),
    padded: false
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid'
    }
  }, window.MEMBERS.map(m => /*#__PURE__*/React.createElement("div", {
    key: m.email,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-3)',
      padding: 'var(--space-3) var(--space-6)',
      borderTop: '1px solid var(--border-subtle)'
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    name: m.name,
    size: "sm"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-label)',
      color: 'var(--text-primary)'
    }
  }, m.name), /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-caption)',
      color: 'var(--text-tertiary)',
      fontFamily: 'var(--font-mono)'
    }
  }, m.email)), /*#__PURE__*/React.createElement(Badge, {
    tone: m.role === 'Owner' ? 'accent' : 'outline',
    size: "sm"
  }, m.role)))))));
}
Object.assign(window, {
  Overview,
  MetricCard,
  Sparkline
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/console/Overview.jsx", error: String((e && e.message) || e) }); }

// ui_kits/console/Settings.jsx
try { (() => {
const {
  Card,
  Button,
  IconButton,
  Field,
  Input,
  Textarea,
  Select,
  Switch,
  Checkbox,
  RadioGroup,
  List,
  ListRow,
  Badge,
  Avatar,
  Dialog,
  SegmentedControl,
  Tabs,
  Kbd,
  Tag
} = window.AreyDesignSystem_1909f9;
function Section({
  title,
  description,
  children,
  footer,
  danger
}) {
  return /*#__PURE__*/React.createElement(Card, {
    title: title,
    description: description,
    footer: footer,
    style: danger ? {
      borderColor: 'var(--danger-solid)'
    } : undefined
  }, children);
}
function Settings() {
  const [tab, setTab] = React.useState('general');
  const [theme, setTheme] = React.useState('system');
  const [confirm, setConfirm] = React.useState(false);
  const [vis, setVis] = React.useState('private');
  return /*#__PURE__*/React.createElement(Page, null, /*#__PURE__*/React.createElement(PageHead, {
    eyebrow: "arey-web",
    title: "Settings",
    description: "Project configuration. Changes apply to the next deployment."
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 'var(--space-8)'
    }
  }, /*#__PURE__*/React.createElement(Tabs, {
    value: tab,
    onChange: setTab,
    items: [{
      value: 'general',
      label: 'General'
    }, {
      value: 'env',
      label: 'Environment',
      count: 6
    }, {
      value: 'members',
      label: 'Members',
      count: 4
    }, {
      value: 'advanced',
      label: 'Advanced',
      icon: 'sliders-horizontal'
    }]
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-6)'
    }
  }, /*#__PURE__*/React.createElement(Section, {
    title: "Project",
    description: "Names and identifiers other people see.",
    footer: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
      style: {
        font: 'var(--type-caption)',
        color: 'var(--text-secondary)',
        marginRight: 'auto'
      }
    }, "Renaming does not change existing deployment URLs."), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      size: "sm"
    }, "Save"))
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-6)'
    }
  }, /*#__PURE__*/React.createElement(Field, {
    layout: "row",
    label: "Project name",
    hint: "Lowercase letters, numbers and dashes",
    htmlFor: "pn"
  }, /*#__PURE__*/React.createElement(Input, {
    id: "pn",
    defaultValue: "arey-web"
  })), /*#__PURE__*/React.createElement(Field, {
    layout: "row",
    label: "Production branch",
    hint: "Pushes here deploy to production"
  }, /*#__PURE__*/React.createElement(Select, {
    options: ['main', 'release/4.2']
  })), /*#__PURE__*/React.createElement(Field, {
    layout: "row",
    label: "Description",
    optional: true
  }, /*#__PURE__*/React.createElement(Textarea, {
    rows: 3,
    defaultValue: "Marketing site and console shell for arey."
  })), /*#__PURE__*/React.createElement(Field, {
    layout: "row",
    label: "Visibility"
  }, /*#__PURE__*/React.createElement(RadioGroup, {
    name: "vis",
    value: vis,
    onChange: setVis,
    options: [{
      value: 'private',
      label: 'Private',
      description: 'Only members can view deployments'
    }, {
      value: 'public',
      label: 'Public',
      description: 'Anyone with the link can view'
    }]
  })))), /*#__PURE__*/React.createElement(Section, {
    title: "Build & deploy",
    description: "How arey builds this project."
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-5)'
    }
  }, /*#__PURE__*/React.createElement(List, null, /*#__PURE__*/React.createElement(ListRow, {
    icon: "lightning",
    title: "Automatic deployments",
    subtitle: "Deploy every push to a tracked branch",
    trailing: /*#__PURE__*/React.createElement(Switch, {
      defaultChecked: true,
      "aria-label": "Automatic deployments"
    })
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "chat-circle-dots",
    title: "Preview comments",
    subtitle: "Let reviewers comment on preview URLs",
    trailing: /*#__PURE__*/React.createElement(Switch, {
      tone: "accent",
      defaultChecked: true,
      "aria-label": "Preview comments"
    })
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "shield-check",
    title: "Protect production",
    subtitle: "Require a review before promoting",
    trailing: /*#__PURE__*/React.createElement(Switch, {
      "aria-label": "Protect production"
    })
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 'var(--space-5)'
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Install command"
  }, /*#__PURE__*/React.createElement(Input, {
    mono: true,
    defaultValue: "npm install"
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Build command"
  }, /*#__PURE__*/React.createElement(Input, {
    mono: true,
    defaultValue: "npm run build"
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Output directory"
  }, /*#__PURE__*/React.createElement(Input, {
    mono: true,
    defaultValue: ".arey/output"
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Node version"
  }, /*#__PURE__*/React.createElement(Select, {
    options: ['node-20', 'node-18']
  }))))), /*#__PURE__*/React.createElement(Section, {
    title: "Appearance",
    description: "Applies to your account across every project."
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-5)',
      maxWidth: 420
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Theme"
  }, /*#__PURE__*/React.createElement(SegmentedControl, {
    value: theme,
    onChange: setTheme,
    options: [{
      value: 'light',
      label: 'Light',
      icon: 'sun'
    }, {
      value: 'dark',
      label: 'Dark',
      icon: 'moon'
    }, {
      value: 'system',
      label: 'System',
      icon: 'desktop'
    }]
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Density",
    hint: "arey defaults to the roomy scale"
  }, /*#__PURE__*/React.createElement(SegmentedControl, {
    value: "roomy",
    onChange: () => {},
    options: [{
      value: 'roomy',
      label: 'Roomy'
    }, {
      value: 'compact',
      label: 'Compact'
    }]
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-3)'
    }
  }, /*#__PURE__*/React.createElement(Checkbox, {
    label: "Show relative timestamps",
    defaultChecked: true,
    description: "Absolute times still appear on hover"
  }), /*#__PURE__*/React.createElement(Checkbox, {
    label: "Reduce motion"
  })))), /*#__PURE__*/React.createElement(Section, {
    title: "API keys",
    description: "Server-side keys. Rotating a key invalidates it immediately.",
    padded: true
  }, /*#__PURE__*/React.createElement(List, {
    inset: true
  }, /*#__PURE__*/React.createElement(ListRow, {
    icon: "key",
    title: "Production",
    value: "sk_live_9f2a7c41e8",
    mono: true,
    trailing: /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        gap: 4
      }
    }, /*#__PURE__*/React.createElement(IconButton, {
      icon: "copy",
      label: "Copy key",
      size: "sm"
    }), /*#__PURE__*/React.createElement(IconButton, {
      icon: "arrows-clockwise",
      label: "Rotate key",
      size: "sm"
    }))
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "key",
    title: "Preview",
    value: "sk_test_41b8e2c04d",
    mono: true,
    trailing: /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        gap: 4
      }
    }, /*#__PURE__*/React.createElement(IconButton, {
      icon: "copy",
      label: "Copy key",
      size: "sm"
    }), /*#__PURE__*/React.createElement(IconButton, {
      icon: "arrows-clockwise",
      label: "Rotate key",
      size: "sm"
    }))
  }))), /*#__PURE__*/React.createElement(Section, {
    title: "Delete project",
    description: "This removes all deployments, domains and logs. It cannot be undone.",
    footer: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
      style: {
        marginRight: 'auto'
      }
    }), /*#__PURE__*/React.createElement(Button, {
      variant: "danger",
      size: "sm",
      onClick: () => setConfirm(true)
    }, "Delete project"))
  })), /*#__PURE__*/React.createElement(Dialog, {
    open: confirm,
    onClose: () => setConfirm(false),
    title: "Delete arey-web",
    description: "This removes 24 deployments, 2 domains and all logs. It cannot be undone.",
    footer: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Button, {
      onClick: () => setConfirm(false)
    }, "Cancel"), /*#__PURE__*/React.createElement(Button, {
      variant: "danger",
      onClick: () => setConfirm(false)
    }, "Delete project"))
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Type the project name to confirm"
  }, /*#__PURE__*/React.createElement(Input, {
    placeholder: "arey-web"
  }))));
}
Object.assign(window, {
  Settings
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/console/Settings.jsx", error: String((e && e.message) || e) }); }

// ui_kits/console/Shell.jsx
try { (() => {
const {
  SidebarNav,
  IconButton,
  Breadcrumbs,
  Avatar,
  Badge,
  Kbd,
  Input,
  Button,
  Icon,
  ProgressBar
} = window.AreyDesignSystem_1909f9;
function ThemeToggle() {
  const [dark, setDark] = React.useState(document.documentElement.getAttribute('data-theme') === 'dark');
  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  }, [dark]);
  return /*#__PURE__*/React.createElement(IconButton, {
    icon: dark ? 'sun' : 'moon',
    label: "Toggle theme",
    onClick: () => setDark(!dark)
  });
}
function Sidebar({
  page,
  setPage
}) {
  return /*#__PURE__*/React.createElement("aside", {
    style: {
      width: 'var(--sidebar-w)',
      flex: 'none',
      borderRight: '1px solid var(--border-subtle)',
      background: 'var(--bg-base)',
      display: 'flex',
      flexDirection: 'column',
      position: 'sticky',
      top: 0,
      height: '100vh'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 'var(--topbar-h)',
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '0 var(--space-4)',
      borderBottom: '1px solid var(--border-subtle)'
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logo-mark.svg",
    style: {
      height: 20,
      color: 'var(--text-primary)'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      font: 'var(--weight-semibold) 15px var(--font-sans)',
      letterSpacing: '-.03em',
      color: 'var(--text-primary)'
    }
  }, "arey"), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 1,
      height: 14,
      background: 'var(--border-default)'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      font: 'var(--type-label)',
      color: 'var(--text-secondary)'
    }
  }, "Console")), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 'var(--space-4) var(--space-4) 0'
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      width: '100%',
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: 'var(--space-2) var(--space-3)',
      background: 'var(--bg-subtle)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-control)',
      cursor: 'pointer',
      textAlign: 'left'
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    name: "Riya Menon",
    size: "sm"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      font: 'var(--type-label)',
      color: 'var(--text-primary)'
    }
  }, "riya"), /*#__PURE__*/React.createElement(Icon, {
    name: "caret-up-down",
    size: 13,
    color: "var(--text-tertiary)"
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflow: 'auto',
      maskImage: 'linear-gradient(to bottom, #000 calc(100% - 24px), transparent)'
    }
  }, /*#__PURE__*/React.createElement(SidebarNav, {
    value: page,
    onChange: setPage,
    groups: [{
      items: [{
        value: 'overview',
        label: 'Overview',
        icon: 'squares-four'
      }, {
        value: 'deployments',
        label: 'Deployments',
        icon: 'rocket-launch',
        count: 24
      }, {
        value: 'analytics',
        label: 'Analytics',
        icon: 'chart-line'
      }, {
        value: 'logs',
        label: 'Logs',
        icon: 'terminal-window'
      }]
    }, {
      label: 'Project',
      items: [{
        value: 'domains',
        label: 'Domains',
        icon: 'globe-hemisphere-west'
      }, {
        value: 'storage',
        label: 'Storage',
        icon: 'database'
      }, {
        value: 'env',
        label: 'Environment',
        icon: 'sliders-horizontal'
      }]
    }, {
      label: 'Team',
      items: [{
        value: 'members',
        label: 'Members',
        icon: 'users-three',
        count: 4
      }, {
        value: 'usage',
        label: 'Usage',
        icon: 'gauge'
      }, {
        value: 'settings',
        label: 'Settings',
        icon: 'gear-six'
      }]
    }]
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 'var(--space-4)',
      borderTop: '1px solid var(--border-subtle)',
      display: 'grid',
      gap: 'var(--space-2)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      font: 'var(--type-caption)',
      color: 'var(--text-secondary)'
    }
  }, /*#__PURE__*/React.createElement("span", null, "Hobby plan"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)'
    }
  }, "68 %")), /*#__PURE__*/React.createElement(ProgressBar, {
    value: 68
  }), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    variant: "secondary",
    block: true,
    iconLeft: "lightning"
  }, "Upgrade")));
}
function TopBar({
  crumbs,
  actions
}) {
  return /*#__PURE__*/React.createElement("header", {
    style: {
      position: 'sticky',
      top: 0,
      zIndex: 30,
      height: 'var(--topbar-h)',
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-4)',
      padding: '0 var(--space-8)',
      background: 'var(--surface-glass)',
      backdropFilter: 'var(--backdrop-glass)',
      WebkitBackdropFilter: 'var(--backdrop-glass)',
      borderBottom: '1px solid var(--border-subtle)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: '0 0 auto'
    }
  }, /*#__PURE__*/React.createElement(Breadcrumbs, {
    items: crumbs
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 'var(--space-4)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 240,
      minWidth: 120,
      flexShrink: 1
    }
  }, /*#__PURE__*/React.createElement(Input, {
    size: "sm",
    icon: "magnifying-glass",
    placeholder: "Search",
    suffix: /*#__PURE__*/React.createElement(Kbd, {
      keys: "cmd+k"
    })
  })), actions, /*#__PURE__*/React.createElement(ThemeToggle, null), /*#__PURE__*/React.createElement(IconButton, {
    icon: "bell",
    label: "Notifications"
  }), /*#__PURE__*/React.createElement(Avatar, {
    name: "Riya Menon",
    size: "sm"
  }));
}
function PageHead({
  eyebrow,
  title,
  description,
  actions
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-end',
      gap: 'var(--space-6)',
      marginBottom: 'var(--space-8)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, eyebrow && /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-eyebrow)',
      letterSpacing: 'var(--tracking-eyebrow)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)',
      marginBottom: 'var(--space-3)'
    }
  }, eyebrow), /*#__PURE__*/React.createElement("h1", {
    style: {
      font: 'var(--type-title-1)',
      letterSpacing: 'var(--tracking-heading)'
    }
  }, title), description && /*#__PURE__*/React.createElement("p", {
    style: {
      font: 'var(--type-body-lg)',
      color: 'var(--text-secondary)',
      marginTop: 'var(--space-2)',
      maxWidth: '60ch'
    }
  }, description)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--space-3)',
      flex: 'none'
    }
  }, actions));
}
function Page({
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 'var(--content-max)',
      margin: '0 auto',
      padding: 'var(--space-12) var(--space-8) var(--space-20)'
    }
  }, children);
}
function StatusDot({
  status
}) {
  const map = {
    ready: 'var(--success-solid)',
    building: 'var(--warning-solid)',
    failed: 'var(--danger-solid)',
    queued: 'var(--grey-400)'
  };
  return /*#__PURE__*/React.createElement("span", {
    style: {
      width: 7,
      height: 7,
      borderRadius: 9,
      background: map[status],
      flex: 'none',
      boxShadow: status === 'building' ? '0 0 0 3px var(--warning-wash)' : undefined
    }
  });
}
Object.assign(window, {
  Sidebar,
  TopBar,
  PageHead,
  Page,
  StatusDot,
  ThemeToggle
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/console/Shell.jsx", error: String((e && e.message) || e) }); }

// ui_kits/console/data.jsx
try { (() => {
const PROJECTS = [{
  name: 'arey-web',
  framework: 'Next.js',
  branch: 'main',
  status: 'ready',
  time: '3 m ago',
  dur: '48 s',
  sha: 'a3f91c8',
  author: 'Riya Menon'
}, {
  name: 'arey-docs',
  framework: 'Astro',
  branch: 'main',
  status: 'building',
  time: '6 m ago',
  dur: '—',
  sha: '7c02be1',
  author: 'Dev Kapoor'
}, {
  name: 'arey-api',
  framework: 'Node',
  branch: 'main',
  status: 'ready',
  time: '1 h ago',
  dur: '1 m 12 s',
  sha: 'f18d4aa',
  author: 'Sam Ito'
}, {
  name: 'arey-mobile',
  framework: 'Expo',
  branch: 'release/4.2',
  status: 'failed',
  time: '2 h ago',
  dur: '22 s',
  sha: '9b7e330',
  author: 'Lea Fischer'
}, {
  name: 'arey-design',
  framework: 'Vite',
  branch: 'main',
  status: 'ready',
  time: '5 h ago',
  dur: '31 s',
  sha: '2d5c917',
  author: 'Riya Menon'
}, {
  name: 'arey-status',
  framework: 'Static',
  branch: 'main',
  status: 'queued',
  time: '5 h ago',
  dur: '—',
  sha: '55a1f0d',
  author: 'Nils Berg'
}];
const DEPLOYMENTS = [{
  env: 'Production',
  status: 'ready',
  sha: 'a3f91c8',
  msg: 'Tighten card shadow on dark surfaces',
  branch: 'main',
  author: 'Riya Menon',
  dur: '48 s',
  time: '3 m ago'
}, {
  env: 'Preview',
  status: 'building',
  sha: '7c02be1',
  msg: 'Add usage meter to overview',
  branch: 'feat/usage',
  author: 'Dev Kapoor',
  dur: '—',
  time: '6 m ago'
}, {
  env: 'Preview',
  status: 'ready',
  sha: 'f18d4aa',
  msg: 'Move eyebrow labels to mono',
  branch: 'feat/type',
  author: 'Sam Ito',
  dur: '1 m 12 s',
  time: '1 h ago'
}, {
  env: 'Preview',
  status: 'failed',
  sha: '9b7e330',
  msg: 'Bump build image to node-20',
  branch: 'chore/node',
  author: 'Lea Fischer',
  dur: '22 s',
  time: '2 h ago'
}, {
  env: 'Production',
  status: 'ready',
  sha: '2d5c917',
  msg: 'Ship segmented control',
  branch: 'main',
  author: 'Riya Menon',
  dur: '31 s',
  time: '5 h ago'
}, {
  env: 'Preview',
  status: 'ready',
  sha: '55a1f0d',
  msg: 'Docs: deployment lifecycle',
  branch: 'docs/lifecycle',
  author: 'Nils Berg',
  dur: '39 s',
  time: '8 h ago'
}, {
  env: 'Preview',
  status: 'ready',
  sha: 'c41b8e2',
  msg: 'Fix focus ring offset in Safari',
  branch: 'fix/focus',
  author: 'Dev Kapoor',
  dur: '44 s',
  time: '1 d ago'
}];
const STATUS = {
  ready: {
    tone: 'success',
    label: 'Ready'
  },
  building: {
    tone: 'warning',
    label: 'Building'
  },
  failed: {
    tone: 'danger',
    label: 'Failed'
  },
  queued: {
    tone: 'neutral',
    label: 'Queued'
  }
};
const MEMBERS = [{
  name: 'Riya Menon',
  email: 'riya@arey.dev',
  role: 'Owner'
}, {
  name: 'Dev Kapoor',
  email: 'dev@arey.dev',
  role: 'Member'
}, {
  name: 'Sam Ito',
  email: 'sam@arey.dev',
  role: 'Member'
}, {
  name: 'Lea Fischer',
  email: 'lea@arey.dev',
  role: 'Viewer'
}];
Object.assign(window, {
  PROJECTS,
  DEPLOYMENTS,
  STATUS,
  MEMBERS
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/console/data.jsx", error: String((e && e.message) || e) }); }

// ui_kits/docs/DocsApp.jsx
try { (() => {
const {
  SidebarNav,
  Button,
  Badge,
  Icon,
  Card,
  Kbd,
  SegmentedControl,
  Tabs
} = window.AreyDesignSystem_1909f9;
const TOC = [{
  id: 'install',
  label: 'Install the CLI'
}, {
  id: 'link',
  label: 'Link a project'
}, {
  id: 'deploy',
  label: 'Your first deployment'
}, {
  id: 'env',
  label: 'Environment variables'
}, {
  id: 'props',
  label: 'Command reference'
}];
function DocsApp() {
  const [page, setPage] = React.useState('quickstart');
  const [active, setActive] = React.useState('install');
  const [pkg, setPkg] = React.useState('npm');
  const install = {
    npm: 'npm i -g arey',
    pnpm: 'pnpm add -g arey',
    brew: 'brew install arey'
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--bg-base)',
      minHeight: '100vh'
    }
  }, /*#__PURE__*/React.createElement(DocsHeader, null), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--space-10)',
      maxWidth: 1440,
      margin: '0 auto',
      padding: '0 var(--space-8)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 240,
      flex: 'none',
      position: 'sticky',
      top: 'var(--topbar-h)',
      height: 'calc(100vh - var(--topbar-h))',
      overflow: 'auto',
      borderRight: '1px solid var(--border-subtle)',
      marginLeft: 'calc(var(--space-8) * -1)',
      paddingLeft: 'var(--space-4)'
    }
  }, /*#__PURE__*/React.createElement(SidebarNav, {
    value: page,
    onChange: setPage,
    groups: [{
      label: 'Getting started',
      items: [{
        value: 'introduction',
        label: 'Introduction'
      }, {
        value: 'quickstart',
        label: 'Quickstart'
      }, {
        value: 'projects',
        label: 'Projects'
      }]
    }, {
      label: 'Deploying',
      items: [{
        value: 'builds',
        label: 'Builds'
      }, {
        value: 'environments',
        label: 'Environments'
      }, {
        value: 'domains',
        label: 'Domains'
      }, {
        value: 'rollbacks',
        label: 'Rollbacks'
      }]
    }, {
      label: 'Reference',
      items: [{
        value: 'cli',
        label: 'CLI'
      }, {
        value: 'config',
        label: 'arey.json'
      }, {
        value: 'api',
        label: 'REST API'
      }]
    }]
  })), /*#__PURE__*/React.createElement("main", {
    style: {
      flex: 1,
      minWidth: 0,
      padding: 'var(--space-10) 0 var(--space-24)'
    },
    className: "prose"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-eyebrow)',
      letterSpacing: 'var(--tracking-eyebrow)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)',
      marginBottom: 'var(--space-4)'
    }
  }, "Getting started"), /*#__PURE__*/React.createElement("h1", {
    style: {
      font: 'var(--type-title-1)',
      letterSpacing: 'var(--tracking-heading)',
      margin: 0
    }
  }, "Quickstart"), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: 'var(--space-4)',
      color: 'var(--text-secondary)'
    }
  }, "Install the CLI, link a project, and ship it. This takes about four minutes."), /*#__PURE__*/React.createElement("h2", {
    id: "install"
  }, "Install the CLI"), /*#__PURE__*/React.createElement("p", null, "The CLI is the fastest way to deploy. It works on macOS, Linux and Windows."), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 300,
      margin: '0 0 var(--space-4)'
    }
  }, /*#__PURE__*/React.createElement(SegmentedControl, {
    value: pkg,
    onChange: setPkg,
    options: [{
      value: 'npm',
      label: 'npm'
    }, {
      value: 'pnpm',
      label: 'pnpm'
    }, {
      value: 'brew',
      label: 'brew'
    }]
  })), /*#__PURE__*/React.createElement(CodeBlock, {
    lines: ['$ ' + install[pkg], '$ arey --version', 'arey/4.2.0 darwin-arm64 node-20.11.1']
  }), /*#__PURE__*/React.createElement(Callout, {
    tone: "note",
    title: "Node 18 or newer"
  }, "The CLI needs Node 18+. Check with ", /*#__PURE__*/React.createElement("code", null, "node --version"), " before installing."), /*#__PURE__*/React.createElement("h2", {
    id: "link"
  }, "Link a project"), /*#__PURE__*/React.createElement("p", null, "Run ", /*#__PURE__*/React.createElement("code", null, "arey link"), " inside your repository. The CLI writes a ", /*#__PURE__*/React.createElement("code", null, ".arey"), " directory holding the project id \u2014 commit it so your team shares the same link."), /*#__PURE__*/React.createElement(CodeBlock, {
    lines: ['$ arey link', '? Link to existing project? yes', '? Which project? arey-web', 'Linked to riya/arey-web (created .arey)']
  }), /*#__PURE__*/React.createElement("h2", {
    id: "deploy"
  }, "Your first deployment"), /*#__PURE__*/React.createElement("p", null, "Deployments are immutable. Every build gets its own URL, and promoting to production only changes which build the production domain points at."), /*#__PURE__*/React.createElement(CodeBlock, {
    lines: ['$ arey deploy', 'Uploading 38 files (4.2 MB)', 'Building in iad1 · node-20', 'Ready — https://arey-web-9f2a.arey.app  48 s']
  }), /*#__PURE__*/React.createElement("ul", null, /*#__PURE__*/React.createElement("li", null, /*#__PURE__*/React.createElement("strong", null, "Preview"), " \u2014 every push to a non-production branch."), /*#__PURE__*/React.createElement("li", null, /*#__PURE__*/React.createElement("strong", null, "Production"), " \u2014 pushes to ", /*#__PURE__*/React.createElement("code", null, "main"), ", or ", /*#__PURE__*/React.createElement("code", null, "arey deploy --prod"), "."), /*#__PURE__*/React.createElement("li", null, /*#__PURE__*/React.createElement("strong", null, "Rollback"), " \u2014 promote any previous build; no rebuild happens.")), /*#__PURE__*/React.createElement(Callout, {
    tone: "warning",
    title: "Production deploys skip the queue"
  }, "A ", /*#__PURE__*/React.createElement("code", null, "--prod"), " deploy is promoted the moment it is ready. Enable ", /*#__PURE__*/React.createElement("strong", null, "Protect production"), " in project settings to require a review first."), /*#__PURE__*/React.createElement("h2", {
    id: "env"
  }, "Environment variables"), /*#__PURE__*/React.createElement("p", null, "Variables are scoped per environment and encrypted at rest. Pull them locally with ", /*#__PURE__*/React.createElement("code", null, "arey env pull"), "."), /*#__PURE__*/React.createElement(CodeBlock, {
    filename: ".env.local",
    lines: ['# Pulled from riya/arey-web · production', 'DATABASE_URL=postgres://…', 'API_KEY=sk_live_9f2a7c41e8']
  }), /*#__PURE__*/React.createElement("h2", {
    id: "props"
  }, "Command reference"), /*#__PURE__*/React.createElement(PropsTable, {
    rows: [['arey deploy', '--prod, --yes', '—'], ['arey link', '--project <name>', 'interactive'], ['arey env pull', '--environment <env>', 'production'], ['arey logs', '--follow, --since <t>', '1h'], ['arey rollback', '<deployment>', 'previous']]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--space-4)',
      marginTop: 'var(--space-12)',
      maxWidth: 'var(--prose-max)'
    }
  }, /*#__PURE__*/React.createElement(Card, {
    interactive: true,
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-caption)',
      color: 'var(--text-tertiary)',
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "arrow-left",
    size: 12
  }), "Previous"), /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-title-3)',
      color: 'var(--text-primary)',
      marginTop: 6
    }
  }, "Introduction")), /*#__PURE__*/React.createElement(Card, {
    interactive: true,
    style: {
      flex: 1,
      textAlign: 'right'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-caption)',
      color: 'var(--text-tertiary)',
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      justifyContent: 'flex-end'
    }
  }, "Next", /*#__PURE__*/React.createElement(Icon, {
    name: "arrow-right",
    size: 12
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-title-3)',
      color: 'var(--text-primary)',
      marginTop: 6
    }
  }, "Projects")))), /*#__PURE__*/React.createElement(OnThisPage, {
    items: TOC,
    active: active,
    onSelect: setActive
  })));
}
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/React.createElement(DocsApp, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/docs/DocsApp.jsx", error: String((e && e.message) || e) }); }

// ui_kits/docs/DocsParts.jsx
try { (() => {
const {
  SidebarNav,
  Input,
  Kbd,
  IconButton,
  Button,
  Badge,
  Icon,
  Card,
  Tabs,
  SegmentedControl
} = window.AreyDesignSystem_1909f9;
function DocsHeader() {
  const [dark, setDark] = React.useState(false);
  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  }, [dark]);
  return /*#__PURE__*/React.createElement("header", {
    style: {
      position: 'sticky',
      top: 0,
      zIndex: 40,
      height: 'var(--topbar-h)',
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-6)',
      padding: '0 var(--space-8)',
      background: 'var(--surface-glass)',
      backdropFilter: 'var(--backdrop-glass)',
      WebkitBackdropFilter: 'var(--backdrop-glass)',
      borderBottom: '1px solid var(--border-subtle)'
    }
  }, /*#__PURE__*/React.createElement("a", {
    href: "#",
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      color: 'var(--text-primary)'
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logo-mark.svg",
    style: {
      height: 20
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      font: 'var(--weight-semibold) 15px var(--font-sans)',
      letterSpacing: '-.03em'
    }
  }, "arey"), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 1,
      height: 14,
      background: 'var(--border-default)'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      font: 'var(--type-label)',
      color: 'var(--text-secondary)'
    }
  }, "Docs")), /*#__PURE__*/React.createElement("nav", {
    style: {
      display: 'flex',
      gap: 'var(--space-5)'
    }
  }, ['Guides', 'Reference', 'CLI', 'Changelog'].map((n, i) => /*#__PURE__*/React.createElement("a", {
    key: n,
    href: "#",
    style: {
      font: 'var(--type-label)',
      color: i === 0 ? 'var(--text-primary)' : 'var(--text-secondary)'
    }
  }, n))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 260
    }
  }, /*#__PURE__*/React.createElement(Input, {
    size: "sm",
    icon: "magnifying-glass",
    placeholder: "Search docs",
    suffix: /*#__PURE__*/React.createElement(Kbd, {
      keys: "cmd+k"
    })
  })), /*#__PURE__*/React.createElement(IconButton, {
    icon: dark ? 'sun' : 'moon',
    label: "Toggle theme",
    onClick: () => setDark(!dark)
  }), /*#__PURE__*/React.createElement(IconButton, {
    icon: "github-logo",
    label: "GitHub"
  }));
}
function CodeBlock({
  lang = 'bash',
  filename,
  lines
}) {
  const [copied, setCopied] = React.useState(false);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      border: '1px solid var(--border-default)',
      borderRadius: 'var(--radius-card)',
      overflow: 'hidden',
      background: 'var(--bg-base)',
      margin: '0 0 var(--space-6)',
      maxWidth: 'var(--prose-max)',
      boxShadow: 'var(--shadow-sm)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-3)',
      padding: 'var(--space-2) var(--space-2) var(--space-2) var(--space-4)',
      borderBottom: '1px solid var(--border-subtle)',
      background: 'var(--bg-subtle)'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: filename ? 'file-code' : 'terminal-window',
    size: 14,
    color: "var(--text-tertiary)"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      font: 'var(--type-code)',
      fontSize: 'var(--text-12)',
      color: 'var(--text-secondary)'
    }
  }, filename || lang), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }), /*#__PURE__*/React.createElement(IconButton, {
    icon: copied ? 'check' : 'copy',
    label: "Copy code",
    size: "sm",
    onClick: () => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  })), /*#__PURE__*/React.createElement("pre", {
    style: {
      margin: 0,
      padding: 'var(--space-4) var(--space-5)',
      overflow: 'auto'
    }
  }, /*#__PURE__*/React.createElement("code", {
    style: {
      font: 'var(--type-code)',
      display: 'grid',
      gap: 2
    }
  }, lines.map((l, i) => /*#__PURE__*/React.createElement("span", {
    key: i,
    style: {
      color: l.startsWith('#') || l.startsWith('//') ? 'var(--text-tertiary)' : 'var(--text-body)',
      whiteSpace: 'pre'
    }
  }, l.startsWith('$') ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-tertiary)',
      userSelect: 'none'
    }
  }, "$ "), l.slice(2)) : l)))));
}
const CALLOUT = {
  note: {
    icon: 'info',
    color: 'var(--accent-solid)',
    wash: 'var(--accent-wash)',
    border: 'var(--accent-border)'
  },
  warning: {
    icon: 'warning',
    color: 'var(--warning-solid)',
    wash: 'var(--warning-wash)',
    border: 'var(--warning-solid)'
  },
  danger: {
    icon: 'warning-octagon',
    color: 'var(--danger-solid)',
    wash: 'var(--danger-wash)',
    border: 'var(--danger-solid)'
  }
};
function Callout({
  tone = 'note',
  title,
  children
}) {
  const c = CALLOUT[tone];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--space-3)',
      padding: 'var(--space-4) var(--space-5)',
      background: c.wash,
      border: '1px solid ' + c.border,
      borderRadius: 'var(--radius-card)',
      margin: '0 0 var(--space-6)',
      maxWidth: 'var(--prose-max)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: c.color,
      marginTop: 1,
      display: 'flex'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: c.icon,
    size: 17,
    weight: "fill"
  })), /*#__PURE__*/React.createElement("div", null, title && /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-label)',
      color: 'var(--text-primary)',
      marginBottom: 4
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-body)',
      color: 'var(--text-body)'
    }
  }, children)));
}
function PropsTable({
  rows
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-card)',
      overflow: 'hidden',
      maxWidth: 'var(--prose-max)',
      margin: '0 0 var(--space-6)',
      boxShadow: 'var(--shadow-sm)',
      background: 'var(--surface-card)'
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: '100%',
      borderCollapse: 'collapse'
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, ['Prop', 'Type', 'Default'].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: {
      textAlign: 'left',
      font: 'var(--type-eyebrow)',
      letterSpacing: 'var(--tracking-eyebrow)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)',
      fontWeight: 'var(--weight-medium)',
      padding: 'var(--space-3) var(--space-4)',
      background: 'var(--bg-subtle)',
      borderBottom: '1px solid var(--border-subtle)'
    }
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, rows.map((r, i) => /*#__PURE__*/React.createElement("tr", {
    key: i
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      padding: 'var(--space-3) var(--space-4)',
      borderTop: i ? '1px solid var(--border-subtle)' : 0,
      font: 'var(--type-code)',
      color: 'var(--text-primary)'
    }
  }, r[0]), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: 'var(--space-3) var(--space-4)',
      borderTop: i ? '1px solid var(--border-subtle)' : 0,
      font: 'var(--type-code)',
      color: 'var(--text-accent)'
    }
  }, r[1]), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: 'var(--space-3) var(--space-4)',
      borderTop: i ? '1px solid var(--border-subtle)' : 0,
      font: 'var(--type-code)',
      color: 'var(--text-tertiary)'
    }
  }, r[2]))))));
}
function OnThisPage({
  items,
  active,
  onSelect
}) {
  return /*#__PURE__*/React.createElement("aside", {
    style: {
      width: 216,
      flex: 'none',
      position: 'sticky',
      top: 'calc(var(--topbar-h) + var(--space-10))',
      alignSelf: 'flex-start',
      display: 'grid',
      gap: 'var(--space-3)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-eyebrow)',
      letterSpacing: 'var(--tracking-eyebrow)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)'
    }
  }, "On this page"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-2)',
      borderLeft: '1px solid var(--border-subtle)'
    }
  }, items.map(it => /*#__PURE__*/React.createElement("a", {
    key: it.id,
    href: '#' + it.id,
    onClick: () => onSelect(it.id),
    style: {
      font: 'var(--type-label)',
      paddingLeft: 'var(--space-4)',
      marginLeft: -1,
      borderLeft: '1px solid ' + (active === it.id ? 'var(--text-primary)' : 'transparent'),
      color: active === it.id ? 'var(--text-primary)' : 'var(--text-secondary)',
      paddingTop: 2,
      paddingBottom: 2
    }
  }, it.label))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 'var(--space-4)',
      display: 'grid',
      gap: 'var(--space-2)'
    }
  }, /*#__PURE__*/React.createElement("a", {
    href: "#",
    style: {
      font: 'var(--type-caption)',
      color: 'var(--text-secondary)',
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "pencil-simple",
    size: 13
  }), "Edit this page"), /*#__PURE__*/React.createElement("a", {
    href: "#",
    style: {
      font: 'var(--type-caption)',
      color: 'var(--text-secondary)',
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "chat-circle",
    size: 13
  }), "Send feedback")));
}
Object.assign(window, {
  DocsHeader,
  CodeBlock,
  Callout,
  PropsTable,
  OnThisPage
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/docs/DocsParts.jsx", error: String((e && e.message) || e) }); }

// ui_kits/mobile/MobileApp.jsx
try { (() => {
const {
  Button,
  Field,
  Input,
  Select,
  Toast,
  EmptyState,
  Switch,
  ListRow,
  List
} = window.AreyDesignSystem_1909f9;
const PROJECTS = window.PROJECTS,
  STATUS = window.STATUS;
function Device() {
  const [tab, setTab] = React.useState('projects');
  const [project, setProject] = React.useState(null);
  const [sheet, setSheet] = React.useState(null);
  let screen;
  if (tab === 'projects') {
    screen = project ? /*#__PURE__*/React.createElement(ProjectScreen, {
      p: project,
      onBack: () => setProject(null),
      onDeploy: () => setSheet('deploy')
    }) : /*#__PURE__*/React.createElement(ProjectsScreen, {
      onOpen: setProject,
      onNew: () => setSheet('new')
    });
  } else if (tab === 'settings') screen = /*#__PURE__*/React.createElement(SettingsScreen, null);else if (tab === 'activity') screen = /*#__PURE__*/React.createElement(ActivityScreen, null);else screen = /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(NavBar, {
    title: "Search",
    large: true
  }), /*#__PURE__*/React.createElement(Scroll, null, /*#__PURE__*/React.createElement(EmptyState, {
    icon: "magnifying-glass",
    title: "Search everything",
    description: "Projects, deployments, domains and logs."
  })));
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(StatusBar, null), screen, /*#__PURE__*/React.createElement(TabBar, {
    value: tab,
    onChange: t => {
      setProject(null);
      setTab(t);
    }
  }), /*#__PURE__*/React.createElement(HomeIndicator, null), /*#__PURE__*/React.createElement(Sheet, {
    open: sheet === 'deploy',
    title: "Deploy arey-web",
    onClose: () => setSheet(null),
    actions: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      size: "lg",
      block: true,
      onClick: () => setSheet(null)
    }, "Deploy to production"), /*#__PURE__*/React.createElement(Button, {
      variant: "ghost",
      size: "lg",
      block: true,
      onClick: () => setSheet(null)
    }, "Cancel"))
  }, /*#__PURE__*/React.createElement(List, {
    inset: true
  }, /*#__PURE__*/React.createElement(ListRow, {
    icon: "git-branch",
    title: "Branch",
    value: "main",
    mono: true
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "git-commit",
    title: "Commit",
    value: "a3f91c8",
    mono: true
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "globe-hemisphere-west",
    title: "Region",
    value: "iad1",
    mono: true
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "bell",
    title: "Notify me when ready",
    trailing: /*#__PURE__*/React.createElement(Switch, {
      defaultChecked: true,
      "aria-label": "Notify me"
    })
  }))), /*#__PURE__*/React.createElement(Sheet, {
    open: sheet === 'new',
    title: "New project",
    onClose: () => setSheet(null),
    actions: /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      size: "lg",
      block: true,
      onClick: () => setSheet(null)
    }, "Create project")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-5)',
      paddingBottom: 4
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Project name",
    hint: "Lowercase letters, numbers and dashes"
  }, /*#__PURE__*/React.createElement(Input, {
    size: "lg",
    placeholder: "arey-web"
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Framework"
  }, /*#__PURE__*/React.createElement(Select, {
    size: "lg",
    options: ['Next.js', 'Astro', 'Vite', 'Expo']
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Region"
  }, /*#__PURE__*/React.createElement(Select, {
    size: "lg",
    options: ['Washington, D.C. (iad1)', 'Mumbai (bom1)']
  })))));
}
function StaticPhone({
  children,
  label
}) {
  return /*#__PURE__*/React.createElement(Phone, {
    label: label
  }, children);
}
function MobileApp() {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--bg-canvas)',
      minHeight: '100vh',
      padding: 'var(--space-10) var(--space-8)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1200,
      margin: '0 auto'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-end',
      gap: 'var(--space-6)',
      marginBottom: 'var(--space-8)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-eyebrow)',
      letterSpacing: 'var(--tracking-eyebrow)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)',
      marginBottom: 'var(--space-3)'
    }
  }, "arey Mobile"), /*#__PURE__*/React.createElement("h1", {
    style: {
      font: 'var(--type-title-1)',
      letterSpacing: 'var(--tracking-heading)'
    }
  }, "iOS screens"), /*#__PURE__*/React.createElement("p", {
    style: {
      font: 'var(--type-body-lg)',
      color: 'var(--text-secondary)',
      marginTop: 'var(--space-2)'
    }
  }, "The left device is live \u2014 tap through projects, open a deployment sheet, switch tabs.")), /*#__PURE__*/React.createElement(ThemeSwitch, null)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--space-10)',
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement(Phone, {
    label: "Live"
  }, /*#__PURE__*/React.createElement(Device, null)), /*#__PURE__*/React.createElement(Phone, {
    label: "Settings"
  }, /*#__PURE__*/React.createElement(StatusBar, null), /*#__PURE__*/React.createElement(SettingsScreen, null), /*#__PURE__*/React.createElement(TabBar, {
    value: "settings",
    onChange: () => {}
  }), /*#__PURE__*/React.createElement(HomeIndicator, null)), /*#__PURE__*/React.createElement(Phone, {
    label: "Activity"
  }, /*#__PURE__*/React.createElement(StatusBar, null), /*#__PURE__*/React.createElement(ActivityScreen, null), /*#__PURE__*/React.createElement(TabBar, {
    value: "activity",
    onChange: () => {}
  }), /*#__PURE__*/React.createElement(HomeIndicator, null)))));
}
function ThemeSwitch() {
  const {
    SegmentedControl
  } = window.AreyDesignSystem_1909f9;
  const [t, setT] = React.useState('light');
  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', t);
  }, [t]);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: 200
    }
  }, /*#__PURE__*/React.createElement(SegmentedControl, {
    value: t,
    onChange: setT,
    options: [{
      value: 'light',
      label: 'Light',
      icon: 'sun'
    }, {
      value: 'dark',
      label: 'Dark',
      icon: 'moon'
    }]
  }));
}
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/React.createElement(MobileApp, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/mobile/MobileApp.jsx", error: String((e && e.message) || e) }); }

// ui_kits/mobile/Phone.jsx
try { (() => {
const {
  Icon,
  IconButton,
  Badge,
  List,
  ListRow,
  Switch,
  SegmentedControl,
  Button,
  Avatar,
  ProgressBar,
  Card
} = window.AreyDesignSystem_1909f9;

/* A neutral phone shell — bezel, status bar, home indicator. No vendor branding. */
function Phone({
  children,
  label
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-4)',
      justifyItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 375,
      height: 720,
      borderRadius: 46,
      padding: 10,
      background: 'var(--grey-1000)',
      boxShadow: 'var(--shadow-xl)',
      flex: 'none'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      width: '100%',
      height: '100%',
      borderRadius: 36,
      overflow: 'hidden',
      background: 'var(--bg-canvas)',
      display: 'flex',
      flexDirection: 'column'
    }
  }, children)), label && /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-eyebrow)',
      letterSpacing: 'var(--tracking-eyebrow)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)'
    }
  }, label));
}
function StatusBar() {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: 44,
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      zIndex: 20,
      pointerEvents: 'none'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: 'var(--weight-semibold) 13px var(--font-sans)',
      color: 'var(--text-primary)',
      letterSpacing: 0
    }
  }, "9:41"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 5,
      color: 'var(--text-primary)'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "cell-signal-full",
    size: 15,
    weight: "fill"
  }), /*#__PURE__*/React.createElement(Icon, {
    name: "wifi-high",
    size: 15,
    weight: "bold"
  }), /*#__PURE__*/React.createElement(Icon, {
    name: "battery-full",
    size: 17,
    weight: "fill"
  })));
}
function HomeIndicator() {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      bottom: 7,
      left: 0,
      right: 0,
      display: 'grid',
      placeItems: 'center',
      zIndex: 30,
      pointerEvents: 'none'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 134,
      height: 5,
      borderRadius: 3,
      background: 'var(--text-primary)',
      opacity: .85
    }
  }));
}

/* Glass nav bar. Compact form shows a centred title; large form shows the 34px title below. */
function NavBar({
  title,
  large,
  back,
  trailing,
  onBack
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'sticky',
      top: 0,
      zIndex: 15,
      background: 'var(--surface-glass)',
      backdropFilter: 'var(--backdrop-glass)',
      WebkitBackdropFilter: 'var(--backdrop-glass)',
      borderBottom: '1px solid var(--border-subtle)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 44
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 44,
      display: 'flex',
      alignItems: 'center',
      padding: '0 8px'
    }
  }, back ? /*#__PURE__*/React.createElement("button", {
    onClick: onBack,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 2,
      height: 44,
      padding: '0 8px',
      border: 0,
      background: 'none',
      color: 'var(--accent-solid)',
      font: 'var(--weight-regular) 17px var(--font-sans)',
      letterSpacing: '-.01em',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "caret-left",
    size: 20,
    weight: "bold"
  }), back) : /*#__PURE__*/React.createElement("div", {
    style: {
      width: 60
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      textAlign: 'center',
      font: 'var(--weight-semibold) 17px var(--font-sans)',
      letterSpacing: '-.02em',
      color: 'var(--text-primary)',
      opacity: large ? 0 : 1,
      transition: 'opacity var(--duration-fast) var(--ease-out)'
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 60,
      display: 'flex',
      justifyContent: 'flex-end',
      gap: 2
    }
  }, trailing)), large && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 20px 8px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--weight-bold) 34px/1.1 var(--font-sans)',
      letterSpacing: '-.032em',
      color: 'var(--text-primary)'
    }
  }, title)));
}
function TabBar({
  value,
  onChange
}) {
  const items = [{
    value: 'projects',
    label: 'Projects',
    icon: 'squares-four'
  }, {
    value: 'activity',
    label: 'Activity',
    icon: 'pulse'
  }, {
    value: 'search',
    label: 'Search',
    icon: 'magnifying-glass'
  }, {
    value: 'settings',
    label: 'Settings',
    icon: 'gear-six'
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'sticky',
      bottom: 0,
      zIndex: 25,
      background: 'var(--surface-glass)',
      backdropFilter: 'var(--backdrop-glass)',
      WebkitBackdropFilter: 'var(--backdrop-glass)',
      borderTop: '1px solid var(--border-subtle)',
      paddingBottom: 22
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridAutoFlow: 'column',
      gridAutoColumns: '1fr',
      paddingTop: 8
    }
  }, items.map(it => {
    const on = value === it.value;
    return /*#__PURE__*/React.createElement("button", {
      key: it.value,
      onClick: () => onChange(it.value),
      style: {
        display: 'grid',
        justifyItems: 'center',
        gap: 3,
        border: 0,
        background: 'none',
        cursor: 'pointer',
        padding: '2px 0',
        color: on ? 'var(--accent-solid)' : 'var(--text-tertiary)',
        transition: 'color var(--duration-fast) var(--ease-out)'
      }
    }, /*#__PURE__*/React.createElement(Icon, {
      name: it.icon,
      size: 24,
      weight: on ? 'fill' : 'regular'
    }), /*#__PURE__*/React.createElement("span", {
      style: {
        font: 'var(--weight-medium) 10px var(--font-sans)',
        letterSpacing: 0
      }
    }, it.label));
  })));
}
function Scroll({
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflow: 'auto',
      WebkitOverflowScrolling: 'touch'
    }
  }, children);
}
function GroupLabel({
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-eyebrow)',
      letterSpacing: 'var(--tracking-eyebrow)',
      textTransform: 'uppercase',
      color: 'var(--text-tertiary)',
      padding: '0 20px var(--space-2)'
    }
  }, children);
}
function Group({
  label,
  children,
  footer
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-2)',
      margin: '0 0 var(--space-6)'
    }
  }, label && /*#__PURE__*/React.createElement(GroupLabel, null, label), /*#__PURE__*/React.createElement("div", {
    style: {
      margin: '0 16px'
    }
  }, /*#__PURE__*/React.createElement(List, {
    inset: true
  }, children)), footer && /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-caption)',
      color: 'var(--text-secondary)',
      padding: '0 20px'
    }
  }, footer));
}

/* Bottom sheet — 20px top radius, rises with a spring. */
function Sheet({
  open,
  title,
  onClose,
  children,
  actions
}) {
  if (!open) return null;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      zIndex: 40,
      display: 'flex',
      alignItems: 'flex-end',
      background: 'var(--surface-scrim)',
      animation: 'arey-fade var(--duration-normal) var(--ease-out)'
    },
    onClick: onClose
  }, /*#__PURE__*/React.createElement("div", {
    onClick: e => e.stopPropagation(),
    style: {
      width: '100%',
      background: 'var(--surface-raised)',
      borderRadius: 'var(--radius-sheet) var(--radius-sheet) 0 0',
      boxShadow: 'var(--shadow-xl)',
      paddingBottom: 34,
      animation: 'arey-rise var(--duration-slow) var(--ease-out)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      placeItems: 'center',
      padding: '8px 0 4px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 36,
      height: 5,
      borderRadius: 3,
      background: 'var(--border-strong)'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      padding: '4px 16px 12px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      font: 'var(--weight-semibold) 17px var(--font-sans)',
      letterSpacing: '-.02em',
      color: 'var(--text-primary)'
    }
  }, title), /*#__PURE__*/React.createElement(IconButton, {
    icon: "x",
    label: "Close",
    size: "sm",
    onClick: onClose
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px'
    }
  }, children), actions && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gap: 'var(--space-2)',
      padding: '16px 16px 0'
    }
  }, actions)));
}
Object.assign(window, {
  Phone,
  StatusBar,
  HomeIndicator,
  NavBar,
  TabBar,
  Scroll,
  Group,
  GroupLabel,
  Sheet
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/mobile/Phone.jsx", error: String((e && e.message) || e) }); }

// ui_kits/mobile/Screens.jsx
try { (() => {
const {
  Icon,
  IconButton,
  Badge,
  ListRow,
  Switch,
  SegmentedControl,
  Button,
  Avatar,
  ProgressBar,
  Input,
  Tag
} = window.AreyDesignSystem_1909f9;
function ProjectsScreen({
  onOpen,
  onNew
}) {
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(NavBar, {
    title: "Projects",
    large: true,
    trailing: /*#__PURE__*/React.createElement(IconButton, {
      icon: "plus",
      label: "New project",
      onClick: onNew
    })
  }), /*#__PURE__*/React.createElement(Scroll, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '8px 16px 16px'
    }
  }, /*#__PURE__*/React.createElement(Input, {
    size: "md",
    icon: "magnifying-glass",
    placeholder: "Search projects"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      padding: '0 16px 20px',
      overflow: 'auto'
    }
  }, /*#__PURE__*/React.createElement(Tag, {
    icon: "funnel",
    onClick: () => {},
    selected: true
  }, "All"), /*#__PURE__*/React.createElement(Tag, {
    onClick: () => {}
  }, "Ready"), /*#__PURE__*/React.createElement(Tag, {
    onClick: () => {}
  }, "Building"), /*#__PURE__*/React.createElement(Tag, {
    onClick: () => {}
  }, "Failed")), /*#__PURE__*/React.createElement(Group, {
    label: "Production"
  }, window.PROJECTS.slice(0, 3).map(p => {
    const s = window.STATUS[p.status];
    return /*#__PURE__*/React.createElement(ListRow, {
      key: p.name,
      leading: /*#__PURE__*/React.createElement(Avatar, {
        name: p.name.replace('arey-', ''),
        square: true,
        tone: "accent"
      }),
      title: p.name,
      subtitle: p.branch + ' · ' + p.time,
      trailing: /*#__PURE__*/React.createElement(Badge, {
        tone: s.tone,
        dot: true,
        size: "sm"
      }, s.label),
      chevron: true,
      onClick: () => onOpen(p)
    });
  })), /*#__PURE__*/React.createElement(Group, {
    label: "All projects",
    footer: "Pull to refresh. Deployments update live."
  }, window.PROJECTS.slice(3).map(p => {
    const s = window.STATUS[p.status];
    return /*#__PURE__*/React.createElement(ListRow, {
      key: p.name,
      leading: /*#__PURE__*/React.createElement(Avatar, {
        name: p.name.replace('arey-', ''),
        square: true
      }),
      title: p.name,
      subtitle: p.framework + ' · ' + p.time,
      trailing: /*#__PURE__*/React.createElement(Badge, {
        tone: s.tone,
        dot: true,
        size: "sm"
      }, s.label),
      chevron: true,
      onClick: () => onOpen(p)
    });
  }))));
}
function ProjectScreen({
  p,
  onBack,
  onDeploy
}) {
  const s = window.STATUS[p.status];
  const [range, setRange] = React.useState('7d');
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(NavBar, {
    title: p.name,
    back: "Projects",
    onBack: onBack,
    trailing: /*#__PURE__*/React.createElement(IconButton, {
      icon: "dots-three",
      label: "Options"
    })
  }), /*#__PURE__*/React.createElement(Scroll, null, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '20px 16px',
      display: 'grid',
      gap: 'var(--space-5)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    name: p.name.replace('arey-', ''),
    square: true,
    tone: "accent",
    size: "xl"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--weight-semibold) 22px var(--font-sans)',
      letterSpacing: '-.028em',
      color: 'var(--text-primary)'
    }
  }, p.name), /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-code)',
      color: 'var(--text-tertiary)',
      marginTop: 2
    }
  }, p.name, ".arey.app")), /*#__PURE__*/React.createElement(Badge, {
    tone: s.tone,
    dot: true
  }, s.label)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridAutoFlow: 'column',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    size: "lg",
    iconLeft: "rocket-launch",
    onClick: onDeploy
  }, "Deploy"), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "lg",
    iconLeft: "arrow-square-out"
  }, "Visit")), /*#__PURE__*/React.createElement(SegmentedControl, {
    size: "lg",
    value: range,
    onChange: setRange,
    options: [{
      value: '24h',
      label: 'Day'
    }, {
      value: '7d',
      label: 'Week'
    }, {
      value: '30d',
      label: 'Month'
    }]
  })), /*#__PURE__*/React.createElement(Group, {
    label: "Latest deployment"
  }, /*#__PURE__*/React.createElement(ListRow, {
    icon: "git-commit",
    title: window.DEPLOYMENTS[0].msg,
    subtitle: window.DEPLOYMENTS[0].sha + ' · ' + window.DEPLOYMENTS[0].author,
    chevron: true,
    onClick: () => {}
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "timer",
    title: "Duration",
    value: p.dur,
    mono: true
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "globe-hemisphere-west",
    title: "Region",
    value: "iad1",
    mono: true
  })), /*#__PURE__*/React.createElement(Group, {
    label: "Usage",
    footer: "68 % of the 1 TB included in the Hobby plan."
  }, /*#__PURE__*/React.createElement(ListRow, {
    icon: "gauge",
    title: "Bandwidth",
    value: "412 GB",
    mono: true
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "lightning",
    title: "Requests",
    value: "2.4 M",
    mono: true
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "clock-countdown",
    title: "Build minutes",
    value: "1 240",
    mono: true
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 20px 24px'
    }
  }, /*#__PURE__*/React.createElement(ProgressBar, {
    value: 68
  }))));
}
function SettingsScreen() {
  const [theme, setTheme] = React.useState('system');
  React.useEffect(() => {
    if (theme === 'system') return;
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(NavBar, {
    title: "Settings",
    large: true
  }), /*#__PURE__*/React.createElement(Scroll, null, /*#__PURE__*/React.createElement("div", {
    style: {
      margin: '8px 16px 24px',
      display: 'flex',
      alignItems: 'center',
      gap: 14,
      padding: 16,
      background: 'var(--surface-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-card)',
      boxShadow: 'var(--shadow-sm)'
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    name: "Riya Menon",
    size: "xl"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--weight-semibold) 17px var(--font-sans)',
      letterSpacing: '-.02em',
      color: 'var(--text-primary)'
    }
  }, "Riya Menon"), /*#__PURE__*/React.createElement("div", {
    style: {
      font: 'var(--type-code)',
      color: 'var(--text-tertiary)'
    }
  }, "riya@arey.dev")), /*#__PURE__*/React.createElement(Icon, {
    name: "caret-right",
    size: 16,
    color: "var(--text-tertiary)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px 24px',
      display: 'grid',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(GroupLabel, null, "Appearance"), /*#__PURE__*/React.createElement(SegmentedControl, {
    size: "lg",
    value: theme,
    onChange: setTheme,
    options: [{
      value: 'light',
      label: 'Light',
      icon: 'sun'
    }, {
      value: 'dark',
      label: 'Dark',
      icon: 'moon'
    }, {
      value: 'system',
      label: 'Auto',
      icon: 'circle-half'
    }]
  })), /*#__PURE__*/React.createElement(Group, {
    label: "Notifications",
    footer: "Push notifications are sent for projects you own."
  }, /*#__PURE__*/React.createElement(ListRow, {
    icon: "bell",
    title: "Deployment ready",
    trailing: /*#__PURE__*/React.createElement(Switch, {
      defaultChecked: true,
      "aria-label": "Deployment ready"
    })
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "warning-octagon",
    title: "Build failed",
    trailing: /*#__PURE__*/React.createElement(Switch, {
      defaultChecked: true,
      "aria-label": "Build failed"
    })
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "chat-circle-dots",
    title: "Comments",
    trailing: /*#__PURE__*/React.createElement(Switch, {
      "aria-label": "Comments"
    })
  })), /*#__PURE__*/React.createElement(Group, {
    label: "Account"
  }, /*#__PURE__*/React.createElement(ListRow, {
    icon: "users-three",
    title: "Team",
    value: "riya",
    chevron: true,
    onClick: () => {}
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "credit-card",
    title: "Plan",
    value: "Hobby",
    chevron: true,
    onClick: () => {}
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "key",
    title: "API keys",
    chevron: true,
    onClick: () => {}
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "shield-check",
    title: "Two-factor auth",
    value: "On",
    chevron: true,
    onClick: () => {}
  })), /*#__PURE__*/React.createElement(Group, {
    label: "About"
  }, /*#__PURE__*/React.createElement(ListRow, {
    icon: "book-open",
    title: "Documentation",
    chevron: true,
    onClick: () => {}
  }), /*#__PURE__*/React.createElement(ListRow, {
    icon: "info",
    title: "Version",
    value: "4.2.0 (812)",
    mono: true
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px 32px'
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "lg",
    block: true
  }, "Sign out"))));
}
function ActivityScreen() {
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(NavBar, {
    title: "Activity",
    large: true,
    trailing: /*#__PURE__*/React.createElement(IconButton, {
      icon: "funnel",
      label: "Filter"
    })
  }), /*#__PURE__*/React.createElement(Scroll, null, /*#__PURE__*/React.createElement(Group, {
    label: "Today"
  }, window.DEPLOYMENTS.slice(0, 4).map((d, i) => {
    const s = window.STATUS[d.status];
    return /*#__PURE__*/React.createElement(ListRow, {
      key: i,
      leading: /*#__PURE__*/React.createElement(Avatar, {
        name: d.author,
        size: "sm"
      }),
      title: d.msg,
      subtitle: d.author + ' · ' + d.branch,
      trailing: /*#__PURE__*/React.createElement(Badge, {
        tone: s.tone,
        dot: true,
        size: "sm"
      }, s.label),
      chevron: true,
      onClick: () => {}
    });
  })), /*#__PURE__*/React.createElement(Group, {
    label: "Yesterday"
  }, window.DEPLOYMENTS.slice(4).map((d, i) => {
    const s = window.STATUS[d.status];
    return /*#__PURE__*/React.createElement(ListRow, {
      key: i,
      leading: /*#__PURE__*/React.createElement(Avatar, {
        name: d.author,
        size: "sm"
      }),
      title: d.msg,
      subtitle: d.author + ' · ' + d.branch,
      trailing: /*#__PURE__*/React.createElement(Badge, {
        tone: s.tone,
        dot: true,
        size: "sm"
      }, s.label),
      chevron: true,
      onClick: () => {}
    });
  }))));
}
Object.assign(window, {
  ProjectsScreen,
  ProjectScreen,
  SettingsScreen,
  ActivityScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/mobile/Screens.jsx", error: String((e && e.message) || e) }); }

// ui_kits/mobile/data.jsx
try { (() => {
const PROJECTS = [{
  name: 'arey-web',
  framework: 'Next.js',
  branch: 'main',
  status: 'ready',
  time: '3 m ago',
  dur: '48 s',
  sha: 'a3f91c8',
  author: 'Riya Menon'
}, {
  name: 'arey-docs',
  framework: 'Astro',
  branch: 'main',
  status: 'building',
  time: '6 m ago',
  dur: '—',
  sha: '7c02be1',
  author: 'Dev Kapoor'
}, {
  name: 'arey-api',
  framework: 'Node',
  branch: 'main',
  status: 'ready',
  time: '1 h ago',
  dur: '1 m 12 s',
  sha: 'f18d4aa',
  author: 'Sam Ito'
}, {
  name: 'arey-mobile',
  framework: 'Expo',
  branch: 'release/4.2',
  status: 'failed',
  time: '2 h ago',
  dur: '22 s',
  sha: '9b7e330',
  author: 'Lea Fischer'
}, {
  name: 'arey-design',
  framework: 'Vite',
  branch: 'main',
  status: 'ready',
  time: '5 h ago',
  dur: '31 s',
  sha: '2d5c917',
  author: 'Riya Menon'
}, {
  name: 'arey-status',
  framework: 'Static',
  branch: 'main',
  status: 'queued',
  time: '5 h ago',
  dur: '—',
  sha: '55a1f0d',
  author: 'Nils Berg'
}];
const DEPLOYMENTS = [{
  env: 'Production',
  status: 'ready',
  sha: 'a3f91c8',
  msg: 'Tighten card shadow on dark surfaces',
  branch: 'main',
  author: 'Riya Menon',
  dur: '48 s',
  time: '3 m ago'
}, {
  env: 'Preview',
  status: 'building',
  sha: '7c02be1',
  msg: 'Add usage meter to overview',
  branch: 'feat/usage',
  author: 'Dev Kapoor',
  dur: '—',
  time: '6 m ago'
}, {
  env: 'Preview',
  status: 'ready',
  sha: 'f18d4aa',
  msg: 'Move eyebrow labels to mono',
  branch: 'feat/type',
  author: 'Sam Ito',
  dur: '1 m 12 s',
  time: '1 h ago'
}, {
  env: 'Preview',
  status: 'failed',
  sha: '9b7e330',
  msg: 'Bump build image to node-20',
  branch: 'chore/node',
  author: 'Lea Fischer',
  dur: '22 s',
  time: '2 h ago'
}, {
  env: 'Production',
  status: 'ready',
  sha: '2d5c917',
  msg: 'Ship segmented control',
  branch: 'main',
  author: 'Riya Menon',
  dur: '31 s',
  time: '5 h ago'
}, {
  env: 'Preview',
  status: 'ready',
  sha: '55a1f0d',
  msg: 'Docs: deployment lifecycle',
  branch: 'docs/lifecycle',
  author: 'Nils Berg',
  dur: '39 s',
  time: '8 h ago'
}, {
  env: 'Preview',
  status: 'ready',
  sha: 'c41b8e2',
  msg: 'Fix focus ring offset in Safari',
  branch: 'fix/focus',
  author: 'Dev Kapoor',
  dur: '44 s',
  time: '1 d ago'
}];
const STATUS = {
  ready: {
    tone: 'success',
    label: 'Ready'
  },
  building: {
    tone: 'warning',
    label: 'Building'
  },
  failed: {
    tone: 'danger',
    label: 'Failed'
  },
  queued: {
    tone: 'neutral',
    label: 'Queued'
  }
};
const MEMBERS = [{
  name: 'Riya Menon',
  email: 'riya@arey.dev',
  role: 'Owner'
}, {
  name: 'Dev Kapoor',
  email: 'dev@arey.dev',
  role: 'Member'
}, {
  name: 'Sam Ito',
  email: 'sam@arey.dev',
  role: 'Member'
}, {
  name: 'Lea Fischer',
  email: 'lea@arey.dev',
  role: 'Viewer'
}];
Object.assign(window, {
  PROJECTS,
  DEPLOYMENTS,
  STATUS,
  MEMBERS
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/mobile/data.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Avatar = __ds_scope.Avatar;

__ds_ns.AvatarStack = __ds_scope.AvatarStack;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.Icon = __ds_scope.Icon;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.Kbd = __ds_scope.Kbd;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.Dialog = __ds_scope.Dialog;

__ds_ns.EmptyState = __ds_scope.EmptyState;

__ds_ns.ProgressBar = __ds_scope.ProgressBar;

__ds_ns.Spinner = __ds_scope.Spinner;

__ds_ns.Toast = __ds_scope.Toast;

__ds_ns.ToastRegion = __ds_scope.ToastRegion;

__ds_ns.Tooltip = __ds_scope.Tooltip;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.Field = __ds_scope.Field;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.Radio = __ds_scope.Radio;

__ds_ns.RadioGroup = __ds_scope.RadioGroup;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Switch = __ds_scope.Switch;

__ds_ns.Textarea = __ds_scope.Textarea;

__ds_ns.Breadcrumbs = __ds_scope.Breadcrumbs;

__ds_ns.ListRow = __ds_scope.ListRow;

__ds_ns.List = __ds_scope.List;

__ds_ns.SegmentedControl = __ds_scope.SegmentedControl;

__ds_ns.SidebarNav = __ds_scope.SidebarNav;

__ds_ns.Tabs = __ds_scope.Tabs;

})();
