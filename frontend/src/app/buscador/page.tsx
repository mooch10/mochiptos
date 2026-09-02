"use client";

import { useState, useEffect } from "react";
import { fetchApi, Property } from "@/lib/api";
import { Search, MapPin, ExternalLink, Filter, Loader2, ChevronDown, X } from "lucide-react";

const CABA_BARRIOS_FALLBACK = [
  "Abasto", "Agronomía", "Almagro", "Balvanera", "Barracas", "Belgrano", "Boedo",
  "Caballito", "Chacarita", "Coghlan", "Colegiales", "Constitución", "Flores",
  "Floresta", "La Boca", "La Paternal", "Liniers", "Mataderos", "Monte Castro",
  "Montserrat", "Nueva Pompeya", "Núñez", "Palermo", "Parque Avellaneda",
  "Parque Chacabuco", "Parque Chas", "Parque Patricios", "Puerto Madero",
  "Recoleta", "Retiro", "Saavedra", "San Cristóbal", "San Nicolás", "San Telmo",
  "Versalles", "Villa Crespo", "Villa del Parque", "Villa Devoto",
  "Villa General Mitre", "Villa Lugano", "Villa Luro", "Villa Ortúzar",
  "Villa Pueyrredón", "Villa Real", "Villa Riachuelo", "Villa Santa Rita",
  "Villa Soldati", "Villa Urquiza"
];

