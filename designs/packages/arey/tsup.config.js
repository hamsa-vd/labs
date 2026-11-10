import { defineConfig } from 'tsup';

export default defineConfig({
  entry: { index: 'components/index.jsx' },
  format: ['esm'],
  outDir: 'dist',
  external: ['react', 'react-dom'],
  clean: true,
  sourcemap: true,
  esbuildOptions(options) {
    options.jsx = 'transform';
  },
});
