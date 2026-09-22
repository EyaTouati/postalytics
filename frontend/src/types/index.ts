// ── Auth & Utilisateurs ─────────────────────────────────────────────────────────

export type UserRole = "admin" | "responsable" | "agent_regional";

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  region_assignee: string | null;
  est_actif: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  role: UserRole;
  region_assignee?: string;
}

export interface UserUpdate {
  email?: string;
  role?: UserRole;
  region_assignee?: string;
  est_actif?: boolean;
}

// ── KPIs Dashboard ──────────────────────────────────────────────────────────────

export interface KPIResume {
  total_colis: number;
  total_ca: number;
  colis_international: number;
  taux_international: number;
  colis_anomalie: number;
}

export interface VolumeParRegion {
  region: string;
  portee: string;
  total_colis: number;
  total_montant: number;
}

export interface RepartitionNature {
  nature: string;
  total: number;
  pourcentage: number;
}

export interface RepartitionService {
  type_service: string;
  total: number;
  pourcentage: number;
  ca_total: number;
}

export interface CAParDestination {
  pays: string;
  portee: string;
  ca_total: number;
  volume: number;
}

export interface EvolutionMensuelle {
  annee: number;
  mois: number;
  label: string;
  volume: number;
  ca: number;
}

// ── Chatbot ─────────────────────────────────────────────────────────────────────

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  answer: string;
  sql_query: string | null;
  sources: string[] | null;
}
