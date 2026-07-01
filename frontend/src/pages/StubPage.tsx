import { Link } from "react-router-dom";
import { ArrowLeft, Construction } from "lucide-react";
import { TopBar } from "@/components/dashboard/TopBar";
import { useI18n } from "@/lib/i18n";

interface Props {
  title: string;
  subtitle: string;
  description: string;
  features: string[];
  icon: React.ReactNode;
}

export function StubPage({ title, subtitle, description, features, icon }: Props) {
  const { t } = useI18n();
  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      <TopBar />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-6 py-12 space-y-8">
          <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-3.5 w-3.5" />
            {t("back_to_dashboard")}
          </Link>

          <div className="flex items-start gap-4">
            <div className="h-14 w-14 rounded-lg bg-primary/10 text-primary grid place-items-center shrink-0">
              {icon}
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-accent/15 text-accent text-[10px] font-bold mono uppercase tracking-widest mb-2">
                <Construction className="h-3 w-3" />
                {t("coming_v2")}
              </div>
              <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
              <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
            </div>
          </div>

          <p className="text-sm leading-relaxed text-foreground/80">{description}</p>

          <section className="rounded-lg border border-border bg-card p-5">
            <h2 className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold mb-3">
              Planned capabilities
            </h2>
            <ul className="space-y-2 text-sm">
              {features.map((f, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mono text-xs text-primary mt-0.5">{String(i + 1).padStart(2, "0")}</span>
                  <span className="text-foreground/80">{f}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </main>
    </div>
  );
}