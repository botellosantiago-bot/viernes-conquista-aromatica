import React from "react";
import { Freeze, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp } from "./core";
import type { Medio, PlanResuelto, Stem } from "./tipos";

/** Geometría "cover" con foco: el punto (fx, fy) del video queda lo más centrado posible en el panel (w x h). */
export const coverEnfocado = (fuente: { w: number; h: number }, w: number, h: number, fx: number, fy: number) => {
  const k = Math.max(w / fuente.w, h / fuente.h);
  const sw = fuente.w * k;
  const sh = fuente.h * k;
  const left = -Math.max(0, Math.min(sw - w, fx * sw - w / 2));
  const top = -Math.max(0, Math.min(sh - h, fy * sh - h / 2));
  return { width: sw, height: sh, left, top };
};

/**
 * Video de Arturo. Su audio ES la voz, salvo cuando hay megáfono: entonces el video va mudo y la voz sale de voz.flac, que es
 * la voz original empalmada muestra por muestra con el tramo procesado (ver scripts/plan.py).
 */
export const VideoArturo: React.FC<{
  plan: PlanResuelto;
  stem: Stem;
  w?: number;
  h?: number;
  conAudio?: boolean;
  fx?: number;
  fy?: number;
  escala?: number;
}> = ({ plan, stem, w, h, conAudio = true, fx, fy, escala = 1 }) => {
  const { width, height, fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const W = w ?? width;
  const H = h ?? height;
  const ox = fx ?? plan.foco.x;
  const oy = fy ?? plan.foco.y;
  const g = coverEnfocado(plan.fuente, W, H, ox, oy);
  const mega = plan.firma.cierre?.megafono; // con megáfono la voz sale de voz.flac (Conquista.tsx) y el video va mudo
  const ultimo = Math.max(1, Math.round(plan.duracion_base * fps) - 2); // en la cola se congela el último cuadro
  const voz = conAudio && !mega && (stem === "todo" || stem === "voz");
  const estilo: React.CSSProperties = {
    position: "absolute",
    width: g.width,
    height: g.height,
    left: g.left,
    top: g.top,
    transform: `scale(${escala})`,
    transformOrigin: `${((-g.left + W / 2) / g.width) * 100}% ${((-g.top + H / 2) / g.height) * 100}%`,
  };
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W, height: H, overflow: "hidden", background: "#000" }}>
      {frame <= ultimo ? (
        <OffthreadVideo src={staticFile(plan.video)} muted={!voz} style={estilo} />
      ) : (
        <Freeze frame={ultimo}>
          <OffthreadVideo src={staticFile(plan.video)} muted style={estilo} />
        </Freeze>
      )}
    </div>
  );
};

/** Foto o video de apoyo (close-up del frasco, ilustración): cubre el panel con un empuje lento. */
export const MedioApoyo: React.FC<{ medio: Medio; w: number; h: number; inicio: number; fin: number }> = ({ medio, w, h, inicio, fin }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const t = frame / fps;
  const z = interpolate(t, [inicio, fin], [1, 1.07], clamp);
  const estilo: React.CSSProperties = { position: "absolute", left: 0, top: 0, width: w, height: h, objectFit: "cover", transform: `scale(${z})` };
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: w, height: h, overflow: "hidden", background: "#000" }}>
      {medio.tipo === "video" ? <OffthreadVideo src={staticFile(medio.src)} muted style={estilo} /> : <Img src={staticFile(medio.src)} style={estilo} />}
    </div>
  );
};
