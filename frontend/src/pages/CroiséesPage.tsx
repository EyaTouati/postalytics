import { useState, useEffect } from "react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
} from "recharts";
import api from "../services/api";

const fmt = (n: number) => n >= 1000 ? `${(n/1000).toFixed(1)}k` : `${n}`;

const MOIS_FR = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"];

const SERVICE_COLORS: Record<string, string> = {
  "EMS-N": "#2E86AB", "CP": "#F0A500", "UP": "#1E3A5F",
  "RPP-I": "#8B5CF6", "RR": "#14B8A6", "EMS-I": "#F97316", "NOR": "#10B981",
};

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

function InsightBox({ emoji, text }: { emoji: string; text: string }) {
  return (
    <div className="flex items-start gap-3 bg-blue-50 border border-blue-100 rounded-lg p-3">
      <span className="text-lg">{emoji}</span>
      <p className="text-sm text-blue-800">{text}</p>
    </div>
  );
}

export default function CroiséesPage() {
  const [annee, setAnnee] = useState<number | "">("");
  const [serviceGouv, setServiceGouv] = useState<any[]>([]);
  const [diaspora, setDiaspora] = useState<any[]>([]);
  const [dattes, setDattes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = annee ? { annee } : {};
    setLoading(true);
    Promise.all([
      api.get("/dashboard/service-par-gouvernorat", { params }),
      api.get("/dashboard/analyse-diaspora"),
      api.get("/dashboard/analyse-dattes"),
    ])
      .then(([s, d, da]) => {
        setServiceGouv(s.data);
        setDiaspora(d.data);
        setDattes(da.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [annee]);

  // ── Traitement Service × Gouvernorat ────────────────────────────────────────
  // Top 10 gouvernorats par volume total
  const gouvTotaux = Object.entries(
    serviceGouv.reduce((acc: any, r: any) => {
      acc[r.gouvernorat] = (acc[r.gouvernorat] || 0) + r.volume;
      return acc;
    }, {})
  )
    .sort((a: any, b: any) => b[1] - a[1])
    .slice(0, 10)
    .map(([g]) => g);

  const serviceGouvData = gouvTotaux.map(gouv => {
    const row: any = { gouvernorat: gouv.length > 10 ? gouv.slice(0, 9) + "…" : gouv };
    serviceGouv
      .filter(r => r.gouvernorat === gouv)
      .forEach(r => { row[r.code_service] = r.volume; });
    return row;
  });

  // ── Traitement Diaspora ──────────────────────────────────────────────────────
  // Volume international juin-août par pays et année
  const diasporaAnnees = [...new Set(diaspora.map(d => d.annee))].sort();
  const diasporaTopPays = Object.entries(
    diaspora.reduce((acc: any, r: any) => {
      acc[r.pays] = (acc[r.pays] || 0) + r.volume;
      return acc;
    }, {})
  )
    .sort((a: any, b: any) => (b[1] as number) - (a[1] as number))
    .slice(0, 8)
    .map(([pays]) => pays);

  const diasporaData = diasporaTopPays.map(pays => {
    const row: any = { pays: pays.length > 15 ? pays.slice(0, 13) + "…" : pays };
    diasporaAnnees.forEach(an => {
      row[`${an}`] = diaspora
        .filter(d => d.pays === pays && d.annee === an)
        .reduce((s, d) => s + d.volume, 0);
    });
    return row;
  });

  // ── Traitement Dattes ────────────────────────────────────────────────────────
  // Volume du Sud par mois — comparer oct-nov vs reste
  const dattesMoisData = MOIS_FR.map((label, i) => {
    const mois = i + 1;
    const volume = dattes
      .filter(d => d.mois === mois)
      .reduce((s, d) => s + d.volume, 0);
    return {
      mois: label,
      volume,
      periode_dattes: mois === 10 || mois === 11,
    };
  });

  // Comparaison oct-nov vs moyenne autres mois
  const volOctNov = dattesMoisData
    .filter(d => d.periode_dattes)
    .reduce((s, d) => s + d.volume, 0) / 2;
  const volMoyenAutres = dattesMoisData
    .filter(d => !d.periode_dattes && d.volume > 0)
    .reduce((s, d, _, arr) => s + d.volume / arr.length, 0);
  const facteurDattes = volMoyenAutres > 0
    ? Math.round(volOctNov / volMoyenAutres * 10) / 10
    : 0;

  // Dattes par gouvernorat
  const dattesByGouv = Object.entries(
    dattes.reduce((acc: any, r: any) => {
      acc[r.gouvernorat] = (acc[r.gouvernorat] || 0) + r.volume;
      return acc;
    }, {})
  ).map(([g, v]) => ({ gouvernorat: g, volume: v as number }))
    .sort((a, b) => b.volume - a.volume);

  const ANNEE_COLORS = ["#2E86AB", "#F0A500", "#1E3A5F", "#10B981"];

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
            Analyses Croisées
          </h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Relations entre régions, services, périodes et destinations
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

      {/* ── Analyse 1 : Service × Gouvernorat ── */}
      <div>
        <SectionTitle
          title="Quel service est utilisé dans chaque région ?"
          sub="Top 10 gouvernorats expéditeurs — répartition des types de service"
        />
        <Card>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={serviceGouvData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
              <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={fmt} />
              <YAxis type="category" dataKey="gouvernorat" tick={{ fontSize: 10 }} width={90} />
              <Tooltip formatter={(v: number, name: string) => [fmt(v), name]} />
              <Legend />
              {Object.keys(SERVICE_COLORS).map(code => (
                <Bar
                  key={code}
                  dataKey={code}
                  stackId="a"
                  fill={SERVICE_COLORS[code]}
                  name={code}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <div className="mt-3 space-y-2">
          <InsightBox
            emoji="💡"
            text="Les grandes villes (Tunis, Sfax, Sousse) concentrent la majorité des envois EMS-N (Express national) — signe d'une activité commerciale plus intense."
          />
        </div>
      </div>

      {/* ── Analyse 2 : Effet Diaspora ── */}
      <div>
        <SectionTitle
          title="Effet diaspora — Flux international Juin-Août"
          sub="Les Tunisiens résidant à l'étranger rentrent en été et génèrent un pic d'envois internationaux"
        />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <h3 className="font-display font-semibold text-navy-900 mb-4 text-sm">
              Top pays destinataires (été)
            </h3>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={diasporaData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={fmt} />
                <YAxis type="category" dataKey="pays" tick={{ fontSize: 10 }} width={80} />
                <Tooltip formatter={(v: number, name: string) => [fmt(v), name]} />
                <Legend />
                {diasporaAnnees.map((an, i) => (
                  <Bar
                    key={an}
                    dataKey={`${an}`}
                    fill={ANNEE_COLORS[i % ANNEE_COLORS.length]}
                    name={`${an}`}
                    radius={i === diasporaAnnees.length - 1 ? [0, 3, 3, 0] : undefined}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card>
            <h3 className="font-display font-semibold text-navy-900 mb-4 text-sm">
              Évolution mensuelle flux international estival
            </h3>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={["Jun","Jul","Aoû"].map(m => {
                  const moisNum = ["Jun","Jul","Aoû"].indexOf(m) + 6;
                  return {
                    mois: m,
                    volume: diaspora
                      .filter(d => d.mois === moisNum)
                      .reduce((s, d) => s + d.volume, 0),
                  };
                })}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                <XAxis dataKey="mois" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={fmt} />
                <Tooltip formatter={(v: number) => [fmt(v), "Colis internationaux"]} />
                <Bar dataKey="volume" fill="#2E86AB" radius={[4,4,0,0]} name="Volume intl">
                  {["Jun","Jul","Aoû"].map((_, i) => (
                    <Cell key={i} fill={i === 1 ? "#F0A500" : "#2E86AB"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <InsightBox
              emoji="✈️"
              text="Juillet est le pic de la diaspora — les Tunisiens résidant en France, Italie et Allemagne envoient des colis lors de leurs vacances en Tunisie."
            />
          </Card>
        </div>
      </div>

      {/* ── Analyse 3 : Effet Dattes ── */}
      <div>
        <SectionTitle
          title="Effet dattes — Flux du Sud en Octobre-Novembre"
          sub="Les gouvernorats du Sud (Tozeur, Kébili, Gafsa) connaissent un pic lors de la récolte des dattes"
        />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          <Card>
            <h3 className="font-display font-semibold text-navy-900 mb-4 text-sm">
              Volume mensuel — Gouvernorats du Sud
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={dattesMoisData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                <XAxis dataKey="mois" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={fmt} />
                <Tooltip formatter={(v: number) => [fmt(v), "Colis"]} />
                <Bar dataKey="volume" radius={[3,3,0,0]} name="Volume">
                  {dattesMoisData.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={entry.periode_dattes ? "#F0A500" : "#2E86AB"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="flex gap-3 mt-3 text-xs">
              <span className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full bg-amber-postal" />
                Période récolte dattes (Oct-Nov)
              </span>
              <span className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full bg-postal" />
                Reste de l'année
              </span>
            </div>
          </Card>

          <Card>
            <h3 className="font-display font-semibold text-navy-900 mb-4 text-sm">
              Volume par gouvernorat du Sud
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={dattesByGouv} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={fmt} />
                <YAxis type="category" dataKey="gouvernorat" tick={{ fontSize: 11 }} width={90} />
                <Tooltip formatter={(v: number) => [fmt(v), "Colis"]} />
                <Bar dataKey="volume" fill="#F0A500" radius={[0,4,4,0]} name="Volume">
                  {dattesByGouv.map((_, i) => (
                    <Cell key={i} fill={i === 0 ? "#F0A500" : "#F7C44D"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* KPI dattes */}
            {facteurDattes > 0 && (
              <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-sm font-semibold text-amber-800">
                  📦 Octobre-Novembre = {facteurDattes}× le volume mensuel moyen
                </p>
                <p className="text-xs text-amber-600 mt-1">
                  Hypothèse : corrélation avec la récolte et l'exportation de dattes
                  depuis les oasis du Sud tunisien.
                </p>
              </div>
            )}
          </Card>
        </div>
      </div>

    </div>
  );
}