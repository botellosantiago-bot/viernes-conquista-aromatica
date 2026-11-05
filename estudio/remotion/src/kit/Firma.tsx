import React from "react";
import { AbsoluteFill, interpolate, random, spring } from "remotion";
import { COLOR, FUENTE } from "./theme";
import { clamp, rampa, SALIDA, SUAVE, useFormato, useT } from "./core";
import type { OlerBien } from "./tipos";

/*
 * FIRMA "EL CANAL DONDE OLER BIEN… ¡SIEMPRE ESTÁ EN EL PLAN!"
 *  - Mientras sube el riser (sonido colocado por plan.py): un brillo ámbar crece por los bordes. No tapa nada.
 *  - Corte seco: el brillo se va de golpe cuando el riser termina.
 *  - En "SIEMPRE" cae el PUM (sonido) y aquí entran el texto, un anillo de choque y un temblor breve de cámara.
 * El texto se pone en el tercio inferior (donde van los subtítulos, que se apagan mientras tanto): no tapa cara ni frasco.
 */
export const ahoraImpacto = (t: number, pums: number[]) => {
  // Temblor de cámara: devuelve {x, y, s} para envolver la escena. Dura 0.28 s y se apaga.
  for (const p of pums) {
    const d = t - p;
    if (d >= 0 && d < 0.28) {
      const env = (1 - d / 0.28) ** 2;
      return { x: (random(`sx${p}${Math.round(d * 30)}`) - 0.5) * 22 * env, y: (random(`sy${p}${Math.round(d * 30)}`) - 0.5) * 18 * env, s: 1 + 0.035 * env };
    }
  }
  return { x: 0, y: 0, s: 1 };
};

export const BrilloRiser: React.FC<{ o: OlerBien }> = ({ o }) => {
  const { t } = useT();
  if (t < o.riser_ini || t >= o.riser_fin) return null; // corte seco: en cuanto termina el riser, se apaga
  const k = rampa(t, o.riser_ini, o.riser_fin, (x) => x * x);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", boxShadow: `inset 0 0 ${40 + 80 * k}px ${8 + 24 * k}px rgba(242,168,59,${0.12 + 0.45 * k})` }} />
  );
};

export const GolpeSiempre: React.FC<{ o: OlerBien }> = ({ o }) => {
  const { t, f, fps } = useT();
  const { u, vertical, seg, w, h } = useFormato();
  const fin = o.frase_fin + 0.45;
  if (t < o.siempre - 0.02 || t > fin) return null;
  const e = spring({ frame: f - Math.round(o.siempre * fps), fps, config: { damping: 11, stiffness: 240, mass: 0.8 } });
  const sal = interpolate(t, [fin - 0.2, fin], [1, 0], clamp);
  const anillo = rampa(t, o.siempre, o.siempre + 0.55, SALIDA);
  const tam = u * (vertical ? 128 : 112);
  const baseY = seg.b - u * (vertical ? 40 : 20);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: sal }}>
      {t < o.siempre + 0.6 ? (
        <div style={{ position: "absolute", left: w / 2 - u * 350 * anillo, top: baseY - u * 170 - u * 350 * anillo, width: u * 700 * anillo, height: u * 700 * anillo, borderRadius: "50%", border: `${u * 10 * (1 - anillo)}px solid ${COLOR.ambar}`, opacity: 1 - anillo, boxSizing: "border-box" }} />
      ) : null}
      <div style={{ position: "absolute", left: seg.l, width: seg.r - seg.l, bottom: h - baseY, textAlign: "center", transform: `scale(${0.5 + 0.5 * Math.min(1.12, e)})`, transformOrigin: "50% 100%" }}>
        <div style={{ fontFamily: FUENTE.sans, fontWeight: 900, fontSize: tam, lineHeight: 0.98, color: COLOR.crema, textTransform: "uppercase", letterSpacing: -1, textShadow: `0 ${u * 5}px ${u * 20}px #000, ${u * 5}px ${u * 5}px 0 ${COLOR.acento}` }}>
          <span style={{ color: COLOR.ambar }}>¡Siempre</span> {vertical ? <br /> : null}está en el plan!
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** APLAUSOS: confeti dorado sobrio por los costados mientras suena el aplauso breve (el audio lo pone plan.py). */
export const Aplausos: React.FC<{ t0: number; dur: number }> = ({ t0, dur }) => {
  const { t } = useT();
  const { w, h, u } = useFormato();
  if (t < t0 - 0.05 || t > t0 + dur) return null;
  const k = (t - t0) / dur;
  // Confeti dorado sobrio que cae por los costados; el centro (la cara de Arturo) queda libre
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: 1 - rampa(t, t0 + dur * 0.55, t0 + dur, SUAVE) }}>
      {Array.from({ length: 22 }, (_, i) => {
        const lado = i % 2 === 0 ? 0 : 1;
        const x = (lado ? w - u * 40 : u * 40) + (lado ? -1 : 1) * random(`ax${i}`) * w * 0.17;
        const y0 = -u * 40 - random(`ay${i}`) * h * 0.2;
        const y = y0 + k * (h * 0.55 + random(`av${i}`) * h * 0.35);
        const s = u * (10 + random(`as${i}`) * 14);
        return <div key={i} style={{ position: "absolute", left: x + Math.sin(k * 7 + i) * u * 16, top: y, width: s, height: s * 0.6, background: i % 4 === 0 ? COLOR.acento : i % 2 ? COLOR.ambar : COLOR.destello, transform: `rotate(${k * 600 + i * 40}deg)`, borderRadius: 2, opacity: 0.9 }} />;
      })}
    </AbsoluteFill>
  );
};
