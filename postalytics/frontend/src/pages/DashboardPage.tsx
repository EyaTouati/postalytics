import { useState, useEffect } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Package, TrendingUp, Globe, AlertTriangle, DollarSign } from "lucide-react";
import api from "../services/api";
import { useAuthStore } from "../store/authStore";
import type {
  KPIResume, VolumeParRegion, RepartitionNature,
  RepartitionService, EvolutionMensuelle, CAParDestination,
} from "../types";

// Palette graphiques
const COLORS = ["#2E86AB", "#F0A500", "#1E3A5F", "#5BA3C0", "#C88400", "#0A1628"];

function KPICard({ icon: Icon, label, value, sub, accent = false }: {
  icon: React.ElementType; label: string; value: string | number; sub?: string; accent?: boolean;
}) {
  return (
    <div className="kpi-card p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">{label}</p>
          <p className={`font-display text-2xl font-bold ${accent ? "text-amber-postal" : "text-navy-900"}`}>
            {value}
          </p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-surface flex items-center justify-center">
          <Icon className="w-5 h-5 text-postal" />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [annee, setAnnee] = useState<number | undefined>(2024);
  const [resume, setResume] = useState<KPIResume | null>(null);
  const [volumeRegion, setVolumeRegion] = useState<VolumeParRegion[]>([]);
  const [nature, setNature] = useState<RepartitionNature[]>([]);
  const [services, setServices] = useState<RepartitionService[]>([]);
  const [evolution, setEvolution] = useState<EvolutionMensuelle[]>([]);
  const [caDestination, setCaDestination] = useState<CAParDestination[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = annee ? { annee } : {};
    setLoading(true);
    Promise.all([
      api.get("/dashboard/resume", { params }),
      api.get("/dashboard/volume-par-region", { params }),
      api.get("/dashboard/repartition-nature", { params }),
      api.get("/dashboard/repartition-service", { params }),
      api.get("/dashboard/evolution-mensuelle", { params }),
      api.get("/dashboard/ca-par-destination", { params: { ...params, top: 8 } }),
    ])
      .then(([r, v, n, s, e, c]) => {
        setResume(r.data);
        setVolumeRegion(v.data);
        setNature(n.data);
        setServices(s.data);
        setEvolution(e.data);
        setCaDestination(c.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [annee]);

  // Agréger volume par région (national + international cumulé)
  const volumeBarData = Object.values(
    volumeRegion.reduce<Record<string, { region: string; National: number; International: number }>>(
      (acc, row) => {
        if (!acc[row.region]) acc[row.region] = { region: row.region, National: 0, International: 0 };
        acc[row.region][row.portee as "National" | "International"] = row.total_colis;
        return acc;
      },
      {}
    )
  );

  const fmt = (n: number) =>
    n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n.toString();

  const fmtDT = (n: number) =>
    new Intl.NumberFormat("fr-TN", { style: "currency", currency: "TND", maximumFractionDigits: 0 }).format(n);

  return (
    <div className="p-6 space-y-6">
      {/* ── En-tête ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-navy-900">Tableau de bord</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {user?.region_assignee ? `Région : ${user.region_assignee}` : "Vue nationale"}
          </p>
        </div>
        <select
          value={annee ?? ""}
          onChange={(e) => setAnnee(e.target.value ? parseInt(e.target.value) : undefined)}
          className="text-sm border border-surface-muted rounded-lg px-3 py-2 bg-white text-navy-900
                     focus:outline-none focus:ring-2 focus:ring-postal"
        >
          <option value="">Toutes les années</option>
          <option value="2023">2023</option>
          <option value="2024">2024</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-gray-400">
          <div className="text-center">
            <Package className="w-10 h-10 mx-auto mb-3 animate-pulse text-postal" />
            <p className="text-sm">Chargement des données…</p>
          </div>
        </div>
      ) : (
        <>
          {/* ── KPI Cards ── */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <KPICard icon={Package} label="Total colis" value={fmt(resume?.total_colis ?? 0)} />
            <KPICard icon={DollarSign} label="Chiffre d'affaires" value={fmtDT(resume?.total_ca ?? 0)} accent />
            <KPICard icon={Globe} label="Colis internationaux" value={fmt(resume?.colis_international ?? 0)}
              sub={`${resume?.taux_international ?? 0}% du total`} />
            <KPICard icon={AlertTriangle} label="Anomalies détectées" value={resume?.colis_anomalie ?? 0} />
            <KPICard icon={TrendingUp} label="Taux international" value={`${resume?.taux_international ?? 0}%`} />
          </div>

          {/* ── Ligne 2 : Évolution mensuelle + Répartition nature ── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 bg-white rounded-xl p-5 shadow-sm border border-surface-muted">
              <h2 className="font-display font-semibold text-navy-900 mb-4">Évolution mensuelle</h2>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={evolution} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="volume" stroke="#2E86AB" strokeWidth={2} dot={false} name="Volume" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-xl p-5 shadow-sm border border-surface-muted">
              <h2 className="font-display font-semibold text-navy-900 mb-4">Nature des envois</h2>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={nature} dataKey="total" nameKey="nature" cx="50%" cy="50%" outerRadius={80} label={({ nature: n, pourcentage: p }) => `${n} ${p}%`}>
                    {nature.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => [fmt(v), "Colis"]} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* ── Ligne 3 : Volume par région + Services ── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white rounded-xl p-5 shadow-sm border border-surface-muted">
              <h2 className="font-display font-semibold text-navy-900 mb-4">Volume par région</h2>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={volumeBarData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                  <XAxis dataKey="region" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="National" fill="#2E86AB" stackId="a" />
                  <Bar dataKey="International" fill="#F0A500" stackId="a" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-xl p-5 shadow-sm border border-surface-muted">
              <h2 className="font-display font-semibold text-navy-900 mb-4">Types de service</h2>
              <div className="space-y-3 mt-2">
                {services.map((s, i) => (
                  <div key={s.type_service}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-navy-700 font-medium">{s.type_service}</span>
                      <span className="text-gray-400">{s.pourcentage}% — {fmtDT(s.ca_total)}</span>
                    </div>
                    <div className="h-2 bg-surface-muted rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{ width: `${s.pourcentage}%`, backgroundColor: COLORS[i % COLORS.length] }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ── Ligne 4 : CA par destination ── */}
          <div className="bg-white rounded-xl p-5 shadow-sm border border-surface-muted">
            <h2 className="font-display font-semibold text-navy-900 mb-4">
              Top destinations — Chiffre d'affaires
            </h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={caDestination} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="pays" tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => [fmtDT(v), "CA"]} />
                <Bar dataKey="ca_total" fill="#1E3A5F" radius={[0, 4, 4, 0]} name="Chiffre d'affaires" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
