import { defineConfig } from 'tsup';

export default defineConfig({
  entry: {
    index: 'src/theme/index.ts',
    'adapters/arey/index': 'src/adapters/arey/index.tsx',
  },
  format: ['esm'],
  outDir: 'dist',
  external: ['react', 'react-dom', '@hamsa-designs/arey/react'],
  dts: true,
  clean: true,
  sourcemap: true,
});
