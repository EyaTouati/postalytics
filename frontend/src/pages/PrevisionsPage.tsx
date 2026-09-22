import { useState, useEffect } from "react";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area,
} from "recharts";
import { TrendingUp, AlertCircle, CheckCircle, Calendar } from "lucide-react";
import api from "../services/api";

const fmt = (n: number | null | undefined) => {
  if (n == null) return "—";
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return `${n}`;
};

function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-surface-muted p-5 ${className}`}
    >
      {children}
    </div>
  );
}

export default function PrevisionsPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/dashboard/previsions")
      .then((r) => {
        if (r.data.error) {
          setError(r.data.error);
        } else {
          setData(r.data);
        }
      })
      .catch(() => setError("Erreur de chargement des prévisions"))
      .finally(() => setLoading(false));
  }, []);

  // Séparer historique et prévisions
  const historique = data.filter((d) => !d.est_prevision);
  const previsions = data.filter((d) => d.est_prevision);

  // Trouver le pivot (premier mois de prévision)
  const pivotLabel = previsions[0]?.label || null;

  // KPIs prévisions
  const prevMax = previsions.reduce(
    (a, b) => ((b.volume_prevu || 0) > (a.volume_prevu || 0) ? b : a),
    {},
  );
  const prevMin = previsions.reduce(
    (a, b) =>
      (b.volume_prevu || Infinity) < (a.volume_prevu || Infinity) ? b : a,
    {},
  );
  const totalPrevu = previsions.reduce((s, d) => s + (d.volume_prevu || 0), 0);

  // Données graphique — derniers 12 mois + 6 prévisions
  const derniers12 = historique.slice(-12);
  const chartData = [
    ...derniers12.map((d) => ({
      label: d.label,
      volume_reel: d.volume_reel,
      volume_prevu: null,
      borne_inf: null,
      borne_sup: null,
      est_prevision: false,
    })),
    ...previsions.map((d) => ({
      label: d.label,
      volume_reel: null,
      volume_prevu: d.volume_prevu,
      borne_inf: d.borne_inf,
      borne_sup: d.borne_sup,
      est_prevision: true,
    })),
  ];

  if (loading)
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-400 text-sm">Chargement des prévisions…</p>
      </div>
    );

  return (
    <div className="p-6 space-y-6">
      {/* En-tête */}
      <div>
        <h1 className="font-display text-2xl font-bold text-navy-900">
          Prévisions de volumes
        </h1>
        <p className="text-sm text-gray-400 mt-0.5">
          Modèle Prophet — saisonnalité islamique et grégoriennes intégrées
        </p>
      </div>

      {/* Erreur */}
      {error && (
        <div
          className="flex items-center gap-3 bg-amber-50 border border-amber-200
                        rounded-xl px-5 py-4"
        >
          <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0" />
          <p className="text-sm text-amber-800">{error}</p>
        </div>
      )}

      {!error && (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                icon: TrendingUp,
                label: "Total prévu (6 mois)",
                value: fmt(totalPrevu),
                color: "#2E86AB",
              },
              {
                icon: Calendar,
                label: "Mois le plus chargé",
                value: prevMax.label || "—",
                sub: fmt(prevMax.volume_prevu) + " colis",
                color: "#F0A500",
              },
              {
                icon: Calendar,
                label: "Mois le plus creux",
                value: prevMin.label || "—",
                sub: fmt(prevMin.volume_prevu) + " colis",
                color: "#8B5CF6",
              },
              {
                icon: CheckCircle,
                label: "MAE modèle",
                value: "430 colis/j",
                sub: "MAPE : 39.4%",
                color: "#10B981",
              },
            ].map((k, i) => (
              <div
                key={i}
                className="bg-white rounded-xl border border-surface-muted overflow-hidden"
              >
                <div className="h-1" style={{ backgroundColor: k.color }} />
                <div className="p-4 flex items-start gap-3">
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ backgroundColor: `${k.color}15` }}
                  >
                    <k.icon className="w-4 h-4" style={{ color: k.color }} />
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wide">
                      {k.label}
                    </p>
                    <p className="font-display text-lg font-bold text-navy-900">
                      {k.value}
                    </p>
                    {k.sub && <p className="text-xs text-gray-400">{k.sub}</p>}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Graphique principal */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-navy-900">
                Historique (12 mois) + Prévisions Prophet (6 mois)
              </h2>
              <div className="flex items-center gap-4 text-xs text-gray-400">
                <span className="flex items-center gap-1.5">
                  <div className="w-4 h-3 bg-postal rounded" />
                  Réel
                </span>
                <span className="flex items-center gap-1.5">
                  <div className="w-4 h-3 bg-amber-postal rounded" />
                  Prévision
                </span>
                <span className="flex items-center gap-1.5">
                  <div className="w-4 h-2 bg-amber-postal opacity-30 rounded" />
                  Intervalle 95%
                </span>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={340}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 10 }}
                  angle={-30}
                  textAnchor="end"
                  height={50}
                />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
                <Tooltip
                  formatter={(v: any, name: string) => {
                    if (v == null) return [null, name];
                    const labels: Record<string, string> = {
                      volume_reel: "Volume réel",
                      volume_prevu: "Volume prévu",
                      borne_sup: "Borne supérieure",
                      borne_inf: "Borne inférieure",
                    };
                    return [fmt(v), labels[name] || name];
                  }}
                />
                {pivotLabel && (
                  <ReferenceLine
                    x={pivotLabel}
                    stroke="#EF4444"
                    strokeDasharray="4 4"
                    label={{
                      value: "→ Prévisions",
                      position: "top",
                      fontSize: 10,
                      fill: "#EF4444",
                    }}
                  />
                )}
                {/* Intervalle confiance */}
                <Area
                  type="monotone"
                  dataKey="borne_sup"
                  fill="#F0A500"
                  stroke="none"
                  fillOpacity={0.15}
                  connectNulls
                />
                <Area
                  type="monotone"
                  dataKey="borne_inf"
                  fill="#ffffff"
                  stroke="none"
                  fillOpacity={1}
                  connectNulls
                />
                {/* Barres historique */}
                <Bar
                  dataKey="volume_reel"
                  fill="#2E86AB"
                  name="volume_reel"
                  radius={[3, 3, 0, 0]}
                />
                {/* Barres prévisions */}
                <Bar
                  dataKey="volume_prevu"
                  fill="#F0A500"
                  name="volume_prevu"
                  radius={[3, 3, 0, 0]}
                  opacity={0.85}
                />
                {/* Lignes bornes */}
                <Line
                  type="monotone"
                  dataKey="borne_sup"
                  stroke="#F0A500"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  dot={false}
                  connectNulls
                  name="borne_sup"
                />
                <Line
                  type="monotone"
                  dataKey="borne_inf"
                  stroke="#F0A500"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  dot={false}
                  connectNulls
                  name="borne_inf"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>

          {/* Tableau des prévisions */}
          <Card>
            <h2 className="font-display font-semibold text-navy-900 mb-4">
              Détail des prévisions mensuelles
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-surface">
                  <tr>
                    {[
                      "Période",
                      "Volume prévu",
                      "Borne inférieure",
                      "Borne supérieure",
                      "Intervalle ±",
                    ].map((h) => (
                      <th
                        key={h}
                        className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-muted">
                  {previsions.map((d, i) => (
                    <tr key={i} className="hover:bg-surface">
                      <td className="px-4 py-3 font-medium text-navy-900">
                        {d.label}
                      </td>
                      <td className="px-4 py-3 font-bold text-amber-postal">
                        {fmt(d.volume_prevu)}
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {fmt(d.borne_inf)}
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {fmt(d.borne_sup)}
                      </td>
                      <td className="px-4 py-3 text-gray-400">
                        ±{" "}
                        {fmt(
                          Math.round(
                            ((d.borne_sup || 0) - (d.borne_inf || 0)) / 2,
                          ),
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Infos modèle */}
          <Card>
            <h2 className="font-display font-semibold text-navy-900 mb-3">
              À propos du modèle
            </h2>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
              {[
                { label: "Algorithme", value: "Facebook Prophet" },
                { label: "Données", value: "2023 → 2026" },
                {
                  label: "Saisonnalités",
                  value: "Annuelle + Hebdo + Mensuelle",
                },
                { label: "Événements", value: "Islamiques + Fériés TN" },
                { label: "Mode", value: "Multiplicatif" },
                { label: "Horizon", value: "6 mois" },
                { label: "Intervalle conf.", value: "95%" },
                { label: "Validation", value: "Cross-validation 90j" },
              ].map((item, i) => (
                <div key={i} className="bg-surface rounded-lg p-3">
                  <p className="text-xs text-gray-400 mb-1">{item.label}</p>
                  <p className="font-medium text-navy-900">{item.value}</p>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
