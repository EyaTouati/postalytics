import { useState, useEffect } from "react";
import { Plus, Pencil, UserX, UserCheck, Shield } from "lucide-react";
import api from "../services/api";
import type { User, UserCreate, UserRole } from "../types";

const ROLE_COLORS: Record<UserRole, string> = {
  admin: "bg-red-100 text-red-700",
  responsable: "bg-blue-100 text-blue-700",
  agent_regional: "bg-green-100 text-green-700",
};

const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Administrateur",
  responsable: "Responsable",
  agent_regional: "Agent régional",
};

const REGIONS = ["Tunis","Sfax","Sousse","Bizerte","Gabès","Ariana","Gafsa","Kairouan","Monastir","Nabeul"];

function CreateUserModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState<UserCreate>({
    username: "", email: "", password: "", role: "responsable", region_assignee: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    setError("");
    if (!form.username || !form.email || !form.password) {
      setError("Tous les champs obligatoires doivent être remplis.");
      return;
    }
    if (form.role === "agent_regional" && !form.region_assignee) {
      setError("Un agent régional doit avoir une région assignée.");
      return;
    }
    setLoading(true);
    try {
      await api.post("/users/", {
        ...form,
        region_assignee: form.role === "agent_regional" ? form.region_assignee : null,
      });
      onCreated();
      onClose();
    } catch (e: any) {
      setError(e.response?.data?.detail || "Erreur lors de la création.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 m-4">
        <h2 className="font-display text-xl font-bold text-navy-900 mb-5">Créer un utilisateur</h2>

        {error && (
          <div className="mb-4 bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>
        )}

        <div className="space-y-3">
          {[
            { label: "Nom d'utilisateur", key: "username", type: "text" },
            { label: "Email", key: "email", type: "email" },
            { label: "Mot de passe", key: "password", type: "password" },
          ].map(({ label, key, type }) => (
            <div key={key}>
              <label className="block text-sm font-medium text-navy-700 mb-1">{label}</label>
              <input
                type={type}
                value={(form as any)[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                className="w-full px-3 py-2 border border-surface-muted rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-postal"
              />
            </div>
          ))}

          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Rôle</label>
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })}
              className="w-full px-3 py-2 border border-surface-muted rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-postal"
            >
              <option value="responsable">Responsable décisionnel</option>
              <option value="agent_regional">Agent régional</option>
              <option value="admin">Administrateur</option>
            </select>
          </div>

          {form.role === "agent_regional" && (
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Région assignée</label>
              <select
                value={form.region_assignee}
                onChange={(e) => setForm({ ...form, region_assignee: e.target.value })}
                className="w-full px-3 py-2 border border-surface-muted rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-postal"
              >
                <option value="">— Sélectionner —</option>
                {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          )}
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="flex-1 px-4 py-2 border border-surface-muted rounded-lg text-sm text-navy-700 hover:bg-surface">
            Annuler
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="flex-1 btn-primary text-sm disabled:opacity-50"
          >
            {loading ? "Création…" : "Créer"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchUsers = () => {
    setLoading(true);
    api.get("/users/")
      .then((r) => setUsers(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchUsers(); }, []);

  async function toggleActive(user: User) {
    await api.patch(`/users/${user.id}`, { est_actif: !user.est_actif });
    fetchUsers();
  }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-navy-900">Gestion des utilisateurs</h1>
          <p className="text-sm text-gray-400 mt-0.5">Créer, modifier et désactiver les comptes applicatifs</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2 text-sm">
          <Plus className="w-4 h-4" />
          Nouvel utilisateur
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-surface-muted overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Chargement…</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-surface">
              <tr>
                {["Utilisateur", "Email", "Rôle", "Région", "Statut", "Actions"].map((h) => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-medium text-gray-400 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-muted">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-surface transition-colors">
                  <td className="px-5 py-3 font-medium text-navy-900">{u.username}</td>
                  <td className="px-5 py-3 text-gray-500">{u.email}</td>
                  <td className="px-5 py-3">
                    <span className={`role-badge ${ROLE_COLORS[u.role]}`}>
                      {ROLE_LABELS[u.role]}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-gray-500">{u.region_assignee || "—"}</td>
                  <td className="px-5 py-3">
                    <span className={`role-badge ${u.est_actif ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-400"}`}>
                      {u.est_actif ? "Actif" : "Désactivé"}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <button
                      onClick={() => toggleActive(u)}
                      title={u.est_actif ? "Désactiver" : "Réactiver"}
                      className="text-gray-400 hover:text-navy-700 transition-colors"
                    >
                      {u.est_actif ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && (
        <CreateUserModal onClose={() => setShowCreate(false)} onCreated={fetchUsers} />
      )}
    </div>
  );
}
