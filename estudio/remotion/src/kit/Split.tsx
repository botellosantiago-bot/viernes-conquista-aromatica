import React from "react";
import { AbsoluteFill, interpolate } from "remotion";
import { COLOR, FUENTE } from "./theme";
import { clamp, SUAVE, useEntrada, useFormato, useT, visible } from "./core";
import { MedioApoyo, VideoArturo } from "./Fondo";
import type { Medio, PlanResuelto, Stem } from "./tipos";

/**
 * FRASCO ILUSTRADO (genérico). Es una ILUSTRACIÓN estilizada, no el frasco real de Arturo: no lleva etiqueta ni marca, y cuando se usa
 * se rotula "Ilustración". Sirve para "el perfume sale disparado" cuando no hay foto. Nunca sustituye al frasco de verdad.
 */
export const FrascoIlustrado: React.FC<{ w: number; h: number; progreso: number }> = ({ w, h, progreso }) => {
  const sube = interpolate(progreso, [0, 1], [0.15, -0.55], { ...clamp, easing: SUAVE });
  const s = Math.min(w, h) / 600;
  return (
    <div style={{ position: "absolute", inset: 0, background: `radial-gradient(circle at 50% 70%, #3A2A1A 0%, ${COLOR.negro} 70%)`, overflow: "hidden" }}>
      {Array.from({ length: 26 }, (_, i) => (
        <div key={i} style={{ position: "absolute", left: ((i * 137) % 100) + "%", top: ((i * 71) % 100) + "%", width: 3 + (i % 3) * 2, height: 3 + (i % 3) * 2, borderRadius: "50%", background: COLOR.dorado, opacity: 0.35 + (i % 4) * 0.12 }} />
      ))}
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ position: "absolute", left: 0, top: 0 }}>
        <defs>
          <linearGradient id="liq" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#FFC25A" />
            <stop offset="1" stopColor="#C97B1A" />
          </linearGradient>
          <linearGradient id="fuego" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#FFF3C4" />
            <stop offset="0.5" stopColor="#FF9F2E" />
            <stop offset="1" stopColor="#FF4D6D" stopOpacity="0" />
          </linearGradient>
        </defs>
        <g transform={`translate(${w / 2}, ${h * (0.5 + sube)}) scale(${s})`}>
          <path d="M-44 70 Q0 360 44 70 Q0 150 -44 70z" fill="url(#fuego)" opacity={0.85} transform={`scale(1, ${0.6 + progreso * 0.9})`} />
          <rect x="-82" y="-130" width="164" height="210" rx="26" fill="rgba(255,244,224,0.14)" stroke={COLOR.crema} strokeWidth="5" />
          <rect x="-70" y="-30" width="140" height="98" rx="16" fill="url(#liq)" opacity="0.92" />
          <rect x="-22" y="-176" width="44" height="50" rx="8" fill="rgba(255,244,224,0.2)" stroke={COLOR.crema} strokeWidth="5" />
          <rect x="-34" y="-224" width="68" height="52" rx="12" fill={COLOR.dorado} stroke={COLOR.crema} strokeWidth="4" />
          <path d="M-60 -100 L-44 -100 L-44 40" stroke="rgba(255,255,255,0.5)" strokeWidth="7" strokeLinecap="round" fill="none" />
        </g>
      </svg>
    </div>
  );
};

const Contenido: React.FC<{ archivo?: Medio; ilustracion?: "frasco"; w: number; h: number; inicio: number; fin: number }> = ({ archivo, ilustracion, w, h, inicio, fin }) => {
  const { t } = useT();
  if (archivo) return <MedioApoyo medio={archivo} w={w} h={h} inicio={inicio} fin={fin} />;
  if (ilustracion === "frasco") return <FrascoIlustrado w={w} h={h} progreso={interpolate(t, [inicio, fin], [0, 1], clamp)} />;
  return null;
};

const Etiqueta: React.FC<{ texto: string; ia: boolean; x: number; y: number }> = ({ texto, ia, x, y }) => {
  const { u } = useFormato();
  return (
    <div style={{ position: "absolute", left: x, top: y, padding: `${u * 8}px ${u * 20}px`, borderRadius: u * 30, background: ia ? "rgba(20,16,12,0.8)" : COLOR.ambar, color: ia ? COLOR.dorado : COLOR.negro, fontFamily: FUENTE.sans, fontWeight: 800, fontSize: u * 34, border: ia ? `${u * 2}px solid ${COLOR.dorado}` : "none", letterSpacing: 0.5 }}>
      {texto}
    </div>
  );
};

