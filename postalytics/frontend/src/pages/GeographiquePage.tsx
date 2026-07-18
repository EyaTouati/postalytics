import { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell,
} from "recharts";
import { AlertTriangle, CheckCircle } from "lucide-react";
import api from "../services/api";

const COLORS = ["#2E86AB", "#F0A500", "#1E3A5F", "#10B981", "#8B5CF6", "#F97316"];

const fmt = (n: number) => n >= 1000 ? `${(n/1000).toFixed(1)}k` : `${n}`;

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-surface-muted p-5 ${className}`}>
      {children}
    </div>
  );
}

function SectionTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="mb-4">
      <h2 className="font-display text-lg font-semibold text-navy-900">{title}</h2>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

// ── Heatmap Région × Mois ─────────────────────────────────────────────────────
function HeatmapRegionMois({ data, gouvernorats, mois }: {
  data: { gouvernorat: string; valeurs: number[]; total: number }[];
  gouvernorats: string[];
  mois: string[];
}) {
  const allVals = data.flatMap(d => d.valeurs).filter(v => v > 0);
  const max = Math.max(...allVals, 1);

  const getColor = (v: number) => {
    if (v === 0) return "#F7F9FC";
    const p = v / max;
    if (p < 0.2)  return "#DBEAFE";
    if (p < 0.4)  return "#93C5FD";
    if (p < 0.6)  return "#3B82F6";
    if (p < 0.8)  return "#2E86AB";
    return "#0A1628";
  };

  const getTextColor = (v: number) => v / max > 0.5 ? "#fff" : "#1E3A5F";

  return (
    <div className="overflow-x-auto">
      <table className="text-xs border-collapse w-full">
        <thead>
          <tr>
            <th className="text-left p-2 text-gray-400 font-medium w-32">Gouvernorat</th>
            {mois.map(m => (
              <th key={m} className="p-1 text-center text-gray-400 font-medium">{m}</th>
            ))}
            <th className="p-1 text-center text-gray-400 font-medium">Total</th>
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 20).map((row, i) => (
            <tr key={i}>
              <td className="p-1.5 font-medium text-navy-900 truncate max-w-[120px]">
                {row.gouvernorat}
              </td>
              {row.valeurs.map((v, j) => (
                <td key={j} className="p-0.5">
                  <div
                    className="rounded text-center py-1.5 font-medium"
                    style={{
                      backgroundColor: getColor(v),
                      color: getTextColor(v),
                      minWidth: "32px",
                    }}
                    title={`${row.gouvernorat} — ${mois[j]} : ${v.toLocaleString()}`}
                  >
                    {v > 0 ? fmt(v) : ""}
                  </div>
                </td>
              ))}
              <td className="p-1 text-center font-bold text-navy-900">
                {fmt(row.total)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center gap-2 mt-3 text-xs text-gray-400">
        <span>Faible</span>
        {["#DBEAFE","#93C5FD","#3B82F6","#2E86AB","#0A1628"].map(c => (
          <div key={c} className="w-8 h-3 rounded" style={{ backgroundColor: c }} />
        ))}
        <span>Élevé</span>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function GeographiquePage() {
  const [annee, setAnnee] = useState<number | "">("");
  const [gouvernorats, setGouvernorats] = useState<any[]>([]);
  const [bureaux, setBureaux] = useState<any[]>([]);
  const [heatmap, setHeatmap] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = annee ? { annee } : {};
    setLoading(true);
    Promise.all([
      api.get("/dashboard/volume-par-gouvernorat", { params }),
      api.get("/dashboard/pression-bureaux", { params: { ...params, top: 20 } }),
      api.get("/dashboard/heatmap-region-mois", { params }),
    ])
      .then(([g, b, h]) => {
        setGouvernorats(g.data);
        setBureaux(b.data);
        setHeatmap(h.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [annee]);

  // Agréger gouvernorats (national + international)
  const gouvernoratsAgg = Object.values(
    gouvernorats.reduce((acc: any, r: any) => {
      if (!acc[r.gouvernorat]) {
        acc[r.gouvernorat] = { gouvernorat: r.gouvernorat, total: 0, national: 0, international: 0, ca: 0 };
      }
      acc[r.gouvernorat].total += r.volume;
      acc[r.gouvernorat].ca += r.ca;
      if (r.portee === "National") acc[r.gouvernorat].national += r.volume;
      else acc[r.gouvernorat].international += r.volume;
      return acc;
    }, {})
  ).sort((a: any, b: any) => b.total - a.total);

  const bureauxSurcharges = bureaux.filter((b: any) => b.surcharge);
  const bureauxNormaux = bureaux.filter((b: any) => !b.surcharge);

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <p className="text-gray-400 text-sm">Chargement…</p>
    </div>
  );

  return (
    <div className="p-6 space-y-8">

      {/* En-tête */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-navy-900">
            Analyse Géographique
          </h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Gouvernorats, bureaux, pression de travail et flux régionaux
          </p>
        </div>
        <select
          value={annee}
          onChange={e => setAnnee(e.target.value ? parseInt(e.target.value) : "")}
          className="text-sm border border-surface-muted rounded-lg px-3 py-2 bg-white
                     text-navy-900 focus:outline-none focus:ring-2 focus:ring-postal"
        >
          <option value="">Toutes les années</option>
          {[2023,2024,2025,2026].map(a => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
      </div>

      {/* Résumé pression */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <span className="font-semibold text-red-700 text-sm">Bureaux surchargés</span>
          </div>
          <p className="text-2xl font-display font-bold text-red-700">
            {bureauxSurcharges.length}
          </p>
          <p className="text-xs text-red-500 mt-1">
            Plus de 1.5× la moyenne journalière
          </p>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="font-semibold text-green-700 text-sm">Bureaux normaux</span>
          </div>
          <p className="text-2xl font-display font-bold text-green-700">
            {bureauxNormaux.length}
          </p>
          <p className="text-xs text-green-500 mt-1">Charge dans la moyenne</p>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-semibold text-blue-700 text-sm">
              Bureau le plus actif
            </span>
          </div>
          <p className="text-lg font-display font-bold text-blue-700">
            {bureaux[0]?.bureau || "—"}
          </p>
          <p className="text-xs text-blue-500 mt-1">
            {bureaux[0] ? `${bureaux[0].colis_par_jour} colis/jour — ${bureaux[0].gouvernorat}` : ""}
          </p>
        </div>
      </div>

      {/* Section 1 — Volume par gouvernorat */}
      <div>
        <SectionTitle
          title="Volume par gouvernorat — National vs International"
          sub="Comparaison des flux expéditeurs par région"
        />
        <Card>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={(gouvernoratsAgg as any[]).slice(0, 15)}
              layout="vertical"
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
              <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={fmt} />
              <YAxis
                type="category"
                dataKey="gouvernorat"
                tick={{ fontSize: 10 }}
                width={100}
              />
              <Tooltip
                formatter={(v: number, name: string) => [fmt(v), name]}
              />
              <Legend />
              <Bar dataKey="national" stackId="a" fill="#2E86AB" name="National" />
              <Bar
                dataKey="international"
                stackId="a"
                fill="#F0A500"
                name="International"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Section 2 — Heatmap Région × Mois */}
      <div>
        <SectionTitle
          title="Carte de chaleur — Région × Mois"
          sub="Identifier les pics saisonniers par gouvernorat (ex: Sud en oct-nov pour les dattes)"
        />
        <Card>
          {heatmap && (
            <HeatmapRegionMois
              data={heatmap.data}
              gouvernorats={heatmap.gouvernorats}
              mois={heatmap.mois}
            />
          )}
        </Card>
      </div>

      {/* Section 3 — Pression des bureaux */}
      <div>
        <SectionTitle
          title="Pression des bureaux — Top 20"
          sub="Colis traités par jour ouvrable — rouge = surcharge (> 1.5× la moyenne)"
        />
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface">
                <tr>
                  {["Bureau","Ville","Gouvernorat","Type","Volume total","Jours actifs","Colis/jour","Statut"].map(h => (
                    <th key={h}
                        className="text-left px-3 py-2.5 text-xs font-medium text-gray-400 uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-muted">
                {bureaux.map((b: any, i: number) => (
                  <tr key={i} className={`hover:bg-surface transition-colors ${b.surcharge ? "bg-red-50" : ""}`}>
                    <td className="px-3 py-2.5 font-mono text-xs text-navy-900">{b.bureau}</td>
                    <td className="px-3 py-2.5 text-navy-700">{b.ville}</td>
                    <td className="px-3 py-2.5 text-gray-500">{b.gouvernorat}</td>
                    <td className="px-3 py-2.5">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        b.type === "Agence"
                          ? "bg-purple-100 text-purple-700"
                          : "bg-blue-100 text-blue-700"
                      }`}>
                        {b.type || "Bureau"}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 font-medium text-navy-900">
                      {b.volume_total.toLocaleString()}
                    </td>
                    <td className="px-3 py-2.5 text-gray-500">{b.jours_actifs}</td>
                    <td className="px-3 py-2.5 font-bold"
                        style={{ color: b.surcharge ? "#EF4444" : "#10B981" }}>
                      {b.colis_par_jour}
                    </td>
                    <td className="px-3 py-2.5">
                      {b.surcharge ? (
                        <span className="flex items-center gap-1 text-xs text-red-600 font-medium">
                          <AlertTriangle className="w-3 h-3" /> Surchargé
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
                          <CheckCircle className="w-3 h-3" /> Normal
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

    </div>
  );
}