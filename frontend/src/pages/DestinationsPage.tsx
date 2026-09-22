import { useState, useEffect } from "react";
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from "recharts";
import { Globe, Flag, MapPin } from "lucide-react";
import api from "../services/api";

const fmt = (n: number) => n >= 1000 ? `${(n/1000).toFixed(1)}k` : `${n}`;
const fmtTND = (n: number) =>
  new Intl.NumberFormat("fr-TN", {
    style: "currency", currency: "TND", maximumFractionDigits: 0,
  }).format(n);

const COLORS = ["#2E86AB","#F0A500","#1E3A5F","#10B981","#8B5CF6",
                "#F97316","#14B8A6","#EF4444","#3B82F6","#EC4899"];

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

export default function DestinationsPage() {
  const [annee, setAnnee] = useState<number | "">("");
  const [intl, setIntl] = useState<any[]>([]);
  const [national, setNational] = useState<any[]>([]);
  const [diaspora, setDiaspora] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = annee ? { annee } : {};
    setLoading(true);
    Promise.all([
      api.get("/dashboard/top-destinations-international", { params: { ...params, top: 20 } }),
      api.get("/dashboard/flux-national-gouvernorat", { params }),
      api.get("/dashboard/analyse-diaspora"),
    ])
      .then(([i, n, d]) => {
        setIntl(i.data);
        setNational(n.data);
        setDiaspora(d.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [annee]);

  // Top 5 pays pour camembert
  const top5Intl = intl.slice(0, 5);
  const autresVol = intl.slice(5).reduce((s, r) => s + r.volume, 0);
  const pieData = [
    ...top5Intl.map(r => ({ name: r.pays, value: r.volume })),
    ...(autresVol > 0 ? [{ name: "Autres", value: autresVol }] : []),
  ];

  // Diaspora été par pays
  const diasporaTopPays = Object.entries(
    diaspora.reduce((acc: any, r: any) => {
      acc[r.pays] = (acc[r.pays] || 0) + r.volume;
      return acc;
    }, {})
  )
    .sort((a: any, b: any) => b[1] - a[1])
    .slice(0, 8)
    .map(([pays, volume]) => ({ pays, volume }));

  // Stats globales
  const totalIntl = intl.reduce((s, r) => s + r.volume, 0);
  const totalCA = intl.reduce((s, r) => s + r.ca, 0);
  const nbPays = intl.length;

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
          <h1 className="font-display text-2xl font-bold text-navy-900">Destinations</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Flux national et international — pays, villes et diaspora
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

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { icon: Globe,  label: "Colis internationaux", value: fmt(totalIntl),  color: "#2E86AB" },
          { icon: Flag,   label: "Pays desservis",        value: `${nbPays}`,     color: "#F0A500" },
          { icon: MapPin, label: "CA international",      value: fmtTND(totalCA), color: "#8B5CF6" },
        ].map((k, i) => (
          <div key={i} className="bg-white rounded-xl border border-surface-muted overflow-hidden">
            <div className="h-1" style={{ backgroundColor: k.color }} />
            <div className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                   style={{ backgroundColor: `${k.color}15` }}>
                <k.icon className="w-5 h-5" style={{ color: k.color }} />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">{k.label}</p>
                <p className="font-display text-xl font-bold text-navy-900">{k.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Section 1 — International */}
      <div>
        <SectionTitle
          title="Top destinations internationales"
          sub="Volume et chiffre d'affaires par pays"
        />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* Camembert top 5 */}
          <Card>
            <h3 className="font-display font-semibold text-navy-900 mb-4 text-sm">
              Répartition top 5 pays
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => [fmt(v), "Colis"]} />
              </PieChart>
            </ResponsiveContainer>
          </Card>

          {/* Top 10 pays barres */}
          <Card>
            <h3 className="font-display font-semibold text-navy-900 mb-4 text-sm">
              Top 10 pays — Volume vs CA
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={intl.slice(0, 10)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
                <XAxis type="number" tick={{ fontSize: 9 }} tickFormatter={fmt} />
                <YAxis
                  type="category"
                  dataKey="pays"
                  tick={{ fontSize: 10 }}
                  width={70}
                />
                <Tooltip
                  formatter={(v: number, name: string) => [
                    name === "volume" ? fmt(v) : fmtTND(v),
                    name === "volume" ? "Colis" : "CA"
                  ]}
                />
                <Legend />
                <Bar dataKey="volume" fill="#2E86AB" name="Volume" radius={[0,3,3,0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Tableau complet */}
        <Card className="mt-4">
          <h3 className="font-display font-semibold text-navy-900 mb-4 text-sm">
            Tableau complet — Top 20 pays
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface">
                <tr>
                  {["#","Pays","Code ISO","Volume","% du total","CA (TND)"].map(h => (
                    <th key={h}
                        className="text-left px-3 py-2 text-xs font-medium text-gray-400 uppercase">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-muted">
                {intl.map((r, i) => (
                  <tr key={i} className="hover:bg-surface">
                    <td className="px-3 py-2 text-gray-400">{i + 1}</td>
                    <td className="px-3 py-2 font-medium text-navy-900">{r.pays}</td>
                    <td className="px-3 py-2">
                      <span className="bg-surface px-2 py-0.5 rounded font-mono text-xs">
                        {r.code_iso}
                      </span>
                    </td>
                    <td className="px-3 py-2 font-medium">{r.volume.toLocaleString()}</td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-surface-muted rounded-full h-1.5 max-w-16">
                          <div
                            className="h-full rounded-full bg-postal"
                            style={{ width: `${r.pourcentage}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{r.pourcentage}%</span>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-gray-500">{fmtTND(r.ca)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Section 2 — National */}
      <div>
        <SectionTitle
          title="Top destinations nationales"
          sub="Villes tunisiennes les plus fréquemment destinataires"
        />
        <Card>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={national.slice(0, 15)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
              <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={fmt} />
              <YAxis type="category" dataKey="ville" tick={{ fontSize: 10 }} width={100} />
              <Tooltip formatter={(v: number) => [fmt(v), "Colis reçus"]} />
              <Bar dataKey="volume" fill="#1E3A5F" radius={[0,4,4,0]} name="Colis reçus">
                {national.slice(0,15).map((_, i) => (
                  <Cell key={i} fill={i < 3 ? "#F0A500" : "#2E86AB"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Section 3 — Diaspora été */}
      <div>
        <SectionTitle
          title="Flux diaspora — Été (Juin-Août)"
          sub="Destinations internationales pendant la période estivale"
        />
        <Card>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={diasporaTopPays} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF4" />
              <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={fmt} />
              <YAxis type="category" dataKey="pays" tick={{ fontSize: 10 }} width={90} />
              <Tooltip formatter={(v: number) => [fmt(v), "Colis (été)"]} />
              <Bar dataKey="volume" radius={[0,4,4,0]} name="Volume été">
                {diasporaTopPays.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 bg-blue-50 border border-blue-100 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              ✈️ <strong>Analyse diaspora :</strong> La France domine les envois
              internationaux estivaux — la communauté tunisienne en Europe profite
              des vacances pour envoyer colis et courriers vers la Tunisie et l'inverse.
            </p>
          </div>
        </Card>
      </div>

    </div>
  );
}