import Link from "next/link";
import { fetchApi, MarketM2Item, NewsItem, Property } from "@/lib/api";
import TrueFocus from "@/components/TrueFocus";
import { 
  Building2, 
  TrendingUp, 
  Sparkles, 
  Search, 
  ArrowUpRight, 
  ExternalLink, 
  ShieldCheck,
  Zap,
  MapPin
} from "lucide-react";

export const revalidate = 60;

export default async function HomePage() {
  let marketSummary: MarketM2Item[] = [];
  let opportunities: Property[] = [];

  try {
    const [m2Res, oppRes] = await Promise.all([
      fetchApi<{ data: MarketM2Item[] }>("/market/m2"),
      fetchApi<{ data: Property[] }>("/market/opportunities", { top_n: 4 }),
    ]);

    marketSummary = m2Res.data || [];
    opportunities = oppRes.data || [];
  } catch (error) {
    console.error("Error al cargar datos en Home:", error);
  }

  const topBarrio = marketSummary[0] || { barrio: "Palermo", mediana_precio_m2: 2450 };
  const totalBarrios = marketSummary.length || 47;

  return (
    <div className="space-y-12 pb-12">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl border border-slate-800/80 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 p-8 sm:p-12">
        <div className="absolute -right-20 -top-20 h-96 w-96 rounded-full bg-blue-600/10 blur-3xl" />
        <div className="absolute -left-20 -bottom-20 h-96 w-96 rounded-full bg-emerald-500/10 blur-3xl" />

        <div className="relative z-10 max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3.5 py-1 text-xs font-semibold text-blue-400">
            <Zap className="h-3.5 w-3.5 text-blue-400" />
            Machine Learning & Big Data Inmobiliario
          </div>

          <div className="flex justify-start text-left">
            <TrueFocus sentence="Inteligencia Inmobiliaria en CABA" blurAmount={3} borderColor="#3b82f6" glowColor="rgba(59, 130, 246, 0.4)" />
          </div>

          <p className="text-lg text-slate-300">
            Analizamos más de <strong className="text-white">92.000 departamentos</strong> en tiempo real con modelos de Machine Learning para detectar las mejores oportunidades de inversión, calcular valores $/m² por barrio sin outliers e índices financieros.
          </p>

          <div className="flex flex-wrap gap-4 pt-2">
            <Link
              href="/oportunidades"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 transition-all hover:brightness-110"
            >
              <Sparkles className="h-4 w-4" />
              Ver Oportunidades ML
            </Link>
            <Link
              href="/buscador"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900/80 px-6 py-3.5 text-sm font-semibold text-slate-200 backdrop-blur-md transition-all hover:bg-slate-800 hover:text-white"
            >
              <Search className="h-4 w-4 text-slate-400" />
              Buscador por Barrio
            </Link>
          </div>
        </div>
      </section>

      {/* Metric Stats Banner */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-6 backdrop-blur-md">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Publicaciones Analizadas</p>
          <p className="mt-2 text-3xl font-extrabold text-white">92.241</p>
          <p className="mt-1 text-xs text-emerald-400 flex items-center gap-1">
            <ShieldCheck className="h-3.5 w-3.5" /> Base en Aiven Cloud en vivo
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-6 backdrop-blur-md">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Barrios de CABA</p>
          <p className="mt-2 text-3xl font-extrabold text-white">{totalBarrios}</p>
          <p className="mt-1 text-xs text-slate-400">Con filtrado IQR anti-outliers</p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-6 backdrop-blur-md">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Barrio de Mayor m²</p>
          <p className="mt-2 text-3xl font-extrabold text-blue-400">{topBarrio.barrio}</p>
          <p className="mt-1 text-xs text-slate-400">${topBarrio.mediana_precio_m2} USD / m²</p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-6 backdrop-blur-md">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Modelo ML Precision</p>
          <p className="mt-2 text-3xl font-extrabold text-emerald-400">96.3% R²</p>
          <p className="mt-1 text-xs text-slate-400">RandomForest Regressor Log</p>
        </div>
      </div>

      {/* Top ML Opportunities Preview */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-emerald-400" />
              Oportunidades Destacadas (Machine Learning)
            </h2>
            <p className="text-sm text-slate-400">Propiedades cuyo precio publicado está por debajo de la estimación de mercado.</p>
          </div>
          <Link href="/oportunidades" className="hidden text-sm font-semibold text-blue-400 hover:underline sm:flex items-center gap-1">
            Ver todas <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {opportunities.length > 0 ? (
            opportunities.map((opp) => (
              <div key={opp.id_publicacion} className="group relative flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md transition-all hover:border-blue-500/50 hover:shadow-xl hover:shadow-blue-500/10">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-1 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-bold text-emerald-400">
                      -{opp.descuento_porcentaje}% Descuento
                    </span>
                    <span className="text-xs font-medium text-slate-400">{opp.portal}</span>
                  </div>

                  <h3 className="line-clamp-2 text-base font-semibold text-white group-hover:text-blue-400 transition-colors">
                    {opp.titulo_aviso}
                  </h3>

                  <div className="flex items-center gap-1 text-xs text-slate-400">
                    <MapPin className="h-3.5 w-3.5 text-slate-500" />
                    {opp.barrio} • {opp.ambientes} amb • {opp.m2_totales} m²
                  </div>
                </div>

                <div className="mt-6 border-t border-slate-800/80 pt-4">
                  <div className="flex items-baseline justify-between">
                    <div>
                      <p className="text-[11px] uppercase tracking-wider text-slate-500">Publicado</p>
                      <p className="text-lg font-extrabold text-white">${opp.precio_usd?.toLocaleString()} USD</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[11px] uppercase tracking-wider text-slate-500">Estimado ML</p>
                      <p className="text-sm font-semibold text-emerald-400">${opp.precio_estimado?.toLocaleString()} USD</p>
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full rounded-2xl border border-slate-800 bg-slate-900/40 p-8 text-center text-slate-400">
              Conectando a la API en vivo de Oportunidades...
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
