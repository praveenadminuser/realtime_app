import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Dev server config. In the cluster none of this runs — nginx serves the built
// files and does the proxying (see nginx.conf). This block only shapes `npm run dev`.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // The browser calls /api/users; this forwards it to the FastAPI backend on
      // :8000. Same-origin from the browser's point of view, so no CORS.
      //
      // rewrite strips the /api prefix because the backend mounts its routes at the
      // root (/users, /health), not under /api. nginx does the identical strip in
      // the cluster, so dev and prod behave the same.
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});