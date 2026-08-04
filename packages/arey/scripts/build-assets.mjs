// Assembles dist/styles.css as a self-contained stylesheet (tokens + vendored
// Phosphor icon fonts, all relative paths) and copies the hand-authored .d.ts
// tree alongside the compiled JS. Run after tsup via `pnpm build`.
import { cpSync, mkdirSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const root = path.dirname(fileURLToPath(import.meta.url)) + '/..';
const dist = path.join(root, 'dist');

const WEIGHTS = ['regular', 'thin', 'light', 'bold', 'fill', 'duotone'];
// @phosphor-icons/web's "exports" map has no "./package.json" subpath, so resolve via a real
// export ("./regular" -> "./src/regular/style.css") and walk up to the package root instead.
const phosphorPkgDir = path.resolve(path.dirname(require.resolve('@phosphor-icons/web/regular')), '..', '..');

// 1. Vendor Phosphor CSS + font files (own directory per weight — filenames collide across weights).
const vendorDir = path.join(dist, 'vendor', 'phosphor');
rmSync(vendorDir, { recursive: true, force: true });
for (const weight of WEIGHTS) {
  cpSync(path.join(phosphorPkgDir, 'src', weight), path.join(vendorDir, weight), { recursive: true });
}

// 2. Copy design tokens.
const tokensDir = path.join(dist, 'tokens');
rmSync(tokensDir, { recursive: true, force: true });
cpSync(path.join(root, 'tokens'), tokensDir, { recursive: true });

// 3. Assemble the self-contained stylesheet: vendored icon CSS first, then tokens.
// All paths are relative to this file, so a plain <link> and a CSS bundler both resolve them
// with no bare-specifier lookup into node_modules.
const styleImports = [
  ...WEIGHTS.map((w) => `@import url("./vendor/phosphor/${w}/style.css");`),
  ...readdirSync(path.join(root, 'tokens'))
    .filter((f) => f.endsWith('.css'))
    .sort()
    .map((f) => `@import url("./tokens/${f}");`),
];
writeFileSync(
  path.join(dist, 'styles.css'),
  `/* arey design system — global entry (built). Vendored icon fonts + tokens, all relative imports. */\n${styleImports.join('\n')}\n`
);

// 4. Copy the hand-authored .d.ts tree (source of truth for types) alongside the compiled JS.
function copyDts(srcDir, destDir) {
  mkdirSync(destDir, { recursive: true });
  for (const entry of readdirSync(srcDir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if (entry.name === 'internal') continue; // not part of the public surface
      copyDts(path.join(srcDir, entry.name), path.join(destDir, entry.name));
    } else if (entry.name.endsWith('.d.ts')) {
      cpSync(path.join(srcDir, entry.name), path.join(destDir, entry.name));
    }
  }
}
copyDts(path.join(root, 'components'), dist);

console.log('dist assets: styles.css, vendor/phosphor, tokens, *.d.ts');
