const API_BASE = typeof window !== "undefined"
  ? `${window.location.origin}/api`
  : `${process.env.NEXT_PUBLIC_API_URL || "https://mochiptos.onrender.com"}/api`;

export async function fetchApi<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
  const url = new URL(`${API_BASE}${endpoint}`);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        if (Array.isArray(value)) {
          value.forEach(val => url.searchParams.append(key, String(val)));
        } else {
          url.searchParams.append(key, String(value));
        }
      }
    });
  }

  try {
    const response = await fetch(url.toString(), {
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      console.warn(`API Error: ${response.status} ${response.statusText}`);
      return { status: "error", count: 0, data: [] } as unknown as T;
    }

    return await response.json();
  } catch (err) {
    return { status: "error", count: 0, data: [] } as unknown as T;
  }
}

export interface IclResult {
  monto_inicial: number;
  monto_actualizado: number;
  porcentaje_aumento: number;
  icl_inicio: number;
  icl_fin: number;
  fecha_inicio_usada: string;
  fecha_fin_usada: string;
}

export interface IpcResult {
  monto_inicial: number;
  monto_actualizado: number;
  porcentaje_aumento: number;
  meses_evaluados: number;
  detalle_meses: Array<{ fecha: string; ipc_mensual: number }>;
}

export interface UvaResult {
  monto_prestamo_usd: number;
  monto_prestamo_ars: number;
  monto_prestamo_uva: number;
  cuota_inicial_uva: number;
  cuota_inicial_ars: number;
  cuota_inicial_usd: number;
  plazo_meses: number;
  tasa_tna: number;
  valor_uva_usado: number;
  dolar_usado: number;
}

export interface MarketM2Item {
  barrio: string;
  mediana_precio_m2: number;
  promedio_precio_m2: number;
  mediana_precio_usd: number;
  total_publicaciones: number;
}

export interface Property {
  id_publicacion: string;
  portal: string;
  titulo_aviso: string;
  barrio: string;
  direccion?: string;
  ambientes: number;
  banos: number;
  estado_propiedad: string;
  precio_usd: number;
  m2_totales: number;
  m2_cubiertos?: number;
  precio_m2?: number;
  expensas?: number;
  antiguedad?: number;
  tiene_cochera: boolean;
  tiene_amenities: boolean;
  url_publicacion?: string;
  precio_estimado?: number;
  margen_ganancia_usd?: number;
  descuento_porcentaje?: number;
}

export interface NewsItem {
  titulo: string;
  resumen: string;
  link: string;
}
