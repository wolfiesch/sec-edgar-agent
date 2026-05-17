import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend target: use VITE_BACKEND_URL env var or default to Fly.io
const backendUrl = process.env.VITE_BACKEND_URL || 'https://sec-edgar-agent.fly.dev'
const devApiKey = process.env.DEV_API_KEY || 'sec-api-demo'

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
        headers: {
          // Server-side dev proxy only. Do not expose API keys with VITE_* env vars.
          'X-API-Key': devApiKey,
        },
      }
    }
  }
})
