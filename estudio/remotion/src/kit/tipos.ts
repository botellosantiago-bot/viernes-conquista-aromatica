/** Plan resuelto: lo que escribe scripts/plan.py y lee Remotion. Todos los tiempos en segundos del video FINAL. */
export type Palabra = { w: string; s: number; e: number };
export type Medio = { src: string; tipo: "imagen" | "video" };

export type SfxEvento = { t: number; archivo: string; vol: number; dur?: number | null; tag?: string; exacto?: boolean };

export type Beat =
  | { tipo: "palabra"; inicio: number; fin: number; texto: string; efecto: "pop" | "shimmer"; lado?: string | null }
  | { tipo: "ingredientes"; inicio: number; fin: number; items: { nombre: string; t: number; foto?: Medio | null }[] }
  | { tipo: "split" | "apoyo"; inicio: number; fin: number; archivo?: Medio; ilustracion?: "frasco"; etiqueta?: string | null; ia: boolean; modo: "split" | "pip" | "completo"; closeup: boolean }
  | { tipo: "veredicto"; inicio: number; fin: number; titulo: string; puntos: string[]; lado: "der" | "izq" | "abajo" }
  | { tipo: "transicion"; inicio: number; fin: number; estilo: "barrido" | "zoom" | "flash" | "luz" | "iris" | "negro" | "persiana" | "shutter" }
  | { tipo: "remate"; inicio: number; fin: number; sonido: "pop" | "scratch" | "silencio" }
  | { tipo: "revelacion"; inicio: number; fin: number; texto?: string | null; sonido: "shimmer" | "impacto" }
  | { tipo: "rotulo"; inicio: number; fin: number; texto: string; sub?: string | null }
  | { tipo: "zoom"; inicio: number; fin: number; escala: number };

export type OlerBien = { inicio: number; riser_ini: number; riser_fin: number; bien_fin: number; siempre: number; pum: number; frase_fin: number };
export type Megafono = { s: number; e: number; archivo: string; voz: string; texto: string; parcial: boolean };
export type Cierre = { inicio: number; iconos: { like?: number; campanita?: number; suscribete?: number }; megafono?: Megafono };
export type Rafaguiza = { inicio: number; palabra_s: number; fin: number; texto: string; sprays: number[]; poder?: boolean };

export type PlanResuelto = {
  slug: string;
  titulo: string;
  perfume?: string | null;
  fps: number;
  duracion_base: number;
  cola: number;
  video: string;
  fuente: { w: number; h: number };
  foco: { x: number; y: number };
  palabras: Palabra[];
  voz: [number, number][];
  musica: { base: string | null; cierre: string | null; volumen: number };
  firma: { aplausos: { t: number; fin: number; dur: number }[]; oler_bien: OlerBien[]; cierre: Cierre | null; rafaguiza: Rafaguiza | null };
  beats: Beat[];
  silencios: [number, number][];
  sfx: SfxEvento[];
  avisos: string[];
};

export type Stem = "todo" | "voz" | "fx" | "musica" | "cuerdas";
export type PropsConquista = { slug: string; stem?: Stem; plan?: PlanResuelto };
