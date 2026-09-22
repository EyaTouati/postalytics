import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./index.css";
import TemporellePage from "./pages/TemporellePage";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ChatbotPage from "./pages/ChatbotPage";
import PrevisionsPage from "./pages/PrevisionsPage";
import AdminUsersPage from "./pages/AdminUsersPage";
import AppLayout from "./components/layout/AppLayout";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import GeographiquePage from "./pages/GeographiquePage";
import CroiséesPage from "./pages/CroiséesPage";
import DestinationsPage from "./pages/DestinationsPage";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* Routes protégées */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/previsions" element={<PrevisionsPage />} />
            <Route path="/chatbot" element={<ChatbotPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
          </Route>
        </Route>

        {/* Redirection racine */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />

        <Route path="/temporelle" element={<TemporellePage />} />
        <Route path="/geographique" element={<GeographiquePage />} />
        <Route path="/croisees" element={<CroiséesPage />} />
        <Route path="/destinations" element={<DestinationsPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
