import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Point at a different backend with VITE_API_PROXY=http://localhost:PORT
      '/api': process.env.VITE_API_PROXY || 'http://localhost:8000',
    },
  },
})
