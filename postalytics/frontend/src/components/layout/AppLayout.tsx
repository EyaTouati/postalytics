import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Package, LayoutDashboard, Users, MessageSquare, TrendingUp,
  UserCircle, LogOut, ChevronLeft, Menu, Clock, MapPin,
  GitBranch, Globe, BarChart2,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import clsx from "clsx";

const ROLE_LABELS: Record<string, { label: string; color: string }> = {
  admin:          { label: "Administrateur",    color: "bg-red-100 text-red-700" },
  responsable:    { label: "Responsable",       color: "bg-blue-100 text-blue-700" },
  agent_regional: { label: "Agent régional",    color: "bg-green-100 text-green-700" },
};

export default function AppLayout() {
  const { user, logout } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    {
      section: "Tableaux de bord",
      items: [
        { to: "/dashboard",    icon: LayoutDashboard, label: "Vue Globale" },
        { to: "/temporelle",   icon: Clock,           label: "Analyse Temporelle" },
        { to: "/geographique", icon: MapPin,          label: "Analyse Géographique" },
        { to: "/croisees",     icon: GitBranch,       label: "Analyses Croisées" },
        { to: "/services",     icon: BarChart2,       label: "Analyse Services" },
        { to: "/destinations", icon: Globe,           label: "Destinations" },
      ],
    },
    {
      section: "Outils",
      items: [
        { to: "/previsions", icon: TrendingUp,    label: "Prévisions ML" },
        { to: "/chatbot",    icon: MessageSquare, label: "Assistant IA" },
        ...(user?.role === "admin"
          ? [{ to: "/admin/users", icon: Users, label: "Utilisateurs" }]
          : []),
      ],
    },
  ];

  const roleInfo = ROLE_LABELS[user?.role || ""] || { label: user?.role, color: "" };

  return (
    <div className="flex h-screen bg-surface overflow-hidden">

      {/* ── Sidebar ── */}
      <aside
        className={clsx(
          "flex flex-col bg-navy-900 text-white transition-all duration-200 flex-shrink-0",
          collapsed ? "w-16" : "w-60"
        )}
      >
        {/* Header */}
        <div className={clsx(
          "flex items-center gap-3 px-4 py-5 border-b border-navy-700",
          collapsed && "justify-center"
        )}>
          <div className="flex-shrink-0 w-8 h-8 bg-amber-postal rounded-lg flex items-center justify-center">
            <Package className="w-4 h-4 text-navy-900" />
          </div>
          {!collapsed && (
            <div>
              <span className="font-display font-bold text-base leading-none">PostalBI</span>
              <p className="text-xs text-gray-400 mt-0.5">La Poste Tunisienne</p>
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className={clsx(
              "text-gray-400 hover:text-white transition-colors",
              collapsed ? "ml-0" : "ml-auto"
            )}
          >
            {collapsed
              ? <Menu className="w-4 h-4" />
              : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 space-y-1 px-2">
          {navItems.map(({ section, items }) => (
            <div key={section}>
              {/* Label section */}
              {!collapsed && (
                <p className="text-xs font-medium text-gray-500 uppercase tracking-widest
                               px-3 pt-4 pb-1">
                  {section}
                </p>
              )}
              {collapsed && <div className="border-t border-navy-700 my-2" />}

              {items.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    clsx(
                      "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                      isActive
                        ? "bg-postal text-white"
                        : "text-gray-400 hover:bg-navy-700 hover:text-white",
                      collapsed && "justify-center"
                    )
                  }
                  title={collapsed ? label : undefined}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  {!collapsed && <span>{label}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {/* Footer — profil */}
        <div className={clsx("border-t border-navy-700 p-3", collapsed && "flex justify-center")}>
          {collapsed ? (
            <button
              onClick={logout}
              className="text-gray-400 hover:text-white"
              title="Déconnexion"
            >
              <LogOut className="w-4 h-4" />
            </button>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-navy-700 flex items-center justify-center flex-shrink-0">
                  <UserCircle className="w-5 h-5 text-gray-300" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-white truncate">{user?.username}</p>
                  {user?.region_assignee && (
                    <p className="text-xs text-gray-400">{user.region_assignee}</p>
                  )}
                </div>
              </div>
              <span className={clsx(
                "inline-flex items-center justify-center w-full px-2 py-0.5 rounded-full text-xs font-medium",
                roleInfo.color
              )}>
                {roleInfo.label}
              </span>
              <button
                onClick={logout}
                className="flex items-center gap-2 text-xs text-gray-400 hover:text-white
                           w-full px-2 py-1 rounded hover:bg-navy-700 transition-colors"
              >
                <LogOut className="w-3 h-3" />
                Déconnexion
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* ── Contenu principal ── */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}