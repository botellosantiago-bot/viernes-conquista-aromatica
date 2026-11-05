import React from "react";
import { AbsoluteFill, spring } from "remotion";
import { COLOR, FUENTE } from "./theme";
import { useFormato, useT, visible } from "./core";

/**
 * TARJETA DE VEREDICTO. Puntos clave (1 a 4), uno por línea, que van entrando. Se coloca de lado (16:9) o abajo (9:16)
 * para no tapar la cara de Arturo ni el frasco.
 */
export const Veredicto: React.FC<{ titulo: string; puntos: string[]; inicio: number; fin: number; lado?: "der" | "izq" | "abajo" }> = ({ titulo, puntos, inicio, fin, lado }) => {
  const { t, f, fps } = useT();
  const { w, h, u, vertical, seg } = useFormato();
  const op = visible(t, inicio, fin, 0.2, 0.3);
  if (op <= 0) return null;
  const pos = lado ?? (vertical ? "abajo" : "der");
  const ancho = vertical ? seg.r - seg.l : w * 0.34;
  const tam = u * (vertical ? 50 : 44);
  const alto = u * 130 + puntos.length * tam * 1.9;
  const left = pos === "izq" ? seg.l : pos === "der" ? seg.r - ancho : seg.l;
  const top = pos === "abajo" ? Math.min(seg.b - alto - u * 230, h - alto - u * 300) : (h - alto) / 2;
  const e = spring({ frame: f - Math.round(inicio * fps), fps, config: { damping: 17, stiffness: 160, mass: 0.8 } });
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: op }}>
      <div style={{ position: "absolute", left, top, width: ancho, padding: `${u * 28}px ${u * 34}px`, borderRadius: u * 34, background: "linear-gradient(160deg, rgba(31,24,18,0.94), rgba(20,16,12,0.94))", border: `${u * 3}px solid ${COLOR.ambar}`, boxShadow: `0 ${u * 20}px ${u * 60}px rgba(0,0,0,0.55)`, transform: `translateY(${(1 - e) * u * 60}px) scale(${0.92 + 0.08 * e})`, boxSizing: "border-box" }}>
        <div style={{ fontFamily: FUENTE.titulo, fontStyle: "italic", fontWeight: 700, fontSize: u * (vertical ? 66 : 58), color: COLOR.ambar, marginBottom: u * 14 }}>{titulo}</div>
        {puntos.map((p, i) => {
          const ei = spring({ frame: f - Math.round((inicio + 0.35 + i * 0.5) * fps), fps, config: { damping: 15, stiffness: 190, mass: 0.7 } });
          return (
            <div key={i} style={{ display: "flex", gap: u * 18, alignItems: "flex-start", marginTop: u * 14, opacity: Math.min(1, ei * 1.5), transform: `translateX(${(1 - ei) * u * 40}px)` }}>
              <div style={{ flex: "0 0 auto", width: tam * 0.9, height: tam * 0.9, borderRadius: "50%", background: i % 2 ? COLOR.acento : COLOR.ambar, color: COLOR.negro, fontFamily: FUENTE.sans, fontWeight: 900, fontSize: tam * 0.62, display: "flex", alignItems: "center", justifyContent: "center", marginTop: tam * 0.08 }}>{i + 1}</div>
              <div style={{ fontFamily: FUENTE.sans, fontWeight: 800, fontSize: tam, lineHeight: 1.12, color: COLOR.crema }}>{p}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** RÓTULO (tercio inferior izquierdo): nombre del perfume y la casa, exactamente como los dio Arturo. */
export const Rotulo: React.FC<{ texto: string; sub?: string | null; inicio: number; fin: number }> = ({ texto, sub, inicio, fin }) => {
  const { t, f, fps } = useT();
  const { u, vertical, seg, h } = useFormato();
  const op = visible(t, inicio, fin, 0.2, 0.3);
  if (op <= 0) return null;
  const e = spring({ frame: f - Math.round(inicio * fps), fps, config: { damping: 16, stiffness: 170, mass: 0.8 } });
  const top = vertical ? seg.t + u * 40 : h * 0.07;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: op }}>
      <div style={{ position: "absolute", left: seg.l, top, transform: `translateX(${(1 - e) * -u * 80}px)` }}>
        <div style={{ height: u * 6, width: u * 120 * e, background: COLOR.ambar, borderRadius: u * 3, marginBottom: u * 14 }} />
        <div style={{ fontFamily: FUENTE.titulo, fontWeight: 900, fontSize: u * (vertical ? 86 : 78), lineHeight: 1.02, color: COLOR.crema, textShadow: `0 ${u * 4}px ${u * 18}px #000` }}>{texto}</div>
        {sub ? <div style={{ fontFamily: FUENTE.sans, fontWeight: 600, fontSize: u * (vertical ? 44 : 40), color: COLOR.dorado, marginTop: u * 8, letterSpacing: 2, textTransform: "uppercase", textShadow: "0 2px 8px #000" }}>{sub}</div> : null}
      </div>
    </AbsoluteFill>
  );
};
