import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// GitHub Pages serves project sites under /<repo-name>/, so every asset
// URL needs that prefix. Local dev (`npm run dev`) still serves from /.
export default defineConfig({
  plugins: [react()],
  base: process.env.GITHUB_ACTIONS ? '/Resume-Screening-Candidate-Ranking/' : '/',
})
