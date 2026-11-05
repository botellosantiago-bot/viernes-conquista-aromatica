import React from "react";
import { AbsoluteFill } from "remotion";
import { COLOR } from "./theme";
import { useFormato, useT } from "./core";

/*
 * TRANSICIONES. Adaptado del kit de transiciones del estudio: aquí todo toma el tamaño de la composición (useVideoConfig),
 * así que sirve en 16:9 y en 9:16. Regla del manual: preferir cortes limpios; barridos, zooms y whooshes SOLO en cambios reales
 * de idea, lugar o energía. El whoosh lo coloca plan.py (variado, nunca seguido). `inicio` es el segundo exacto del corte.
 */
export type EstiloTransicion = "barrido" | "zoom" | "flash" | "luz" | "iris" | "negro" | "persiana" | "shutter";
export type Transicion = { estilo: EstiloTransicion; inicio: number };

const tramo = (t: number, a: number, b: number) => Math.min(1, Math.max(0, (t - a) / (b - a)));
const entra = (x: number) => x * x * x * x;
const sale = (x: number) => 1 - entra(1 - x);
const liso = (x: number) => x * x * (3 - 2 * x);
const campana = (d: number, a: number, b: number) => (d < 0 ? liso(tramo(d, -a, 0)) : 1 - liso(tramo(d, 0, b)));

type Est = { s: number; x: number; y: number; blurX: number; blurY: number; brillo: number; peso: number };
const neutro = (): Est => ({ s: 1, x: 0, y: 0, blurX: 0, blurY: 0, brillo: 1, peso: 0 });

const estado = (lista: Transicion[], t: number, w: number): Est => {
  let mejor = neutro();
  for (const { estilo, inicio } of lista) {
    const d = t - inicio;
    if (d < -0.45 || d > 0.45) continue;
    const e = neutro();
    if (estilo === "barrido") {
      const k = d < 0 ? entra(tramo(d, -0.3, 0)) : 1 - sale(tramo(d, 0, 0.3));
      e.x = (d < 0 ? -1 : 1) * w * 0.22 * k;
      e.blurX = 38 * k;
      e.s = 1 + 0.75 * k * (w > 1500 ? 0.3 : 1);
      e.peso = k;
    } else if (estilo === "zoom") {
      const k = d < 0 ? entra(tramo(d, -0.2, 0)) : 1 - sale(tramo(d, 0, 0.4));
      e.s = 1 + (d < 0 ? 0.2 : 0.3) * k;
      e.blurX = e.blurY = 14 * k;
      e.peso = k;
    } else if (estilo === "luz") {
      const k = campana(d, 0.25, 0.35);
      e.brillo = 1 + 0.18 * k;
      e.peso = k;
    } else if (estilo === "shutter") {
      const k = d < 0 ? entra(tramo(d, -0.25, 0)) : 1 - sale(tramo(d, 0.05, 0.3));
      e.blurY = 20 * k;
      e.peso = k;
    } else if (estilo === "negro" || estilo === "iris" || estilo === "persiana") {
      const k = campana(d, 0.25, 0.25);
      e.s = 1 + 0.03 * k;
      e.peso = k;
    } else if (estilo === "flash") {
      const k = d < 0 ? entra(tramo(d, -0.1, 0)) : 1 - sale(tramo(d, 0, 0.2));
      e.s = 1 + 0.03 * k;
      e.peso = k;
    }
    if (e.peso > mejor.peso) mejor = e;
  }
  return mejor;
};

