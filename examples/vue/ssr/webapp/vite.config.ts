import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig(({ isSsrBuild }) => ({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    manifest: isSsrBuild ? false : 'manifest.json',
    outDir: isSsrBuild ? 'dist/ssr' : 'dist/client',
    rollupOptions: {
      input: isSsrBuild ? 'src/ssr.ts' : 'src/main.ts'
    }
  },
}))
