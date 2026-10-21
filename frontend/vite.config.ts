import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5171,
    strictPort: true,
    allowedHosts: true,
    cors: true,
    hmr: {
      clientPort: 5171,
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8011',
        changeOrigin: true,
      },
    },
  },
})
