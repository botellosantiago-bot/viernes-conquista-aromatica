import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
export const SALIDA = Easing.bezier(0.16, 1, 0.3, 1); // entradas: llegan rápido y se asientan sin rebote
export const SUAVE = Easing.bezier(0.65, 0, 0.35, 1);

/**
 * Medidas del lienzo. TODO el kit toma el tamaño de aquí (useVideoConfig), así que sirve igual en 16:9 y en 9:16.
 * `u` es una unidad de escala: 1 en ambos formatos (el lado corto siempre mide 1080). Los tamaños de letra se escriben
 * como `u * 120`, y en 16:9 la letra se ve proporcionalmente igual de grande que en vertical.
 */
export const useFormato = () => {
  const { width: w, height: h, fps } = useVideoConfig();
  const vertical = h > w;
  const u = Math.min(w, h) / 1080;
  // Zona segura de texto. 9:16: lo que no tapan los botones de Shorts/Reels/TikTok. 16:9: margen de título (5%).
  const seg = vertical ? { l: 80, t: 250, r: w - 180, b: 1500 } : { l: Math.round(w * 0.05), t: Math.round(h * 0.05), r: Math.round(w * 0.95), b: Math.round(h * 0.95) };
  return { w, h, fps, vertical, u, seg };
};

export const useT = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return { f, t: f / fps, fps };
};

/** Entrada con resorte corto (0 -> 1) que arranca en `inicio` segundos. */
export const useEntrada = (inicio: number, amortiguacion = 16) => {
  const { f, fps } = useT();
  return spring({ frame: f - Math.round(inicio * fps), fps, config: { damping: amortiguacion, stiffness: 180, mass: 0.7 } });
};

export const rampa = (t: number, a: number, b: number, easing: (x: number) => number = SALIDA) => interpolate(t, [a, b], [0, 1], { ...clamp, easing });

/** Opacidad de un elemento visible de `ini` a `fin` con fundidos de `ent` y `sal` segundos. */
export const visible = (t: number, ini: number, fin: number, ent = 0.15, sal = 0.2) => {
  if (t < ini || t > fin) return 0;
  return Math.min(rampa(t, ini, ini + ent, SUAVE), 1 - rampa(t, fin - sal, fin, SUAVE));
};

export const norm = (s: string) =>
  s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]/g, "");

/** Ruido determinista (0..1) para que cada render salga idéntico. */
export const azar = (semilla: number) => {
  const x = Math.sin(semilla * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};