const Capa: React.FC<{ tr: Transicion; t: number; w: number; h: number }> = ({ tr, t, w, h }) => {
  const d = t - tr.inicio;
  if (d < -0.45 || d > 0.6) return null;
  if (tr.estilo === "flash") {
    const o = d < 0 ? entra(tramo(d, -0.1, 0)) : 1 - sale(tramo(d, 0, 0.2));
    return o > 0.004 ? <AbsoluteFill style={{ background: COLOR.destello, opacity: o, pointerEvents: "none" }} /> : null;
  }
  if (tr.estilo === "negro") {
    const o = campana(d, 0.25, 0.25);
    return o > 0.003 ? <AbsoluteFill style={{ background: COLOR.negro, opacity: o, pointerEvents: "none" }} /> : null;
  }
  if (tr.estilo === "luz") {
    // Fuga de luz cálida (ámbar): vela y dos manchas que cruzan; en `inicio` lavan la imagen sin llegar al negro.
    const k = campana(d, 0.25, 0.35);
    if (k <= 0.003) return null;
    const p = (d + 0.25) / 0.6;
    const manchas = [
      { c: "255,208,150", r: w * 0.7, y: 0.28, x0: -0.4, x1: 0.8 },
      { c: "255,138,58", r: w * 0.55, y: 0.65, x0: 1.4, x1: 0.15 },
    ];
    return (
      <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen" }}>
        <AbsoluteFill style={{ background: `rgba(255,190,120,${(0.8 * k).toFixed(3)})` }} />
        {manchas.map((m, i) => (
          <AbsoluteFill key={i} style={{ background: `radial-gradient(circle ${m.r}px at ${(m.x0 + (m.x1 - m.x0) * p) * w}px ${m.y * h}px, rgba(${m.c},${k.toFixed(3)}) 0%, rgba(${m.c},0) 100%)` }} />
        ))}
      </AbsoluteFill>
    );
  }
  if (tr.estilo === "iris") {
    const rMax = Math.hypot(w / 2, h / 2) + 6;
    const r = d < 0 ? rMax * (1 - liso(tramo(d, -0.28, 0))) : d < 0.04 ? 0 : rMax * liso(tramo(d, 0.04, 0.34));
    if (r >= rMax) return null;
    return <AbsoluteFill style={{ pointerEvents: "none", background: r < 0.5 ? COLOR.negro : `radial-gradient(circle at 50% 50%, transparent ${r.toFixed(1)}px, ${COLOR.negro} ${(r + 3).toFixed(1)}px)` }} />;
  }
  if (tr.estilo === "persiana") {
    const N = 8;
    const alto = h / N;
    const tiras: React.ReactNode[] = [];
    for (let i = 0; i < N; i++) {
      const cierra = d < 0.01;
      const k = cierra ? liso(tramo(d, -0.28 + i * 0.02, -0.14 + i * 0.02)) : 1 - liso(tramo(d, 0.04 + i * 0.02, 0.18 + i * 0.02));
      if (k <= 0.002) continue;
      tiras.push(<div key={i} style={{ position: "absolute", left: 0, top: i * alto - 0.5, width: w, height: alto + 1, background: COLOR.negro, transform: `scaleY(${k.toFixed(4)})` }} />);
    }
    return <AbsoluteFill style={{ pointerEvents: "none" }}>{tiras}</AbsoluteFill>;
  }
  if (tr.estilo === "shutter") {
    const k = d < 0 ? entra(tramo(d, -0.25, 0)) : d < 0.05 ? 1 : 1 - sale(tramo(d, 0.05, 0.3));
    if (k <= 0) return null;
    return (
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div style={{ position: "absolute", left: 0, top: 0, width: w, height: (h / 2) * k, background: COLOR.negro }} />
        <div style={{ position: "absolute", left: 0, bottom: 0, width: w, height: (h / 2) * k, background: COLOR.negro }} />
      </AbsoluteFill>
    );
  }
  return null;
};

export const Transiciones: React.FC<{ lista: Transicion[]; children: React.ReactNode }> = ({ lista, children }) => {
  const { t } = useT();
  const { w, h } = useFormato();
  const e = estado(lista, t, w);
  const blur = e.blurX > 0.4 || e.blurY > 0.4;
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      {blur ? (
        <svg width="0" height="0" style={{ position: "absolute" }}>
          <filter id="tr-blur" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation={`${e.blurX.toFixed(1)} ${e.blurY.toFixed(1)}`} />
          </filter>
        </svg>
      ) : null}
      <AbsoluteFill
        style={{
          scale: String(+e.s.toFixed(4)),
          translate: `${+e.x.toFixed(2)}px ${+e.y.toFixed(2)}px`,
          filter: [blur ? "url(#tr-blur)" : "", e.brillo > 1.005 ? `brightness(${e.brillo.toFixed(3)})` : ""].filter(Boolean).join(" ") || undefined,
        }}
      >
        {children}
      </AbsoluteFill>
      {lista.map((tr) => (
        <Capa key={`${tr.estilo}-${tr.inicio}`} tr={tr} t={t} w={w} h={h} />
      ))}
    </AbsoluteFill>
  );
};