/**
 * PANTALLA DIVIDIDA / PiP. Arturo ABAJO, el apoyo (perfume, animación o la escena narrada) ARRIBA.
 *  - modo "split": dos paneles a todo lo ancho (los dos formatos).
 *  - modo "pip": el apoyo ocupa todo y Arturo queda en un recuadro inferior (útil en 16:9 si la franja le corta la cara).
 */
export const SplitApoyo: React.FC<{ plan: PlanResuelto; stem: Stem; archivo?: Medio; ilustracion?: "frasco"; inicio: number; fin: number; modo: "split" | "pip"; etiqueta?: string | null; ia: boolean }> = ({ plan, stem, archivo, ilustracion, inicio, fin, modo, etiqueta, ia }) => {
  const { t } = useT();
  const { w, h, vertical, u } = useFormato();
  const op = visible(t, inicio, fin, 0.18, 0.2);
  const e = useEntrada(inicio, 18);
  if (op <= 0) return null;
  const altoArriba = vertical ? h * 0.5 : h * 0.58;
  const altoAbajo = h - altoArriba;
  return (
    <AbsoluteFill style={{ opacity: op, background: COLOR.negro }}>
      {modo === "split" ? (
        <>
          <div style={{ position: "absolute", left: 0, top: 0, width: w, height: altoArriba, overflow: "hidden", transform: `translateY(${(1 - e) * -altoArriba * 0.25}px)` }}>
            <Contenido archivo={archivo} ilustracion={ilustracion} w={w} h={altoArriba} inicio={inicio} fin={fin} />
            {etiqueta ? <Etiqueta texto={etiqueta} ia={ia} x={vertical ? 80 : w * 0.05} y={altoArriba - u * 90} /> : null}
          </div>
          <div style={{ position: "absolute", left: 0, top: altoArriba, width: w, height: altoAbajo, overflow: "hidden" }}>
            <div style={{ position: "absolute", left: 0, top: 0, width: w, height: altoAbajo, overflow: "hidden" }}>
              <VideoArturo plan={plan} stem={stem} conAudio={false} w={w} h={altoAbajo} />
            </div>
          </div>
          <div style={{ position: "absolute", left: 0, top: altoArriba - u * 3, width: w, height: u * 6, background: `linear-gradient(90deg, transparent, ${COLOR.ambar}, transparent)` }} />
        </>
      ) : (
        <>
          <div style={{ position: "absolute", inset: 0 }}>
            <Contenido archivo={archivo} ilustracion={ilustracion} w={w} h={h} inicio={inicio} fin={fin} />
          </div>
          <div style={{ position: "absolute", right: vertical ? 90 : w * 0.04, bottom: vertical ? 470 : h * 0.06, width: vertical ? 360 : 520, height: vertical ? 480 : 292, borderRadius: u * 28, overflow: "hidden", border: `${u * 5}px solid ${COLOR.ambar}`, boxShadow: "0 12px 40px rgba(0,0,0,0.6)", transform: `scale(${0.8 + 0.2 * e})` }}>
            <VideoArturo plan={plan} stem={stem} conAudio={false} w={vertical ? 360 : 520} h={vertical ? 480 : 292} />
          </div>
          {etiqueta ? <Etiqueta texto={etiqueta} ia={ia} x={vertical ? 80 : w * 0.05} y={vertical ? 280 : h * 0.07} /> : null}
        </>
      )}
    </AbsoluteFill>
  );
};

/** APOYO A PANTALLA COMPLETA: close-up del frasco, atomizador, textura o ilustración. Se regresa a Arturo antes del remate. */
export const ApoyoCompleto: React.FC<{ archivo?: Medio; ilustracion?: "frasco"; inicio: number; fin: number; etiqueta?: string | null; ia: boolean }> = ({ archivo, ilustracion, inicio, fin, etiqueta, ia }) => {
  const { t } = useT();
  const { w, h, vertical } = useFormato();
  const op = visible(t, inicio, fin, 0.15, 0.15);
  if (op <= 0) return null;
  return (
    <AbsoluteFill style={{ opacity: op }}>
      <Contenido archivo={archivo} ilustracion={ilustracion} w={w} h={h} inicio={inicio} fin={fin} />
      {etiqueta ? <Etiqueta texto={etiqueta} ia={ia} x={vertical ? 80 : w * 0.05} y={vertical ? 280 : h * 0.07} /> : null}
    </AbsoluteFill>
  );
};
