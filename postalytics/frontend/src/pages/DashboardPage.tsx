import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Package,
  TrendingUp,
  Globe,
  DollarSign,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from "lucide-react";
import api from "../services/api";
import { useAuthStore } from "../store/authStore";

// ── Palette ───────────────────────────────────────────────────────────────────
const COLORS = {
  primary: "#2E86AB",
  amber: "#F0A500",
  navy: "#0A1628",
  dark: "#1E3A5F",
  green: "#10B981",
  red: "#EF4444",
  purple: "#8B5CF6",
  orange: "#F97316",
  teal: "#14B8A6",
};

const SERVICE_COLORS: Record<string, string> = {
  "EMS-N": COLORS.primary,
  CP: COLORS.amber,
  UP: COLORS.dark,
  "RPP-I": COLORS.purple,
  RR: COLORS.teal,
  "EMS-I": COLORS.orange,
  NOR: COLORS.green,
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const fmt = (n: number) => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toString();
};

const fmtTND = (n: number) =>
  new Intl.NumberFormat("fr-TN", {
    style: "currency",
    currency: "TND",
    maximumFractionDigits: 0,
  }).format(n);

// ── Composants ────────────────────────────────────────────────────────────────

function KPICard({
  icon: Icon,
  label,
  value,
  sub,
  trend,
  color = COLORS.primary,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sub?: string;
  trend?: number | null;
  color?: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-surface-muted overflow-hidden">
      <div className="h-1" style={{ backgroundColor: color }} />
      <div className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">
              {label}
            </p>
            <p className="font-display text-2xl font-bold text-navy-900">
              {value}
            </p>
            {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
          </div>
          <div
            className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: `${color}15` }}
          >
            <Icon className="w-5 h-5" style={{ color }} />
          </div>
        </div>
        {trend !== undefined && trend !== null && (
          <div
            className={`flex items-center gap-1 mt-3 text-xs font-medium ${
              trend > 0
                ? "text-green-600"
                : trend < 0
                  ? "text-red-500"
                  : "text-gray-400"
            }`}
          >
            {trend > 0 ? (
              <ArrowUpRight className="w-3 h-3" />
            ) : trend < 0 ? (
              <ArrowDownRight className="w-3 h-3" />
            ) : (
              <Minus className="w-3 h-3" />
            )}
            {Math.abs(trend)}% vs année précédente
          </div>
        )}
      </div>
    </div>
  );
}

function SectionTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="mb-4">
      <h2 className="font-display text-lg font-semibold text-navy-900">
        {title}
      </h2>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

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

