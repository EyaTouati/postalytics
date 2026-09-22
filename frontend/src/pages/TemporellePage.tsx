import { useState, useEffect } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
} from "recharts";
import api from "../services/api";

const COLORS = ["#2E86AB", "#F0A500", "#1E3A5F", "#10B981"];
const MOIS_FR = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"];

// ── Heatmap component ─────────────────────────────────────────────────────────
function Heatmap({ data, rows, cols }: {
  data: { annee?: number; gouvernorat?: string; valeurs: number[] }[];
  rows: (number | string)[];
  cols: string[];
}) {
  const allVals = data.flatMap(d => d.valeurs).filter(v => v > 0);
  const max = Math.max(...allVals, 1);

  const getColor = (v: number) => {
    if (v === 0) return "#F7F9FC";
    const intensity = v / max;
    if (intensity < 0.25) return "#DBEAFE";
    if (intensity < 0.5)  return "#93C5FD";
    if (intensity < 0.75) return "#2E86AB";
    return "#0A1628";
  };

  const getTextColor = (v: number) => {
    const intensity = v / max;
    return intensity > 0.5 ? "#FFFFFF" : "#1E3A5F";
  };

  const fmt = (n: number) => n >= 1000 ? `${(n/1000).toFixed(0)}k` : `${n}`;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr>
            <th className="text-left p-2 text-gray-400 font-medium w-24">Année</th>
            {cols.map(c => (
              <th key={c} className="p-1 text-center text-gray-500 font-medium">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              <td className="p-2 font-semibold text-navy-900">
                {row.annee || row.gouvernorat}
              </td>
              {row.valeurs.map((v, j) => (
                <td key={j} className="p-0.5">
                  <div
                    className="rounded text-center py-2 px-1 font-medium transition-all cursor-default"
                    style={{
                      backgroundColor: getColor(v),
                      color: getTextColor(v),
                      minWidth: "36px",
                    }}
                    title={`${row.annee || row.gouvernorat} — ${cols[j]} : ${v.toLocaleString()}`}
                  >
                    {v > 0 ? fmt(v) : ""}
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center gap-3 mt-3 text-xs text-gray-400">
        <span>Faible</span>
        {["#DBEAFE","#93C5FD","#2E86AB","#0A1628"].map(c => (
          <div key={c} className="w-8 h-4 rounded" style={{ backgroundColor: c }} />
        ))}
        <span>Élevé</span>
      </div>
    </div>
  );
}

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

// ── Horaires La Poste ─────────────────────────────────────────────────────────
const HORAIRES = {
  hiver: { ouv: 8, ferm: 17, pause_debut: 12, pause_fin: 14.5 },
  ete:   { ouv: 7.5, ferm: 13, pause_debut: null, pause_fin: null },
};

function getBgTranche(tranche: string, mois: number): string {
  const estEte = mois >= 7 && mois <= 8;
  const h = HORAIRES[estEte ? "ete" : "hiver"];
  if (tranche.includes("6h-10h"))   return h.ouv <= 8 ? "#DCFCE7" : "#FEF9C3";
  if (tranche.includes("10h-13h"))  return "#DCFCE7";
  if (tranche.includes("13h-15h"))  return estEte ? "#FEE2E2" : (h.pause_debut ? "#FEF9C3" : "#DCFCE7");
  if (tranche.includes("15h-18h"))  return estEte ? "#FEE2E2" : "#DCFCE7";
  if (tranche.includes("18h-21h"))  return "#FEE2E2";
  return "#F3F4F6";
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function TemporellePage() {
  const [annee, setAnnee] = useState<number | "">("");
  const [heatmap, setHeatmap] = useState<any>(null);
  const [jourSemaine, setJourSemaine] = useState<any[]>([]);
  const [tranches, setTranches] = useState<any[]>([]);
  const [islamique, setIslamique] = useState<any>(null);
  const [mensuelle, setMensuelle] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = annee ? { annee } : {};
    setLoading(true);
    Promise.all([
      api.get("/dashboard/heatmap-mois-annee"),
      api.get("/dashboard/volume-par-jour-semaine", { params }),
      api.get("/dashboard/volume-par-tranche-horaire", { params }),
      api.get("/dashboard/volume-islamique"),
      api.get("/dashboard/evolution-mensuelle", { params }),
    ])
      .then(([h, j, t, i, m]) => {
        setHeatmap(h.data);
        setJourSemaine(j.data);
        setTranches(t.data);
        setIslamique(i.data);
        setMensuelle(m.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [annee]);

  // Conclusions automatiques
  const jourPic = jourSemaine.reduce((a, b) => a.volume > b.volume ? a : b, { jour: "—", volume: 0 });
  const jourCreux = jourSemaine.reduce((a, b) => a.volume < b.volume ? a : b, { jour: "—", volume: Infinity });
  const tranchePic = tranches.reduce((a, b) => a.volume > b.volume ? a : b, { tranche: "—", volume: 0 });

  // Événements islamiques groupés par événement
  const evenementsGroupes = islamique?.par_evenement?.reduce((acc: any, r: any) => {
    if (!acc[r.evenement]) acc[r.evenement] = [];
    acc[r.evenement].push(r);
    return acc;
  }, {}) || {};

  const fmt = (n: number) => n >= 1000 ? `${(n/1000).toFixed(1)}k` : `${n}`;

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
            Analyse Temporelle
          </h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Saisonnalité, jours de la semaine, horaires et calendrier islamique
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

      {/* Conclusions automatiques */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          {
            label: "Jour le plus chargé",
            value: jourPic.jour,
            sub: `${fmt(jourPic.volume)} colis en moyenne`,
            color: "#10B981",
          },
          {
            label: "Jour le moins chargé",
            value: jourCreux.volume === Infinity ? "—" : jourCreux.jour,
            sub: jourCreux.volume === Infinity ? "" : `${fmt(jourCreux.volume)} colis`,
            color: "#EF4444",
          },
          {
            label: "Tranche horaire de pointe",
            value: tranchePic.tranche.split("(")[1]?.replace(")", "") || tranchePic.tranche,
            sub: `${fmt(tranchePic.volume)} colis déposés`,
            color: "#F0A500",
          },
        ].map((item, i) => (
          <div key={i} className="bg-white rounded-xl border border-surface-muted p-4">
            <div className="h-1 rounded mb-3" style={{ backgroundColor: item.color }} />
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{item.label}</p>
            <p className="font-display text-xl font-bold text-navy-900">{item.value}</p>
            <p className="text-xs text-gray-400 mt-1">{item.sub}</p>
          </div>
        ))}
      </div>

      {/* Section 1 — Heatmap mois × année */}
      <div>
        <SectionTitle
          title="Heatmap saisonnière — Volume par mois et par année"
          sub="Plus la couleur est foncée, plus le volume est élevé"
        />
        <Card>
          {heatmap && (
            <Heatmap
              data={heatmap.data}
              rows={heatmap.annees}
              cols={MOIS_FR}
            />
          )}
        </Card>
      </div>

      {/* Section 2 — Évolution mensuelle */}
      <div>
        <SectionTitle
          title="Évolution mensuelle détaillée"
          sub={annee ? `Année ${annee}` : "Toutes les années superposées"}
        />
        <Card>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={(() => {
              const annees = [...new Set(mensuelle.map(d => d.annee))].sort();
              return MOIS_FR.map((label, i) => {
                const row: any = { mois: label };
                annees.forEach(an => {
                  const found = mensuelle.find(d => d.annee === an && d.mois === i + 1);
                  row[`${an}`] = found?.volume || 0;
                });
                return row;
              });
            })()}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
              <XAxis dataKey="mois" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
              <Tooltip formatter={(v: number) => [fmt(v), "Colis"]} />
              <Legend />
              {[...new Set(mensuelle.map(d => d.annee))].sort().map((an, i) => (
                <Line
                  key={an}
                  type="monotone"
                  dataKey={`${an}`}
                  stroke={COLORS[i % COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  name={`${an}`}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Section 3 — Jour de la semaine */}
      <div>
        <SectionTitle
          title="Volume par jour de la semaine"
          sub="Lundi = accumulation weekend — Vendredi = baisse avant weekend"
        />
        <Card>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={jourSemaine}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
              <XAxis dataKey="jour" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
              <Tooltip
                formatter={(v: number, name: string) => [fmt(v), "Colis"]}
                labelFormatter={(l) => `${l}`}
              />
              <Bar dataKey="volume" radius={[4, 4, 0, 0]} name="Volume">
                {jourSemaine.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={
                      entry.jour === jourPic.jour ? "#F0A500" :
                      entry.jour === "Samedi" || entry.jour === "Dimanche"
                        ? "#E8EDF4" : "#2E86AB"
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-3 text-xs">
            <span className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-amber-postal" />
              Jour de pointe
            </span>
            <span className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-postal" />
              Jours ouvrables
            </span>
            <span className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-surface-muted" />
              Weekend
            </span>
          </div>
        </Card>
      </div>

      {/* Section 4 — Tranches horaires */}
      <div>
        <SectionTitle
          title="Répartition horaire des dépôts (colis normaux)"
          sub="Zones vertes = bureaux ouverts | Zones rouges = hors horaires"
        />
        <Card>
          <div className="space-y-3">
            {/* Légende horaires */}
            <div className="flex flex-wrap gap-3 mb-4 text-xs">
              <div className="flex items-center gap-1.5 bg-green-50 px-2 py-1 rounded">
                <div className="w-2 h-2 rounded-full bg-green-400" />
                Bureaux ouverts (hiver : 8h-12h / 14h30-17h)
              </div>
              <div className="flex items-center gap-1.5 bg-yellow-50 px-2 py-1 rounded">
                <div className="w-2 h-2 rounded-full bg-yellow-400" />
                Pause déjeuner (12h-14h30)
              </div>
              <div className="flex items-center gap-1.5 bg-red-50 px-2 py-1 rounded">
                <div className="w-2 h-2 rounded-full bg-red-400" />
                Hors horaires
              </div>
            </div>

            {tranches.map((t, i) => {
              const bg = getBgTranche(t.tranche, annee ? parseInt(annee.toString()) : 6);
              return (
                <div key={i} className="rounded-lg p-3" style={{ backgroundColor: bg }}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium text-navy-900">{t.tranche}</span>
                    <div className="text-right">
                      <span className="font-bold text-navy-900">{fmt(t.volume)}</span>
                      <span className="text-gray-500 ml-2 text-xs">{t.pourcentage}%</span>
                    </div>
                  </div>
                  <div className="h-2 bg-white/50 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full bg-postal transition-all"
                      style={{ width: `${t.pourcentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Section 5 — Calendrier islamique */}
      <div>
        <SectionTitle
          title="Impact du calendrier islamique sur les flux"
          sub="Analyse Ramadan, Aïd el-Fitr, Aïd el-Adha par année"
        />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* Par événement */}
          <Card>
            <h3 className="font-display font-semibold text-navy-900 mb-4 text-sm">
              Volume par événement islamique
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={Object.entries(evenementsGroupes).map(([ev, rows]: any) => ({
                  evenement: ev.length > 20 ? ev.substring(0, 18) + "…" : ev,
                  evenement_full: ev,
                  volume: rows.reduce((s: number, r: any) => s + r.volume, 0),
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                <XAxis dataKey="evenement" tick={{ fontSize: 9 }} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={fmt} />
                <Tooltip
                  formatter={(v: number) => [fmt(v), "Colis"]}
                  labelFormatter={(l: string, payload: any) =>
                    payload?.[0]?.payload?.evenement_full || l
                  }
                />
                <Bar dataKey="volume" radius={[4, 4, 0, 0]}>
                  {Object.keys(evenementsGroupes).map((ev, i) => (
                    <Cell
                      key={i}
                      fill={
                        ev.includes("Aïd") ? "#F0A500" :
                        ev.includes("Ramadan") ? "#2E86AB" :
                        ev.includes("Pré") ? "#10B981" :
                        "#8B5CF6"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Par mois islamique */}
          <Card>
            <h3 className="font-display font-semibold text-navy-900 mb-4 text-sm">
              Volume par mois islamique
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={islamique?.par_mois || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                <XAxis
                  dataKey="mois"
                  tick={{ fontSize: 8 }}
                  angle={-30}
                  textAnchor="end"
                  height={50}
                />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={fmt} />
                <Tooltip formatter={(v: number) => [fmt(v), "Colis"]} />
                <Bar dataKey="volume" fill="#2E86AB" radius={[3, 3, 0, 0]}>
                  {(islamique?.par_mois || []).map((r: any, i: number) => (
                    <Cell
                      key={i}
                      fill={
                        r.mois === "Ramadan" ? "#2E86AB" :
                        r.mois === "Chawwal" ? "#F0A500" :
                        r.mois === "Dhou al-Hijja" ? "#8B5CF6" :
                        "#1E3A5F"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="flex flex-wrap gap-2 mt-3 text-xs">
              {[
                { label: "Ramadan", color: "#2E86AB" },
                { label: "Chawwal (Aïd Fitr)", color: "#F0A500" },
                { label: "Dhou al-Hijja (Aïd Adha)", color: "#8B5CF6" },
                { label: "Autres mois", color: "#1E3A5F" },
              ].map(l => (
                <span key={l.label} className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: l.color }} />
                  {l.label}
                </span>
              ))}
            </div>
          </Card>
        </div>
      </div>

    </div>
  );
}