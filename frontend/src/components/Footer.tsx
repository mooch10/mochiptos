"use client";

import { useState } from "react";
import { X, ShieldCheck, FileText, Lock } from "lucide-react";

export function Footer() {
  const [activeModal, setActiveModal] = useState<"privacy" | "terms" | "disclaimer" | null>(null);

  return (
    <>
      <footer className="border-t border-slate-800/80 bg-slate-950 py-8 text-center text-xs text-slate-500">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6 lg:px-8">
          <p>© 2026 Mochiptos - Inteligencia Inmobiliaria. Todos los derechos reservados.</p>
          
          <div className="flex flex-wrap items-center justify-center gap-4 text-slate-400">
            <button
              onClick={() => setActiveModal("privacy")}
              className="transition-colors hover:text-blue-400 hover:underline"
            >
              Políticas de Privacidad
            </button>
            <span>•</span>
            <button
              onClick={() => setActiveModal("terms")}
              className="transition-colors hover:text-blue-400 hover:underline"
            >
              Términos de Servicio
            </button>
            <span>•</span>
            <button
              onClick={() => setActiveModal("disclaimer")}
              className="transition-colors hover:text-blue-400 hover:underline"
            >
              Aviso Legal & ML
            </button>
          </div>
        </div>
      </footer>

      {/* Modal Emergente */}
      {activeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8 shadow-2xl text-slate-300">
            {/* Header Modal */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <div className="flex items-center gap-2.5 text-white font-bold text-lg">
                {activeModal === "privacy" && <Lock className="h-5 w-5 text-blue-400" />}
                {activeModal === "terms" && <FileText className="h-5 w-5 text-emerald-400" />}
                {activeModal === "disclaimer" && <ShieldCheck className="h-5 w-5 text-purple-400" />}
                <span>
                  {activeModal === "privacy" && "Políticas de Privacidad"}
                  {activeModal === "terms" && "Términos y Condiciones de Uso"}
                  {activeModal === "disclaimer" && "Aviso Legal y Transparencia de ML"}
                </span>
              </div>
              <button
                onClick={() => setActiveModal(null)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Contenido Modal */}
            <div className="space-y-4 text-sm leading-relaxed text-slate-300">
              {activeModal === "privacy" && (
                <>
                  <p>
                    En <strong>Mochiptos - Inteligencia Inmobiliaria</strong> nos tomamos muy en serio la privacidad y protección de los datos de nuestros usuarios.
                  </p>
                  <h4 className="font-semibold text-white pt-2">1. Recopilación de Información</h4>
                  <p>
                    Esta plataforma opera principalmente de manera informativa y analítica. No solicitamos datos personales sensibles para la consulta de estadísticas de mercado, algoritmos de oportunidad ni calculadoras financieras.
                  </p>
                  <h4 className="font-semibold text-white pt-2">2. Uso de Datos Inmobiliarios</h4>
                  <p>
                    Todos los datos de precios, barrios y superficies provienen de fuentes públicas y de agregación automatizada de ofertas inmobiliarias en CABA. No almacenamos datos de propietarios particulares.
                  </p>
                  <h4 className="font-semibold text-white pt-2">3. Cookies y Almacenamiento Local</h4>
                  <p>
                    Utilizamos únicamente cookies técnicas de sesión y almacenamiento local para mantener las preferencias de navegación del usuario (como filtros aplicados y temas visuales).
                  </p>
                </>
              )}

              {activeModal === "terms" && (
                <>
                  <p>
                    Al acceder y utilizar la plataforma <strong>Mochiptos</strong>, el usuario acepta los siguientes términos de servicio:
                  </p>
                  <h4 className="font-semibold text-white pt-2">1. Uso del Servicio</h4>
                  <p>
                    Mochiptos provee herramientas de Big Data y estimaciones basadas en Machine Learning como servicio gratuito de consulta informativa para el mercado de departamentos en CABA.
                  </p>
                  <h4 className="font-semibold text-white pt-2">2. Propiedad Intelectual</h4>
                  <p>
                    Los modelos estadísticos, interfaces de usuario, branding y código fuente de la plataforma pertenecen a sus creadores y están protegidos por licencias de software libre e intelectual.
                  </p>
                  <h4 className="font-semibold text-white pt-2">3. Disponibilidad</h4>
                  <p>
                    Nos reservamos el derecho de actualizar, modificar o pausar temporalmente los motores de búsqueda o las APIs de cálculo por tareas de mantenimiento sin previo aviso.
                  </p>
                </>
              )}

              {activeModal === "disclaimer" && (
                <>
                  <p>
                    Por favor lea atentamente esta exención de responsabilidad respecto a las predicciones algorítmicas de mercado:
                  </p>
                  <h4 className="font-semibold text-white pt-2">1. Carácter Informativo y No Financiero</h4>
                  <p>
                    Los precios estimados y los porcentajes de descuento etiquetados como <em>"Oportunidad ML"</em> son resultado de modelos matemáticos (RandomForest / Regresión Regularizada) y filtrados estadísticos (IQR). <strong>No constituyen asesoramiento financiero, inmobiliario ni tasación oficial.</strong>
                  </p>
                  <h4 className="font-semibold text-white pt-2">2. Verificación de Ofertas</h4>
                  <p>
                    El usuario debe verificar de manera independiente con inmobiliarias o martilleros colegiados la veracidad, estado real, títulos de propiedad y vigencia de cualquier inmueble antes de tomar decisiones de inversión.
                  </p>
                  <h4 className="font-semibold text-white pt-2">3. Calculadoras Financieras</h4>
                  <p>
                    Las proyecciones de ICL, IPC y Créditos UVA son estimativas en base a los índices publicados por el Banco Central de la República Argentina (BCRA) e INDEC.
                  </p>
                </>
              )}
            </div>

            {/* Footer Modal */}
            <div className="mt-6 border-t border-slate-800 pt-4 flex justify-end">
              <button
                onClick={() => setActiveModal(null)}
                className="rounded-xl bg-blue-600 px-5 py-2 text-sm font-semibold text-white transition-all hover:bg-blue-500 shadow-md shadow-blue-500/20"
              >
                Entendido
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
