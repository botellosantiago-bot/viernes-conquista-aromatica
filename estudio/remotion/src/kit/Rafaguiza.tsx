import React from "react";
import { AbsoluteFill, random, spring } from "remotion";
import { COLOR, FUENTE } from "./theme";
import { rampa, useFormato, useT } from "./core";
import type { Rafaguiza as RafaguizaPlan } from "./tipos";

/*
 * RAFAGUIZA. "¡ES HORA DE DARNOS UNA RAFAGUIZA!" y, en cada spray: PSSHT (sonido, lo coloca plan.py) -> destello/rayo/aura -> reacción.
 * El poder CRECE con cada spray: 1.º destello, 2.º rayo, 3.º aura de poder (y las partículas aumentan).
 * Todo va por los BORDES del cuadro: el centro (la cara de Arturo y el frasco) nunca se tapa. No es obligatorio en cada video.
 */
const nivelEn = (t: number, sprays: number[]) => sprays.filter((s) => s <= t).length;

/** Rayo dentado (path SVG) que baja por un costado. */
const rayoPath = (x: number, alto: number, semilla: string, ancho: number) => {
  let d = `M ${x} 0`;
  let y = 0;
  let cx = x;
  let i = 0;
  while (y < alto) {
    y += alto / 9 + random(`${semilla}y${i}`) * 40;
    cx = x + (random(`${semilla}x${i}`) - 0.5) * ancho;
    d += ` L ${cx.toFixed(1)} ${Math.min(y, alto).toFixed(1)}`;
    i++;
  }
  return d;
};

export const TituloRafaguiza: React.FC<{ r: RafaguizaPlan }> = ({ r }) => {
  const { t, f, fps } = useT();
  const { u, vertical, seg, h } = useFormato();
  const fin = r.fin + 0.45;
  if (t < r.inicio - 0.02 || t > fin) return null;
  const e = spring({ frame: f - Math.round(r.inicio * fps), fps, config: { damping: 12, stiffness: 220, mass: 0.8 } });
  const sal = 1 - rampa(t, fin - 0.2, fin);
  const tam = u * (vertical ? 92 : 84);
  const baseY = seg.b - u * (vertical ? 40 : 20);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: sal }}>
      <div style={{ position: "absolute", left: seg.l, width: seg.r - seg.l, bottom: h - baseY, textAlign: "center", transform: `scale(${0.6 + 0.4 * Math.min(1.1, e)}) rotate(${(1 - e) * -3}deg)`, transformOrigin: "50% 100%" }}>
        <div style={{ fontFamily: FUENTE.sans, fontWeight: 900, fontSize: tam, lineHeight: 1, textTransform: "uppercase", color: COLOR.destello, letterSpacing: -0.5, textShadow: `0 0 ${u * 28}px ${COLOR.ambar}, 0 ${u * 5}px ${u * 14}px #000, ${u * 4}px ${u * 4}px 0 ${COLOR.acento}` }}>
          ¡Es hora de darnos una <span style={{ color: COLOR.ambar }}>rafaguiza</span>!
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const EfectosRafaguiza: React.FC<{ r: RafaguizaPlan }> = ({ r }) => {
  const { t } = useT();
  const { w, h, u } = useFormato();
  const sp = r.sprays;
  if (!sp.length || r.poder === false) return null;
  const ultimo = sp[sp.length - 1];
  if (t < sp[0] - 0.05 || t > ultimo + 1.6) return null;
  const nivel = nivelEn(t, sp);
  const total = sp.length;
  const apaga = 1 - rampa(t, ultimo + 0.6, ultimo + 1.6);
  // Destello: pico de 0.14 s en cada spray, más fuerte con el nivel
  const destello = sp.reduce((m, s, i) => {
    const d = t - s;
    return d >= 0 && d < 0.14 ? Math.max(m, (1 - d / 0.14) * (0.5 + 0.1 * (i + 1))) : m;
  }, 0);
  // Aura: crece con cada spray y se apaga después del último
  const intensidad = Math.min(1, nivel / Math.max(2, total)) * apaga;
  // Rayos: a partir del 2.º spray, 0.28 s cada vez, por los costados
  const rayos = sp.map((s, i) => ({ s, i })).filter(({ s, i }) => i >= 1 && t >= s && t < s + 0.28);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {nivel >= 1 ? (
        <AbsoluteFill style={{ boxShadow: `inset 0 0 ${u * (50 + 60 * intensidad)}px ${u * (14 + 26 * intensidad)}px rgba(255,170,60,${0.25 + 0.5 * intensidad}), inset 0 0 ${u * 120}px ${u * 8}px rgba(255,77,109,${0.35 * intensidad})` }} />
      ) : null}
      {destello > 0.01 ? (
        <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 50%, rgba(255,233,176,0) 66%, rgba(255,233,176,${destello}) 100%)` }} />
      ) : null}
      {rayos.map(({ s, i }) => {
        const k = 1 - (t - s) / 0.28;
        const n = Math.min(3, i + 1);
        return (
          <svg key={i} width={w} height={h} style={{ position: "absolute", left: 0, top: 0, opacity: k }}>
            {Array.from({ length: n * 2 }, (_, j) => {
              const lado = j % 2 === 0;
              const x = lado ? w * (0.035 + 0.025 * (j / 2)) : w * (0.965 - 0.025 * Math.floor(j / 2));
              const d = rayoPath(x, h, `r${i}${j}${Math.floor((t - s) * 30)}`, u * 70);
              return (
                <g key={j}>
                  <path d={d} stroke={COLOR.rayo} strokeWidth={u * 14} strokeLinejoin="round" fill="none" opacity={0.35} />
                  <path d={d} stroke="#FFFFFF" strokeWidth={u * 4.5} strokeLinejoin="round" fill="none" />
                </g>
              );
            })}
          </svg>
        );
      })}
      {nivel >= 3
        ? Array.from({ length: 14 + 6 * (nivel - 3) }, (_, i) => {
            const lado = i % 2 === 0;
            const base = random(`p${i}`);
            const y = h * (1.05 - ((t * (0.35 + base * 0.4) + base) % 1.1));
            const x = lado ? w * (0.03 + random(`px${i}`) * 0.16) : w * (0.81 + random(`px${i}`) * 0.16);
            const s = u * (6 + random(`ps${i}`) * 12);
            return <div key={i} style={{ position: "absolute", left: x, top: y, width: s, height: s, borderRadius: "50%", background: i % 3 === 0 ? COLOR.acento : COLOR.destello, boxShadow: `0 0 ${s * 2}px ${COLOR.ambar}`, opacity: apaga * 0.9 }} />;
          })
        : null}
    </AbsoluteFill>
  );
};