export default function BuscadorPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [barriosList, setBarriosList] = useState<string[]>(CABA_BARRIOS_FALLBACK);
  const [loading, setLoading] = useState(false);

  // Filtros del buscador
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
      .then((res) => {
        if (res.data && Array.isArray(res.data) && res.data.length > 0) {
          setBarriosList(res.data);
        }
      })
      .catch((err) => console.error(err));
  }, []);

  useEffect(() => {
    handleSearch();
  }, [selectedBarrios, selectedAmbientes, selectedEstado, precioMin, precioMax, banosMin, tieneCochera, tieneAmenities]);

  const toggleBarrio = (b: string) => {
    if (selectedBarrios.includes(b)) {
      setSelectedBarrios(selectedBarrios.filter((item) => item !== b));
    } else {
      setSelectedBarrios([...selectedBarrios, b]);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = { limit: 100 };
      if (selectedBarrios.length > 0) params.barrios = selectedBarrios;
      if (selectedAmbientes) params.ambientes = selectedAmbientes;
      if (selectedEstado) params.estado = selectedEstado;
      if (precioMin) params.precio_min = precioMin;
      if (precioMax) params.precio_max = precioMax;
      if (banosMin) params.banos_min = banosMin;
      if (tieneCochera !== "") params.tiene_cochera = tieneCochera;
      if (tieneAmenities !== "") params.tiene_amenities = tieneAmenities;

      const res = await fetchApi<{ data: Property[] }>("/market/search", params);
      setProperties(res.data || []);
    } catch (err) {
      console.error("Error en buscador de propiedades:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-8 pb-12">
      <div>
        <h1 className="text-3xl font-extrabold text-white sm:text-4xl flex items-center gap-3">
          <Search className="h-8 w-8 text-blue-400" />
          Buscador Universal de Propiedades por Barrio
        </h1>
        <p className="mt-2 text-slate-400">
          Explora y filtra las 92.241 publicaciones disponibles en toda la Ciudad Autónoma de Buenos Aires.
        </p>
      </div>

      {/* Buscador Interactivo */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 backdrop-blur-md space-y-6">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <Filter className="h-4 w-4 text-blue-400" />
          Panel de Filtros Cruzados Multiselect
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-4">
          {/* Barrio Multiselect */}
          <div className="relative">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Barrios (Múltiple)
            </label>
            <button
              type="button"
              onClick={() => setShowBarrioDropdown(!showBarrioDropdown)}
              className="flex w-full items-center justify-between rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white focus:outline-none"
            >
              <span className="truncate">
                {selectedBarrios.length === 0
                  ? "Todos los Barrios"
                  : `${selectedBarrios.length} seleccionado(s)`}
              </span>
              <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" />
            </button>

            {showBarrioDropdown && (
              <div className="absolute z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-xl border border-slate-700 bg-slate-950 p-2 shadow-xl">
                <div className="mb-2 flex items-center justify-between border-b border-slate-800 pb-1 text-[11px] text-slate-400">
                  <span>Elegir barrios</span>
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
                      className="rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-blue-500"
                    />
                    {b}
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Ambientes */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Ambientes
            </label>
            <select
              value={selectedAmbientes}
              onChange={(e) => setSelectedAmbientes(e.target.value ? Number(e.target.value) : "")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="">Cualquier cantidad</option>
              <option value={1}>1 Ambiente (Monoambiente)</option>
              <option value={2}>2 Ambientes</option>
              <option value={3}>3 Ambientes</option>
              <option value={4}>4+ Ambientes</option>
            </select>
          </div>

          {/* Precio Min */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Precio Mínimo ($ USD)
            </label>
            <input
              type="number"
              placeholder="Ej: 50000"
              value={precioMin}
              onChange={(e) => setPrecioMin(e.target.value ? Number(e.target.value) : "")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Precio Max */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Precio Máximo ($ USD)
            </label>
            <input
              type="number"
              placeholder="Ej: 200000"
              value={precioMax}
              onChange={(e) => setPrecioMax(e.target.value ? Number(e.target.value) : "")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Baños */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Baños Mínimos
            </label>
            <select
              value={banosMin}
              onChange={(e) => setBanosMin(e.target.value ? Number(e.target.value) : "")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="">Indistinto</option>
              <option value={1}>1+ Baño</option>
              <option value={2}>2+ Baños</option>
              <option value={3}>3+ Baños</option>
            </select>
          </div>

          {/* Estado */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Estado Propiedad
            </label>
            <select
              value={selectedEstado}
              onChange={(e) => setSelectedEstado(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="">Cualquier estado</option>
              <option value="usado">Usado</option>
              <option value="a estrenar">A estrenar</option>
              <option value="en construccion">En construcción</option>
            </select>
          </div>

          {/* Cochera */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Cochera
            </label>
            <select
              value={tieneCochera === "" ? "" : tieneCochera ? "true" : "false"}
              onChange={(e) => setTieneCochera(e.target.value === "" ? "" : e.target.value === "true")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="">Indistinto</option>
              <option value="true">Con Cochera</option>
              <option value="false">Sin Cochera</option>
            </select>
          </div>

          {/* Amenities */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Amenities
            </label>
            <select
              value={tieneAmenities === "" ? "" : tieneAmenities ? "true" : "false"}
              onChange={(e) => setTieneAmenities(e.target.value === "" ? "" : e.target.value === "true")}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="">Indistinto</option>
              <option value="true">Con Amenities</option>
              <option value="false">Sin Amenities</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleSearch}
          disabled={loading}
          className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 transition-all hover:brightness-110 flex items-center justify-center gap-2"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Search className="h-4 w-4" /> Buscar Propiedades</>}
        </button>
      </div>

      {/* Grid de Resultados */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
          <Loader2 className="h-10 w-10 animate-spin text-blue-400" />
          <p className="text-base font-bold text-white">Explorando departamentos disponibles...</p>
          <p className="text-xs text-slate-400 max-w-sm text-center">Buscando las mejores coincidencias según tus filtros seleccionados.</p>
        </div>
      ) : properties.length > 0 ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-sm text-slate-400">
            <span>Resultados encontrados: <strong className="text-white">{properties.length} propiedades</strong></span>
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {properties.map((prop) => (
              <div
                key={prop.id_publicacion}
                className="group flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/80 p-6 backdrop-blur-md transition-all hover:border-blue-500/50 hover:shadow-xl hover:shadow-blue-500/10"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="rounded-md border border-slate-700 bg-slate-950 px-2.5 py-1 text-xs font-semibold text-blue-400">
                      {prop.portal}
                    </span>
                    <span className="text-xs text-slate-500 capitalize">{prop.estado_propiedad || "Usado"}</span>
                  </div>

                  <h3 className="line-clamp-2 text-base font-bold text-white group-hover:text-blue-400 transition-colors">
                    {prop.titulo_aviso}
                  </h3>

                  <div className="space-y-2 text-xs text-slate-400">
                    <div className="flex items-center gap-1.5 text-slate-300">
                      <MapPin className="h-4 w-4 text-blue-400 shrink-0" />
                      <span className="font-semibold">{prop.barrio}</span>
                      {prop.direccion && <span>• {prop.direccion}</span>}
                    </div>

                    <div className="flex flex-wrap gap-2 pt-1 text-[11px]">
                      <span className="rounded-md bg-slate-950 px-2 py-1 border border-slate-800">{prop.ambientes} amb</span>
                      <span className="rounded-md bg-slate-950 px-2 py-1 border border-slate-800">{prop.m2_totales} m²</span>
                      <span className="rounded-md bg-slate-950 px-2 py-1 border border-slate-800">{prop.banos} baños</span>
                      {prop.tiene_cochera === true && <span className="rounded-md bg-blue-950/60 text-blue-400 px-2 py-1 border border-blue-800/50">Cochera</span>}
                      {prop.tiene_amenities === true && <span className="rounded-md bg-emerald-950/60 text-emerald-400 px-2 py-1 border border-emerald-800/50">Amenities</span>}
                    </div>
                  </div>
                </div>

                <div className="mt-6 border-t border-slate-800 pt-4 flex items-center justify-between">
                  <div>
                    <p className="text-[11px] uppercase tracking-wider text-slate-400">Precio USD</p>
                    <p className="text-2xl font-extrabold text-white">${prop.precio_usd?.toLocaleString()}</p>
                  </div>

                  {prop.url_publicacion && (
                    <a
                      href={prop.url_publicacion}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2 text-xs font-semibold text-slate-200 transition-all hover:bg-slate-800 hover:text-white flex items-center gap-1"
                    >
                      Ver aviso <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center text-slate-400">
          No se encontraron propiedades que coincidan con la búsqueda.
        </div>
      )}
    </div>
  );
}
