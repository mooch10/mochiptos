"use client";

import { useEffect, useState } from "react";
import { fetchApi, MarketM2Item } from "@/lib/api";
import { TrendingUp, Building2, Layers, Loader2 } from "lucide-react";

export default function MercadoPage() {
  const [m2Data, setM2Data] = useState<MarketM2Item[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadM2Data() {
      try {
        const res = await fetchApi<{ data: MarketM2Item[] }>("/market/m2");
        if (res.data && Array.isArray(res.data)) {
          setM2Data(res.data);
        }
      } catch (err) {
        console.error("Error al cargar índice de m2:", err);
      } finally {
        setLoading(false);
      }
    }
    loadM2Data();
  }, []);

  const maxM2 = m2Data.length > 0 ? Math.max(...m2Data.map(d => d.mediana_precio_m2)) : 3000;

  return (
    <div className="mx-auto max-w-6xl space-y-8 pb-12">
      <div>
        <h1 className="text-3xl font-extrabold text-white sm:text-4xl flex items-center gap-3">
          <TrendingUp className="h-8 w-8 text-blue-400" />
          Índice de Precios USD / m² por Barrio en CABA
        </h1>
        <p className="mt-2 text-slate-400">
          Valores medianos de mercado calculados sobre 92.241 departamentos, aplicando filtrado estadístico IQR para eliminar outliers.
        </p>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
          <Loader2 className="h-10 w-10 animate-spin text-blue-400" />
          <p className="text-base font-bold text-white">Calculando medianas de USD/m² por barrio...</p>
          <p className="text-xs text-slate-400 max-w-sm text-center">Filtrando outliers estadísticos con IQR sobre todas las publicaciones.</p>
        </div>
      ) : (
        <>
          {/* Grid Bar Chart Visualizer */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 sm:p-8 backdrop-blur-md space-y-6">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Building2 className="h-5 w-5 text-emerald-400" />
              Ranking de Barrios por Mediana USD/m²
            </h2>

            <div className="space-y-4">
              {m2Data.slice(0, 20).map((item, idx) => {
                const widthPercent = Math.round((item.mediana_precio_m2 / maxM2) * 100);
                return (
                  <div key={item.barrio} className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-semibold text-white">
                        {idx + 1}. {item.barrio}
                      </span>
                      <span className="font-bold text-blue-400">
                        ${item.mediana_precio_m2.toLocaleString()} USD/m²
                      </span>
                    </div>
                    <div className="h-3 w-full overflow-hidden rounded-full bg-slate-950">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-blue-600 via-teal-400 to-emerald-400 transition-all duration-500"
                        style={{ width: `${widthPercent}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-500">
                      <span>Promedio: ${item.promedio_precio_m2} USD/m²</span>
                      <span>{item.total_publicaciones} publicaciones evaluadas</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Table Detail */}
          <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md">
            <div className="p-6 border-b border-slate-800">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Layers className="h-5 w-5 text-blue-400" />
                Detalle General de Barrios
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="border-b border-slate-800 bg-slate-950/80 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="px-6 py-4">Barrio</th>
                    <th className="px-6 py-4 text-right">Mediana USD/m²</th>
                    <th className="px-6 py-4 text-right">Promedio USD/m²</th>
                    <th className="px-6 py-4 text-right">Mediana Depto USD</th>
                    <th className="px-6 py-4 text-right">Muestra Valida</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {m2Data.map((row) => (
                    <tr key={row.barrio} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-6 py-4 font-semibold text-white">{row.barrio}</td>
                      <td className="px-6 py-4 text-right font-extrabold text-blue-400">${row.mediana_precio_m2.toLocaleString()}</td>
                      <td className="px-6 py-4 text-right text-slate-400">${row.promedio_precio_m2.toLocaleString()}</td>
                      <td className="px-6 py-4 text-right font-semibold text-emerald-400">${row.mediana_precio_usd?.toLocaleString()}</td>
                      <td className="px-6 py-4 text-right text-slate-400">{row.total_publicaciones} deptos</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
