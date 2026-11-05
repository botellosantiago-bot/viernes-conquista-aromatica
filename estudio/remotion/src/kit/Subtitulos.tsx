import React from "react";
import { AbsoluteFill } from "remotion";
import { COLOR, FUENTE } from "./theme";
import { clamp, SALIDA, useFormato, useT } from "./core";
import { interpolate } from "remotion";
import type { Palabra } from "./tipos";

/*
 * SUBTÍTULOS. Salen de las palabras REALES del video (ya revisadas a mano con words.py: marcas, perfumes y notas bien escritos).
 * Frases cortas, la palabra que suena en ámbar, abajo y dentro de la zona segura. `ocultar` apaga el subtítulo mientras otro
 * elemento ya muestra esas mismas palabras en grande (SIEMPRE ESTÁ EN EL PLAN, la Rafaguiza): una idea por pantalla.
 */
type Frase = { palabras: Palabra[]; ini: number; fin: number };

export const agrupar = (ws: Palabra[], maxPalabras: number, maxLetras: number): Frase[] => {
  const frases: Frase[] = [];
  let cur: Palabra[] = [];
  const cerrar = () => {
    if (cur.length) frases.push({ palabras: cur, ini: cur[0].s, fin: cur[cur.length - 1].e });
    cur = [];
  };
  ws.forEach((w, i) => {
    const letras = cur.reduce((n, x) => n + x.w.length + 1, 0) + w.w.length;
    if (cur.length && (cur.length >= maxPalabras || letras > maxLetras || w.s - cur[cur.length - 1].e > 0.55)) cerrar();
    cur.push(w);
    const finDeIdea = /[.?!…]$/.test(w.w) && cur.length >= 2;
    const hayPausa = ws[i + 1] ? ws[i + 1].s - w.e > 0.35 : true;
    if (finDeIdea || (hayPausa && cur.length >= 3)) cerrar();
  });
  cerrar();
  return frases;
};

export const Subtitulos: React.FC<{ palabras: Palabra[]; ocultar?: [number, number][]; acento?: string }> = ({ palabras, ocultar = [], acento = COLOR.ambar }) => {
  const { t } = useT();
  const { vertical, u, seg } = useFormato();
  const frases = React.useMemo(() => agrupar(palabras, vertical ? 4 : 7, vertical ? 22 : 40), [palabras, vertical]);
  if (ocultar.some(([a, b]) => t >= a - 0.05 && t <= b + 0.05)) return null;
  // La frase activa: empieza un poco antes de su primera palabra y se queda hasta la siguiente (máx. 0.35 s después de la última)
  let k = -1;
  for (let i = 0; i < frases.length; i++) {
    const sig = frases[i + 1]?.ini ?? Infinity;
    if (t >= frases[i].ini - 0.06 && t <= Math.min(frases[i].fin + 0.35, sig - 0.02)) {
      k = i;
      break;
    }
  }
  if (k < 0) return null;
  const fr = frases[k];
  const entra = interpolate(t, [fr.ini - 0.06, fr.ini + 0.08], [0, 1], { ...clamp, easing: SALIDA });
  const tam = u * (vertical ? 66 : 58);
  const base = vertical ? seg.b - u * 20 : seg.b - u * 8;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: seg.l,
          width: seg.r - seg.l,
          top: base - tam * 2.6,
          height: tam * 2.6,
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "center",
          opacity: entra,
          transform: `translateY(${(1 - entra) * u * 14}px)`,
        }}
      >
        <div style={{ textAlign: "center", fontFamily: FUENTE.sans, fontWeight: 800, fontSize: tam, lineHeight: 1.08, color: COLOR.crema, letterSpacing: -0.5 }}>
          {fr.palabras.map((p, i) => {
            const activa = t >= p.s - 0.02 && t < p.e + 0.04;
            const dicha = t >= p.e;
            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  marginLeft: tam * 0.13,
                  marginRight: tam * 0.13,
                  color: activa ? acento : COLOR.crema,
                  opacity: dicha || activa ? 1 : 0.88,
                  transform: activa ? `scale(1.04)` : "none",
                  textShadow: `0 ${u * 3}px ${u * 14}px ${COLOR.sombra}, 0 0 ${u * 2}px #000, ${u * 2.5}px ${u * 2.5}px 0 rgba(10,6,3,0.9), -${u * 2.5}px ${u * 2.5}px 0 rgba(10,6,3,0.9), ${u * 2.5}px -${u * 2.5}px 0 rgba(10,6,3,0.9), -${u * 2.5}px -${u * 2.5}px 0 rgba(10,6,3,0.9)`,
                }}
              >
                {p.w}
              </span>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
