import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  publicDir: 'public',
  base: '/safari_writer/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
