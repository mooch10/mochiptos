"use client";

import { useState } from "react";
import { fetchApi, IclResult, IpcResult, UvaResult } from "@/lib/api";
import { Calculator, TrendingUp, Landmark, Calendar, DollarSign, Loader2 } from "lucide-react";

export default function CalculadorasPage() {
  const [activeTab, setActiveTab] = useState<"icl" | "ipc" | "uva">("icl");

  // State ICL
  const [montoIcl, setMontoIcl] = useState<number>(250000);
  const [fechaInicioIcl, setFechaInicioIcl] = useState<string>("2023-01-01");
  const [fechaFinIcl, setFechaFinIcl] = useState<string>("2024-01-01");
  const [resIcl, setResIcl] = useState<IclResult | null>(null);
  const [loadingIcl, setLoadingIcl] = useState(false);

  // State IPC
  const [montoIpc, setMontoIpc] = useState<number>(300000);
  const [mesesIpc, setMesesIpc] = useState<number>(6);
  const [fechaInicioIpc, setFechaInicioIpc] = useState<string>("2024-01-01");
  const [resIpc, setResIpc] = useState<IpcResult | null>(null);
  const [loadingIpc, setLoadingIpc] = useState(false);

  // State UVA
  const [montoUva, setMontoUva] = useState<number>(100000);
  const [tnaUva, setTnaUva] = useState<number>(5.5);
  const [plazoUva, setPlazoUva] = useState<number>(20);
  const [resUva, setResUva] = useState<UvaResult | null>(null);
  const [loadingUva, setLoadingUva] = useState(false);

  const handleCalcIcl = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingIcl(true);
    try {
      const data = await fetchApi<{ data: IclResult }>("/calc/icl", {
        monto_inicial: montoIcl,
        fecha_inicio: fechaInicioIcl,
        fecha_fin: fechaFinIcl,
      });
      setResIcl(data.data);
    } catch (err) {
      console.error("Error en ICL:", err);
    } finally {
      setLoadingIcl(false);
    }
  };

  const handleCalcIpc = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingIpc(true);
    try {
      const data = await fetchApi<{ data: IpcResult }>("/calc/ipc", {
        monto_inicial: montoIpc,
        meses: mesesIpc,
        fecha_inicio: fechaInicioIpc,
      });
      setResIpc(data.data);
    } catch (err) {
      console.error("Error en IPC:", err);
    } finally {
      setLoadingIpc(false);
    }
  };

  const handleCalcUva = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingUva(true);
    try {
      const data = await fetchApi<{ data: UvaResult }>("/calc/uva", {
        monto_usd: montoUva,
        tna: tnaUva,
        plazo_anios: plazoUva,
      });
      setResUva(data.data);
    } catch (err) {
      console.error("Error en UVA:", err);
    } finally {
      setLoadingUva(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-12">
      <div>
        <h1 className="text-3xl font-extrabold text-white sm:text-4xl flex items-center gap-3">
          <Calculator className="h-8 w-8 text-blue-400" />
          Calculadoras y Simulaciones Financieras
        </h1>
        <p className="mt-2 text-slate-400">
          Herramientas de actualización de alquileres (ICL / IPC) y proyección de Créditos Hipotecarios UVA en CABA.
        </p>
      </div>

      {/* Tabs Switcher - Responsive Mobile Grid */}
      <div className="flex flex-col sm:flex-row gap-2 rounded-2xl border border-slate-800 bg-slate-900/80 p-2 backdrop-blur-md">
        <button
          onClick={() => setActiveTab("icl")}
          className={`flex items-center justify-center gap-2 rounded-xl py-3 px-4 text-xs sm:text-sm font-semibold transition-all ${
            activeTab === "icl"
              ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <TrendingUp className="h-4 w-4 shrink-0" />
          <span>Ajuste ICL (BCRA)</span>
        </button>

        <button
          onClick={() => setActiveTab("ipc")}
          className={`flex items-center justify-center gap-2 rounded-xl py-3 px-4 text-xs sm:text-sm font-semibold transition-all ${
            activeTab === "ipc"
              ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Calendar className="h-4 w-4 shrink-0" />
          <span>Ajuste IPC (INDEC)</span>
        </button>

        <button
          onClick={() => setActiveTab("uva")}
          className={`flex items-center justify-center gap-2 rounded-xl py-3 px-4 text-xs sm:text-sm font-semibold transition-all ${
            activeTab === "uva"
              ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Landmark className="h-4 w-4 shrink-0" />
          <span>Simulador Hipotecario UVA</span>
        </button>
      </div>

      {/* Tab 1: ICL */}
      {activeTab === "icl" && (
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          <form onSubmit={handleCalcIcl} className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
            <h2 className="text-xl font-bold text-white">Calculadora ICL</h2>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">Monto Inicial ($ ARS)</label>
              <input
                type="number"
                value={montoIcl}
                onChange={(e) => setMontoIcl(Number(e.target.value))}
                className="mt-1.5 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">Fecha Inicio</label>
                <input
                  type="date"
                  value={fechaInicioIcl}
                  onChange={(e) => setFechaInicioIcl(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">Fecha Fin</label>
                <input
                  type="date"
                  value={fechaFinIcl}
                  onChange={(e) => setFechaFinIcl(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loadingIcl}
              className="w-full rounded-xl bg-blue-600 py-3.5 text-sm font-semibold text-white transition-all hover:bg-blue-500 flex items-center justify-center gap-2"
            >
              {loadingIcl ? <Loader2 className="h-4 w-4 animate-spin" /> : "Calcular Ajuste ICL"}
            </button>
          </form>

          {/* Resultado ICL */}
          <div className="flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
            <div>
              <h3 className="text-lg font-bold text-white">Resultado de Actualización</h3>
              {resIcl ? (
                <div className="mt-6 space-y-6">
                  <div>
                    <p className="text-xs uppercase text-slate-400">Monto Actualizado</p>
                    <p className="text-4xl font-extrabold text-emerald-400">${resIcl.monto_actualizado.toLocaleString()} ARS</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4 border-t border-slate-800 pt-4">
                    <div>
                      <p className="text-xs text-slate-400">Aumento Porcentual</p>
                      <p className="text-xl font-bold text-white">+{resIcl.porcentaje_aumento}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400">Monto Inicial</p>
                      <p className="text-xl font-semibold text-slate-300">${resIcl.monto_inicial.toLocaleString()}</p>
                    </div>
                  </div>

                  <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 text-xs text-slate-400 space-y-1">
                    <p>ICL Fecha Inicial ({resIcl.fecha_inicio_usada}): <strong className="text-white">{resIcl.icl_inicio}</strong></p>
                    <p>ICL Fecha Final ({resIcl.fecha_fin_usada}): <strong className="text-white">{resIcl.icl_fin}</strong></p>
                  </div>
                </div>
              ) : (
                <p className="mt-8 text-center text-sm text-slate-500">Ingresa los datos y presiona calcular para ver el monto ajustado por ICL.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: IPC */}
      {activeTab === "ipc" && (
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          <form onSubmit={handleCalcIpc} className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
            <h2 className="text-xl font-bold text-white">Calculadora IPC</h2>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">Monto Inicial ($ ARS)</label>
              <input
                type="number"
                value={montoIpc}
                onChange={(e) => setMontoIpc(Number(e.target.value))}
                className="mt-1.5 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">Meses Acumulados</label>
                <select
                  value={mesesIpc}
                  onChange={(e) => setMesesIpc(Number(e.target.value))}
                  className="mt-1.5 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                >
                  <option value={3}>3 Meses (Trimestral)</option>
                  <option value={4}>4 Meses (Cuatrimestral)</option>
                  <option value={6}>6 Meses (Semestral)</option>
                  <option value={12}>12 Meses (Anual)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">Fecha de Inicio</label>
                <input
                  type="date"
                  value={fechaInicioIpc}
                  onChange={(e) => setFechaInicioIpc(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loadingIpc}
              className="w-full rounded-xl bg-blue-600 py-3.5 text-sm font-semibold text-white transition-all hover:bg-blue-500 flex items-center justify-center gap-2"
            >
              {loadingIpc ? <Loader2 className="h-4 w-4 animate-spin" /> : "Calcular Ajuste IPC"}
            </button>
          </form>

          {/* Resultado IPC */}
          <div className="flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
            <div>
              <h3 className="text-lg font-bold text-white">Resultado Inflación IPC</h3>
              {resIpc ? (
                <div className="mt-6 space-y-6">
                  <div>
                    <p className="text-xs uppercase text-slate-400">Monto Actualizado</p>
                    <p className="text-4xl font-extrabold text-emerald-400">${resIpc.monto_actualizado.toLocaleString()} ARS</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4 border-t border-slate-800 pt-4">
                    <div>
                      <p className="text-xs text-slate-400">Inflación Acumulada</p>
                      <p className="text-xl font-bold text-white">+{resIpc.porcentaje_aumento}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400">Meses Evaluados</p>
                      <p className="text-xl font-semibold text-slate-300">{resIpc.meses_evaluados} meses</p>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="mt-8 text-center text-sm text-slate-500">Ingresa los datos para calcular el impacto de la inflación acumulada INDEC.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: UVA */}
      {activeTab === "uva" && (
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          <form onSubmit={handleCalcUva} className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
            <h2 className="text-xl font-bold text-white">Simulador Hipotecario UVA</h2>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">Monto Préstamo ($ USD)</label>
              <input
                type="number"
                value={montoUva}
                onChange={(e) => setMontoUva(Number(e.target.value))}
                className="mt-1.5 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">Tasa TNA (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={tnaUva}
                  onChange={(e) => setTnaUva(Number(e.target.value))}
                  className="mt-1.5 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">Plazo (Años)</label>
                <input
                  type="number"
                  value={plazoUva}
                  onChange={(e) => setPlazoUva(Number(e.target.value))}
                  className="mt-1.5 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loadingUva}
              className="w-full rounded-xl bg-blue-600 py-3.5 text-sm font-semibold text-white transition-all hover:bg-blue-500 flex items-center justify-center gap-2"
            >
              {loadingUva ? <Loader2 className="h-4 w-4 animate-spin" /> : "Simular Cuota Inicial UVA"}
            </button>
          </form>

          {/* Resultado UVA */}
          <div className="flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
            <div>
              <h3 className="text-lg font-bold text-white">Proyección Cuota Inicial</h3>
              {resUva ? (
                <div className="mt-6 space-y-6">
                  <div>
                    <p className="text-xs uppercase text-slate-400">Cuota Inicial Estimada</p>
                    <p className="text-4xl font-extrabold text-blue-400">${resUva.cuota_inicial_ars.toLocaleString()} ARS</p>
                    <p className="text-sm font-semibold text-emerald-400 mt-1">~${resUva.cuota_inicial_usd} USD / mes ({resUva.cuota_inicial_uva} UVAs)</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4 border-t border-slate-800 pt-4 text-xs">
                    <div>
                      <p className="text-slate-400">Valor UVA Usado</p>
                      <p className="text-base font-bold text-white">${resUva.valor_uva_usado}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Dólar Blue Usado</p>
                      <p className="text-base font-bold text-white">${resUva.dolar_usado}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="mt-8 text-center text-sm text-slate-500">Ingresa el monto deseado en USD y plazo para simular tu cuota hipotecaria.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
