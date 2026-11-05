import React from "react";
import { AbsoluteFill, spring } from "remotion";
import { COLOR, FUENTE } from "./theme";
import { useFormato, useT, visible } from "./core";
import { IconoCampana, IconoLike, IconoMegafono, IconoSuscribir } from "./Iconos";
import type { Cierre as CierrePlan } from "./tipos";

/*
 * CIERRE DEL CANAL.
 *  - Las cuerdas entran suaves al empezar "Hermosas y hermosos, denle like" (las pone Mezcla.Musica) y quedan debajo de la voz.
 *  - Iconos DISCRETOS y sincronizados: like, campanita, suscríbete. Pequeños, en la esquina de la zona segura; no son publicidad invasiva.
 *  - Megáfono: el efecto de voz SOLO cubre "a lo que desean proyectar" (VideoArturo apaga la voz original en esos cuadros
 *    y suena el tramo procesado por ffmpeg). Aquí solo hay una señal visual pequeña, sin tapar nada.
 */
const DUR_ICONO = 1.6;

const Icono: React.FC<{ tipo: "like" | "campanita" | "suscribete"; t0: number; indice: number }> = ({ tipo, t0, indice }) => {
  const { t, f, fps } = useT();
  const { u, vertical, seg } = useFormato();
  const op = visible(t, t0 - 0.04, t0 + DUR_ICONO, 0.12, 0.3);
  if (op <= 0) return null;
  const e = spring({ frame: f - Math.round(t0 * fps), fps, config: { damping: 11, stiffness: 220, mass: 0.7 } });
  const tam = u * (vertical ? 96 : 84);
  const etiqueta = tipo === "like" ? "Like" : tipo === "campanita" ? "Campanita" : "Suscríbete";
  const Ico = tipo === "like" ? IconoLike : tipo === "campanita" ? IconoCampana : IconoSuscribir;
  const color = tipo === "suscribete" ? COLOR.acento : COLOR.ambar;
  const mueve = tipo === "campanita" ? Math.sin((t - t0) * 24) * 14 * Math.max(0, 1 - (t - t0)) : 0;
  return (
    <div style={{ position: "absolute", right: vertical ? 1080 - seg.r : 1920 - seg.r, top: seg.t + u * (vertical ? 30 : 20) + indice * u * (vertical ? 122 : 108), opacity: op, transform: `scale(${0.4 + 0.6 * Math.min(1.15, e)})`, transformOrigin: "100% 0%", display: "flex", alignItems: "center", gap: u * 14, padding: `${u * 10}px ${u * 24}px ${u * 10}px ${u * 14}px`, borderRadius: u * 60, background: "rgba(20,16,12,0.82)", border: `${u * 2.5}px solid ${color}` }}>
      <div style={{ transform: `rotate(${mueve}deg)`, display: "flex" }}>
        <Ico size={tam * 0.62} color={color} />
      </div>
      <div style={{ fontFamily: FUENTE.sans, fontWeight: 800, fontSize: tam * 0.4, color: COLOR.crema, letterSpacing: 0.3 }}>{etiqueta}</div>
    </div>
  );
};

export const CierreCanal: React.FC<{ c: CierrePlan }> = ({ c }) => {
  const { t, f, fps } = useT();
  const { u, vertical, seg } = useFormato();
  const mg = c.megafono;
  const lista = (["like", "campanita", "suscribete"] as const)
    .filter((k) => c.iconos[k] !== undefined)
    .map((k) => ({ tipo: k, t0: c.iconos[k] as number }))
    .sort((a, b) => a.t0 - b.t0);
  const enMega = mg ? visible(t, mg.s - 0.05, mg.e + 0.1, 0.1, 0.15) : 0;
  const pulso = mg ? Math.sin(((t - mg.s) * Math.PI * 2) / 0.45) * 0.5 + 0.5 : 0;
  const e = mg ? spring({ frame: f - Math.round(mg.s * fps), fps, config: { damping: 12, stiffness: 200, mass: 0.7 } }) : 0;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {lista.map((x, i) => (
        <Icono key={x.tipo} tipo={x.tipo} t0={x.t0} indice={lista.slice(0, i).filter((y) => y.t0 + DUR_ICONO > x.t0).length} />
      ))}
      {mg && enMega > 0 ? (
        <div style={{ position: "absolute", right: (vertical ? 1080 : 1920) - seg.r, top: seg.t + u * (vertical ? 30 : 20), opacity: enMega, transform: `scale(${0.5 + 0.5 * Math.min(1.1, e)})`, transformOrigin: "100% 0%", display: "flex", alignItems: "center", gap: u * 14 }}>
          <div style={{ width: u * 100, height: u * 100, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(20,16,12,0.82)", border: `${u * 3}px solid ${COLOR.acento}`, boxShadow: `0 0 ${u * (20 + 40 * pulso)}px ${COLOR.acento}` }}>
            <IconoMegafono size={u * 58} color={COLOR.destello} />
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
