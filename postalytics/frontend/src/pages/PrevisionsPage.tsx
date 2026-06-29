import { TrendingUp, FlaskConical } from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";

// Données mock de prévision (seront remplacées par les sorties Prophet/statsmodels)
const MOCK_DATA = [
  { label: "Jan 2024", volume: 220, est_prevision: false },
  { label: "Fév 2024", volume: 195, est_prevision: false },
  { label: "Mar 2024", volume: 260, est_prevision: false },
  { label: "Avr 2024", volume: 240, est_prevision: false },
  { label: "Mai 2024", volume: 275, est_prevision: false },
  { label: "Jun 2024", volume: 310, est_prevision: false },
  { label: "Jul 2024", volume: 350, est_prevision: false },
  { label: "Aoû 2024", volume: 345, est_prevision: false },
  { label: "Sep 2024", volume: 290, est_prevision: false },
  { label: "Oct 2024", volume: 305, est_prevision: false },
  { label: "Nov 2024", volume: 410, est_prevision: false },
  { label: "Déc 2024", volume: 480, est_prevision: false },
  // Prévisions (en pointillés visuellement)
  { label: "Jan 2025", volume_prevu: 340, borne_inf: 295, borne_sup: 385, est_prevision: true },
  { label: "Fév 2025", volume_prevu: 310, borne_inf: 265, borne_sup: 355, est_prevision: true },
  { label: "Mar 2025", volume_prevu: 375, borne_inf: 320, borne_sup: 430, est_prevision: true },
  { label: "Avr 2025", volume_prevu: 350, borne_inf: 295, borne_sup: 405, est_prevision: true },
  { label: "Mai 2025", volume_prevu: 395, borne_inf: 335, borne_sup: 455, est_prevision: true },
  { label: "Jun 2025", volume_prevu: 430, borne_inf: 365, borne_sup: 495, est_prevision: true },
];

export default function PrevisionsPage() {
  const pivot = MOCK_DATA.findIndex((d) => d.est_prevision);
  const pivotLabel = pivot >= 0 ? MOCK_DATA[pivot].label : null;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-navy-900">Prévisions de volume</h1>
        <p className="text-sm text-gray-400 mt-0.5">Phase 3 — Modèles Prophet / statsmodels</p>
      </div>

      {/* Bannière Phase 3 */}
      <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-5 py-4">
        <FlaskConical className="w-5 h-5 text-amber-postal flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-amber-800">Données de démonstration</p>
          <p className="text-xs text-amber-700 mt-0.5">
            Les prévisions affichées sont générées à partir de données fictives.
            Une fois les modèles ML entraînés sur les vraies données (Phase 3),
            cet endpoint sera mis à jour — aucune modification côté frontend nécessaire.
          </p>
        </div>
      </div>

      {/* Graphique prévisions */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-surface-muted">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display font-semibold text-navy-900">Évolution et prévisions 6 mois</h2>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1.5">
              <span className="w-6 h-0.5 bg-postal inline-block" />
              Historique réel
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-6 border-t-2 border-dashed border-amber-postal inline-block" />
              Prévision
            </span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={MOCK_DATA} margin={{ top: 5, right: 30, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
            <XAxis dataKey="label" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            {pivotLabel && (
              <ReferenceLine
                x={pivotLabel}
                stroke="#F0A500"
                strokeDasharray="4 4"
                label={{ value: "Prévisions →", position: "top", fontSize: 10, fill: "#C88400" }}
              />
            )}
            <Line
              type="monotone"
              dataKey="volume"
              stroke="#2E86AB"
              strokeWidth={2}
              dot={false}
              name="Volume réel"
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="volume_prevu"
              stroke="#F0A500"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="Volume prévu"
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="borne_sup"
              stroke="#F0A500"
              strokeWidth={1}
              strokeDasharray="2 4"
              dot={false}
              name="Borne sup."
              opacity={0.5}
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="borne_inf"
              stroke="#F0A500"
              strokeWidth={1}
              strokeDasharray="2 4"
              dot={false}
              name="Borne inf."
              opacity={0.5}
              connectNulls
            />
            <Legend />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Table des prévisions */}
      <div className="bg-white rounded-xl shadow-sm border border-surface-muted overflow-hidden">
        <div className="px-5 py-4 border-b border-surface-muted">
          <h2 className="font-display font-semibold text-navy-900">Détail des prévisions</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface">
              <tr>
                {["Période", "Volume prévu", "Borne inférieure", "Borne supérieure", "Intervalle"].map((h) => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-medium text-gray-400 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-muted">
              {MOCK_DATA.filter((d) => d.est_prevision).map((d) => (
                <tr key={d.label} className="hover:bg-surface transition-colors">
                  <td className="px-5 py-3 font-medium text-navy-900">{d.label}</td>
                  <td className="px-5 py-3 text-postal font-semibold">{d.volume_prevu}</td>
                  <td className="px-5 py-3 text-gray-500">{d.borne_inf}</td>
                  <td className="px-5 py-3 text-gray-500">{d.borne_sup}</td>
                  <td className="px-5 py-3 text-gray-400">
                    ± {Math.round(((d.borne_sup! - d.borne_inf!) / 2))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
