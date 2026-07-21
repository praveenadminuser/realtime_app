// The route table. Public routes (login, register) and one protected route (dashboard).
// The nginx/Vite SPA fallback serves index.html for all of these, so a refresh on
// /login works — routing is entirely client-side from here.
import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./components/ProtectedRoute";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      {/* Unknown path → home, which itself redirects to /login if not authed. */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
