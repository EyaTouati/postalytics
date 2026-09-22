/**
 * Store Zustand — état d'authentification global.
 * Persiste le token dans localStorage pour survivre aux rechargements.
 */
import { create } from "zustand";
import api from "../services/api";
import type { User } from "../types";

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem("access_token"),
  isLoading: false,

  login: async (username, password) => {
    set({ isLoading: true });
    try {
      const { data } = await api.post("/auth/login", { username, password });
      localStorage.setItem("access_token", data.access_token);
      set({ token: data.access_token, user: data.user, isLoading: false });
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem("access_token");
    set({ user: null, token: null });
    window.location.href = "/login";
  },

  fetchMe: async () => {
    try {
      const { data } = await api.get("/auth/me");
      set({ user: data });
    } catch {
      // Token invalide — nettoyer
      localStorage.removeItem("access_token");
      set({ user: null, token: null });
    }
  },
}));
