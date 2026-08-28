"use client";

import { useState, useEffect } from "react";
import { fetchApi, Property } from "@/lib/api";
import { Sparkles, MapPin, ExternalLink, Filter, Loader2, Check, ChevronDown, X } from "lucide-react";

export default function OportunidadesPage() {
  const [opportunities, setOpportunities] = useState<Property[]>([]);
  const [barriosList, setBarriosList] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  // Filtros idénticos al buscador general
  const [selectedBarrios, setSelectedBarrios] = useState<string[]>([]);
  const [showBarrioDropdown, setShowBarrioDropdown] = useState(false);
  const [selectedAmbientes, setSelectedAmbientes] = useState<number | "">("");
  const [selectedEstado, setSelectedEstado] = useState<string>("");
  const [precioMin, setPrecioMin] = useState<number | "">("");
  const [precioMax, setPrecioMax] = useState<number | "">("");
  const [banosMin, setBanosMin] = useState<number | "">("");
  const [tieneCochera, setTieneCochera] = useState<boolean | "">("");
  const [tieneAmenities, setTieneAmenities] = useState<boolean | "">("");

  useEffect(() => {
    fetchApi<{ data: string[] }>("/market/barrios")
      .then((res) => setBarriosList(res.data || []))
      .catch((err) => console.error(err));
  }, []);

  const toggleBarrio = (b: string) => {
    if (selectedBarrios.includes(b)) {
      setSelectedBarrios(selectedBarrios.filter((item) => item !== b));
    } else {
      setSelectedBarrios([...selectedBarrios, b]);
    }
  };

  const loadOpportunities = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = { top_n: 50 };
      if (selectedBarrios.length > 0) params.barrios = selectedBarrios;
      if (selectedAmbientes) params.ambientes = selectedAmbientes;
      if (selectedEstado) params.estado = selectedEstado;
      if (precioMin) params.precio_min = precioMin;
      if (precioMax) params.precio_max = precioMax;
      if (banosMin) params.banos_min = banosMin;
      if (tieneCochera !== "") params.tiene_cochera = tieneCochera;
      if (tieneAmenities !== "") params.tiene_amenities = tieneAmenities;

      const res = await fetchApi<{ data?: Property[] }>("/market/opportunities", params);
      setOpportunities(res.data || []);
    } catch (err) {
      console.error("Error al cargar oportunidades:", err);
      setOpportunities([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOpportunities();
  }, [selectedBarrios, selectedAmbientes, selectedEstado, precioMin, precioMax, banosMin, tieneCochera, tieneAmenities]);

  return (
    <div className="mx-auto max-w-7xl space-y-8 pb-12">
      <div>
        <h1 className="text-3xl font-extrabold text-white sm:text-4xl flex items-center gap-3">
          <Sparkles className="h-8 w-8 text-emerald-400" />
          Detector de Oportunidades
        </h1>
        <p className="mt-2 text-slate-400">
          Algoritmo inteligente de Machine Learning (RandomForest) entrenado sobre 92.241 departamentos en CABA. Carga el Top 50 de mejores oportunidades globales o filtradas por tus criterios específicos.
        </p>
      </div>

      {/* Filter Toolbar completo */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Filter className="h-4 w-4 text-emerald-400" />
            Filtros del Detector de Oportunidades
          </div>
          {(selectedBarrios.length > 0 || selectedAmbientes || selectedEstado || precioMin || precioMax || banosMin || tieneCochera !== "" || tieneAmenities !== "") && (
            <button
              onClick={() => {
                setSelectedBarrios([]);
                setSelectedAmbientes("");
                setSelectedEstado("");
                setPrecioMin("");
                setPrecioMax("");
                setBanosMin("");
                setTieneCochera("");
                setTieneAmenities("");
              }}
              className="text-xs text-red-400 hover:underline"
            >
              Restablecer Filtros
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-4">
          {/* Barrio Multiselect Dropdown */}
          <div className="relative">
            <label className="block text-xs uppercase text-slate-400 mb-1">Barrios (Múltiple)</label>
            <button
              type="button"
              onClick={() => setShowBarrioDropdown(!showBarrioDropdown)}
              className="flex w-full items-center justify-between rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs text-white focus:outline-none"
            >
              <span className="truncate">
                {selectedBarrios.length === 0
                  ? "Todos los Barrios"
                  : `${selectedBarrios.length} barrio(s) seleccionado(s)`}
              </span>
              <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" />
            </button>

            {showBarrioDropdown && (
              <div className="absolute z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-xl border border-slate-700 bg-slate-950 p-2 shadow-xl">
                <div className="mb-2 flex items-center justify-between border-b border-slate-800 pb-1 text-[11px] text-slate-400">
                  <span>Seleccionar barrios</span>
                  {selectedBarrios.length > 0 && (
                    <button
                      onClick={() => setSelectedBarrios([])}
                      className="text-red-400 hover:underline"
                    >
                      Limpiar
                    </button>
                  )}
                </div>
                {barriosList.map((b) => (
                  <label
                    key={b}
                    className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-slate-200 hover:bg-slate-900 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedBarrios.includes(b)}
                      onChange={() => toggleBarrio(b)}
                      className="rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-emerald-500"
                    />
                    {b}
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Ambientes */}
          <div>
            <label className="block text-xs uppercase text-slate-400 mb-1">Ambientes</label>
            <select
              value={selectedAmbientes}
              onChange={(e) => setSelectedAmbientes(e.target.value ? Number(e.target.value) : "")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="">Cualquier Amb.</option>
              <option value={1}>1 Ambiente</option>
              <option value={2}>2 Ambientes</option>
              <option value={3}>3 Ambientes</option>
              <option value={4}>4+ Ambientes</option>
            </select>
          </div>

          {/* Estado */}
          <div>
            <label className="block text-xs uppercase text-slate-400 mb-1">Estado</label>
            <select
              value={selectedEstado}
              onChange={(e) => setSelectedEstado(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="">Cualquier Estado</option>
              <option value="usado">Usado</option>
              <option value="a estrenar">A estrenar</option>
              <option value="en construccion">En construcción</option>
            </select>
          </div>

          {/* Precio Mínimo */}
          <div>
            <label className="block text-xs uppercase text-slate-400 mb-1">Precio Mín ($ USD)</label>
            <input
              type="number"
              placeholder="Ej: 50000"
              value={precioMin}
              onChange={(e) => setPrecioMin(e.target.value ? Number(e.target.value) : "")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs text-white focus:border-emerald-500 focus:outline-none"
            />
          </div>

          {/* Precio Máximo */}
          <div>
            <label className="block text-xs uppercase text-slate-400 mb-1">Precio Máx ($ USD)</label>
            <input
              type="number"
              placeholder="Ej: 180000"
              value={precioMax}
              onChange={(e) => setPrecioMax(e.target.value ? Number(e.target.value) : "")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs text-white focus:border-emerald-500 focus:outline-none"
            />
          </div>

          {/* Baños Mínimos */}
          <div>
            <label className="block text-xs uppercase text-slate-400 mb-1">Baños Mínimos</label>
            <select
              value={banosMin}
              onChange={(e) => setBanosMin(e.target.value ? Number(e.target.value) : "")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="">Indistinto</option>
              <option value={1}>1+ Baño</option>
              <option value={2}>2+ Baños</option>
              <option value={3}>3+ Baños</option>
            </select>
          </div>

          {/* Cochera */}
          <div>
            <label className="block text-xs uppercase text-slate-400 mb-1">Cochera</label>
            <select
              value={tieneCochera === "" ? "" : tieneCochera ? "true" : "false"}
              onChange={(e) => setTieneCochera(e.target.value === "" ? "" : e.target.value === "true")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="">Indistinto</option>
              <option value="true">Con Cochera</option>
              <option value="false">Sin Cochera</option>
            </select>
          </div>

          {/* Amenities */}
          <div>
            <label className="block text-xs uppercase text-slate-400 mb-1">Amenities</label>
            <select
              value={tieneAmenities === "" ? "" : tieneAmenities ? "true" : "false"}
              onChange={(e) => setTieneAmenities(e.target.value === "" ? "" : e.target.value === "true")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="">Indistinto</option>
              <option value="true">Con Amenities</option>
              <option value="false">Sin Amenities</option>
            </select>
          </div>
        </div>

        {/* Selected Barrios Pills */}
        {selectedBarrios.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-2">
            {selectedBarrios.map((b) => (
              <span
                key={b}
                className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400"
              >
                {b}
                <button onClick={() => toggleBarrio(b)} className="hover:text-white">
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Grid de Oportunidades */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <Loader2 className="h-10 w-10 animate-spin text-emerald-400 mb-4" />
          <p className="text-sm font-semibold">Evaluando modelo RandomForest ML sobre los datos...</p>
        </div>
      ) : opportunities.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {opportunities.map((opp) => (
            <div
              key={opp.id_publicacion}
              className="group relative flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/80 p-6 backdrop-blur-md transition-all hover:border-emerald-500/50 hover:shadow-2xl hover:shadow-emerald-500/10"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-extrabold text-emerald-400">
                    -{opp.descuento_porcentaje}% Oportunidad ML
                  </span>
                  <span className="text-xs font-medium text-slate-400">{opp.portal}</span>
                </div>

                <h3 className="line-clamp-2 text-base font-bold text-white group-hover:text-emerald-400 transition-colors">
                  {opp.titulo_aviso}
                </h3>

                <div className="space-y-2 text-xs text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <MapPin className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span className="font-semibold text-slate-200">{opp.barrio}</span>
                    {opp.direccion && <span>• {opp.direccion}</span>}
                  </div>
                  <div className="flex flex-wrap gap-2 pt-1 text-[11px]">
                    <span className="rounded-md bg-slate-950 px-2 py-1 border border-slate-800">{opp.ambientes} amb</span>
                    <span className="rounded-md bg-slate-950 px-2 py-1 border border-slate-800">{opp.m2_totales} m²</span>
                    <span className="rounded-md bg-slate-950 px-2 py-1 border border-slate-800">{opp.banos} baños</span>
                    {opp.tiene_cochera && <span className="rounded-md bg-emerald-950/60 text-emerald-400 px-2 py-1 border border-emerald-800/50">Cochera</span>}
                    {opp.tiene_amenities && <span className="rounded-md bg-blue-950/60 text-blue-400 px-2 py-1 border border-blue-800/50">Amenities</span>}
                  </div>
                </div>
              </div>

              <div className="mt-6 border-t border-slate-800 pt-4 space-y-3">
                <div className="flex items-baseline justify-between">
                  <div>
                    <p className="text-[11px] uppercase tracking-wider text-slate-400">Precio Publicado</p>
                    <p className="text-2xl font-extrabold text-white">
                      ${opp.precio_usd ? Number(opp.precio_usd).toLocaleString("es-AR") : 0} USD
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-[11px] uppercase tracking-wider text-slate-400">Valor Estimado ML</p>
                    <p className="text-base font-bold text-emerald-400">
                      ${opp.precio_estimado ? Number(opp.precio_estimado).toLocaleString("es-AR") : 0} USD
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between rounded-xl bg-emerald-950/30 border border-emerald-500/20 px-3 py-2 text-xs">
                  <span className="text-slate-300">Margen estimado:</span>
                  <span className="font-extrabold text-emerald-400">
                    +${opp.margen_ganancia_usd ? Number(opp.margen_ganancia_usd).toLocaleString("es-AR") : 0} USD
                  </span>
                </div>

                {opp.url_publicacion && (
                  <a
                    href={opp.url_publicacion}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-xl border border-slate-700 bg-slate-950 py-2.5 text-xs font-semibold text-slate-200 transition-all hover:bg-slate-800 hover:text-white"
                  >
                    Ver Publicación Original <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center text-slate-400">
          No se encontraron oportunidades con los filtros seleccionados. Intenta ampliar el rango de búsqueda.
        </div>
      )}
    </div>
  );
}