// ── Page principale ───────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { user } = useAuthStore();
  const [annee, setAnnee] = useState<number | "">("");
  const [kpis, setKpis] = useState<any>(null);
  const [evolutionAnnuelle, setEvolutionAnnuelle] = useState<any[]>([]);
  const [evolutionMensuelle, setEvolutionMensuelle] = useState<any[]>([]);
  const [services, setServices] = useState<any[]>([]);
  const [gouvernorats, setGouvernorats] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = annee ? { annee } : {};
    setLoading(true);
    Promise.all([
      api.get("/dashboard/kpis-globaux", { params }),
      api.get("/dashboard/evolution-annuelle"),
      api.get("/dashboard/evolution-mensuelle", { params }),
      api.get("/dashboard/repartition-services", { params }),
      api.get("/dashboard/top-gouvernorats", {
        params: { ...params, top: 10 },
      }),
    ])
      .then(([k, ea, em, s, g]) => {
        setKpis(k.data);
        setEvolutionAnnuelle(ea.data);
        setEvolutionMensuelle(em.data);
        setServices(s.data);
        setGouvernorats(g.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [annee]);

  // Grouper évolution mensuelle par mois pour comparaison multi-années
  const moisLabels = [
    "Jan",
    "Fév",
    "Mar",
    "Avr",
    "Mai",
    "Jun",
    "Jul",
    "Aoû",
    "Sep",
    "Oct",
    "Nov",
    "Déc",
  ];
  const anneesDispo = [
    ...new Set(evolutionMensuelle.map((d) => d.annee)),
  ].sort();
  const dataParMois = moisLabels.map((label, i) => {
    const row: any = { mois: label };
    anneesDispo.forEach((an) => {
      const found = evolutionMensuelle.find(
        (d) => d.annee === an && d.mois === i + 1,
      );
      row[`${an}`] = found?.volume || 0;
    });
    return row;
  });

  const ANNEE_COLORS = ["#2E86AB", "#F0A500", "#1E3A5F", "#10B981"];

  if (loading)
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Package className="w-10 h-10 mx-auto mb-3 animate-pulse text-postal" />
          <p className="text-sm text-gray-400">Chargement des données…</p>
        </div>
      </div>
    );

  return (
    <div className="p-6 space-y-8">
      {/* ── En-tête ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-navy-900">
            Tableau de bord
          </h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {user?.region_assignee
              ? `Gouvernorat : ${user.region_assignee}`
              : "Vue nationale — toutes régions"}
          </p>
        </div>
        <select
          value={annee}
          onChange={(e) =>
            setAnnee(e.target.value ? parseInt(e.target.value) : "")
          }
          className="text-sm border border-surface-muted rounded-lg px-3 py-2 bg-white
                     text-navy-900 focus:outline-none focus:ring-2 focus:ring-postal"
        >
          <option value="">Toutes les années</option>
          {[2023, 2024, 2025, 2026].map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
      </div>

      {/* ── KPI Cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <KPICard
          icon={Package}
          label="Total colis"
          value={fmt(kpis?.total_colis ?? 0)}
          sub={`${fmt(kpis?.moyenne_par_jour ?? 0)} / jour`}
          trend={kpis?.croissance_vs_precedent}
          color={COLORS.primary}
        />
        <KPICard
          icon={DollarSign}
          label="Chiffre d'affaires"
          value={fmtTND(kpis?.ca_total ?? 0)}
          color={COLORS.amber}
        />
        <KPICard
          icon={Globe}
          label="Colis internationaux"
          value={fmt(kpis?.colis_international ?? 0)}
          sub={`${kpis?.taux_international ?? 0}% du total`}
          color={COLORS.purple}
        />
        <KPICard
          icon={TrendingUp}
          label="Taux international"
          value={`${kpis?.taux_international ?? 0}%`}
          color={COLORS.teal}
        />
        <KPICard
          icon={Calendar}
          label="Moy. journalière"
          value={fmt(kpis?.moyenne_par_jour ?? 0)}
          sub="colis / jour ouvrable"
          color={COLORS.orange}
        />
        <KPICard
          icon={ArrowUpRight}
          label="Croissance"
          value={
            kpis?.croissance_vs_precedent != null
              ? `${kpis.croissance_vs_precedent > 0 ? "+" : ""}${kpis.croissance_vs_precedent}%`
              : "—"
          }
          sub={
            kpis?.annee_precedente
              ? `vs ${kpis.annee_precedente}`
              : "Sélectionner une année"
          }
          trend={kpis?.croissance_vs_precedent}
          color={kpis?.croissance_vs_precedent > 0 ? COLORS.green : COLORS.red}
        />
      </div>

      {/* ── Évolution annuelle ── */}
      <div>
        <SectionTitle
          title="Évolution du volume — toutes les années"
          sub="Comparaison 2023 / 2024 / 2025 / 2026"
        />
        <Card>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={evolutionAnnuelle}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
              <XAxis dataKey="annee" tick={{ fontSize: 13, fontWeight: 600 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
              <Tooltip formatter={(v: number) => [fmt(v), "Colis"]} />
              <Bar
                dataKey="volume"
                fill={COLORS.primary}
                radius={[6, 6, 0, 0]}
                name="Volume"
              >
                {evolutionAnnuelle.map((_, i) => (
                  <Cell key={i} fill={ANNEE_COLORS[i % ANNEE_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* ── Évolution mensuelle multi-années ── */}
      <div>
        <SectionTitle
          title="Saisonnalité mensuelle"
          sub="Superposition des années pour identifier les tendances récurrentes"
        />
        <Card>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={dataParMois}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
              <XAxis dataKey="mois" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
              <Tooltip formatter={(v: number) => [fmt(v), "Colis"]} />
              <Legend />
              {anneesDispo.map((an, i) => (
                <Line
                  key={an}
                  type="monotone"
                  dataKey={`${an}`}
                  stroke={ANNEE_COLORS[i % ANNEE_COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  name={`${an}`}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* ── Services + Gouvernorats ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Services */}
        <div>
          <SectionTitle title="Répartition par service" />
          <Card>
            <div className="space-y-3">
              {services.map((s) => (
                <div key={s.code}>
                  <div className="flex justify-between text-sm mb-1">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{
                          backgroundColor:
                            SERVICE_COLORS[s.code] || COLORS.primary,
                        }}
                      />
                      <span className="font-medium text-navy-900">
                        {s.label}
                      </span>
                      <span className="text-xs text-gray-400">({s.code})</span>
                    </div>
                    <div className="text-right">
                      <span className="font-medium text-navy-900">
                        {fmt(s.volume)}
                      </span>
                      <span className="text-gray-400 ml-2">
                        {s.pourcentage}%
                      </span>
                    </div>
                  </div>
                  <div className="h-2 bg-surface-muted rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${s.pourcentage}%`,
                        backgroundColor:
                          SERVICE_COLORS[s.code] || COLORS.primary,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Top gouvernorats */}
        <div>
          <SectionTitle title="Top gouvernorats expéditeurs" />
          <Card>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={gouvernorats} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                <XAxis
                  type="number"
                  tick={{ fontSize: 10 }}
                  tickFormatter={fmt}
                />
                <YAxis
                  type="category"
                  dataKey="gouvernorat"
                  tick={{ fontSize: 11 }}
                  width={90}
                />
                <Tooltip formatter={(v: number) => [fmt(v), "Colis"]} />
                <Bar
                  dataKey="volume"
                  fill={COLORS.primary}
                  radius={[0, 4, 4, 0]}
                  name="Volume"
                >
                  {gouvernorats.map((_, i) => (
                    <Cell
                      key={i}
                      fill={
                        i === 0
                          ? COLORS.amber
                          : i < 3
                            ? COLORS.primary
                            : COLORS.dark
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      </div>
    </div>
  );
}
