import { Link, useLocation } from "react-router-dom";
import { Globe, Map as MapIcon, Brain, Cpu, FlaskConical, GitCompare, Thermometer, Upload } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export function TopBar() {
  const { t, lang, setLang } = useI18n();
  const loc = useLocation();
  const navItems = [
    { to: "/", label: t("nav_dashboard"), icon: MapIcon },
    { to: "/internal/poi-heatmap", label: t("nav_poi_heatmap"), icon: Thermometer },
    { to: "/poi-manager", label: t("nav_poi_manager"), icon: Upload },
  ];
  return (
    <header className="h-12 shrink-0 border-b border-border bg-card flex items-center px-4 gap-6">
      <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight">
        <span className="h-6 w-6 rounded bg-primary text-primary-foreground grid place-items-center text-xs font-bold">UA</span>
        <span className="hidden md:inline">{t("app_title")}</span>
      </Link>
      <nav className="flex items-center gap-1 text-sm">
        {navItems.map((it) => {
          const active = loc.pathname === it.to;
          const Icon = it.icon;
          return (
            <Link key={it.to} to={it.to}
              className={cn("flex items-center gap-1.5 px-2.5 py-1.5 rounded-md transition-colors",
                active ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-secondary/60")}>
              <Icon className="h-3.5 w-3.5" />
              <span className="hidden lg:inline">{it.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="ml-auto flex items-center gap-3">
        <span className="px-2 py-0.5 rounded text-[10px] font-bold mono uppercase tracking-widest bg-mock-banner text-primary-foreground">{t("mock_mode")}</span>
        <button onClick={() => setLang(lang === "en" ? "ar" : "en")} className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground" title="Toggle language">
          <Globe className="h-3.5 w-3.5" /><span className="mono">{lang.toUpperCase()}</span>
        </button>
      </div>
    </header>
  );
}
