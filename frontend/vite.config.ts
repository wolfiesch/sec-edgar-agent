import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend target: use VITE_BACKEND_URL env var or default to Fly.io
const backendUrl = process.env.VITE_BACKEND_URL || 'https://sec-edgar-agent.fly.dev'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
        ws: true,
        secure: true,
      }
    }
  }
})
