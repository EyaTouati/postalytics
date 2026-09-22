import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Package, Lock, User, AlertCircle } from "lucide-react";
import { useAuthStore } from "../store/authStore";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login, isLoading } = useAuthStore();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await login(username, password);
      navigate("/dashboard");
    } catch {
      setError("Identifiant ou mot de passe incorrect.");
    }
  }

  return (
    <div className="min-h-screen bg-navy-900 flex items-center justify-center p-4">
      {/* Arrière-plan géométrique subtil */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-postal/10" />
        <div className="absolute -bottom-20 -left-20 w-64 h-64 rounded-full bg-amber-postal/10" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo / titre */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-postal mb-4 shadow-lg">
            <Package className="w-8 h-8 text-navy-900" />
          </div>
          <h1 className="font-display text-3xl font-bold text-white tracking-tight">
            PostalBI
          </h1>
          <p
            className="mt-1 text-navy-700 text-sm font-body"
            style={{ color: "#8BA3C4" }}
          >
            La Poste Tunisienne — Plateforme décisionnelle
          </p>
        </div>

        {/* Carte de connexion */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="font-display text-xl font-semibold text-navy-900 mb-6">
            Connexion
          </h2>

          {error && (
            <div className="mb-4 flex items-center gap-2 bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1.5">
                Identifiant
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 border border-surface-muted rounded-lg
                             focus:outline-none focus:ring-2 focus:ring-postal focus:border-transparent
                             text-navy-900 text-sm"
                  placeholder="admin"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1.5">
                Mot de passe
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 border border-surface-muted rounded-lg
                             focus:outline-none focus:ring-2 focus:ring-postal focus:border-transparent
                             text-navy-900 text-sm"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-navy-900 text-white font-display font-semibold py-2.5 rounded-lg
                         hover:bg-navy-700 transition-colors duration-150
                         disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {isLoading ? "Connexion…" : "Se connecter"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
