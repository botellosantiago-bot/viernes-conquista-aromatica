import React from "react";
import { AbsoluteFill, interpolate } from "remotion";
import { COLOR, FUENTE } from "./theme";
import { clamp, SUAVE, useEntrada, useFormato, useT, visible, azar } from "./core";
import { Chispa } from "./Iconos";

/**
 * PALABRA CLAVE. Una sola palabra o frase muy corta, enorme y legible en celular (nombres de perfumes, notas, cifras, remates).
 * Una idea por pantalla: el plan avisa si dos textos se encimarían. `lado` evita tapar la cara de Arturo.
 */
export const PalabraClave: React.FC<{ texto: string; inicio: number; fin: number; efecto?: "pop" | "shimmer"; lado?: string | null }> = ({ texto, inicio, fin, efecto = "pop", lado }) => {
  const { t } = useT();
  const { vertical, u, w, h, seg } = useFormato();
  const op = visible(t, inicio, fin, 0.08, 0.2);
  const e = useEntrada(inicio, 13);
  if (op <= 0) return null;
  const posicion = lado ?? (vertical ? "arriba" : "izq");
  const tam = u * (vertical ? 150 : 128) * (texto.length > 12 ? 0.72 : texto.length > 8 ? 0.85 : 1);
  const caja: React.CSSProperties = { position: "absolute", maxWidth: (seg.r - seg.l) * (vertical ? 1 : 0.46) };
  if (posicion === "arriba") Object.assign(caja, { left: seg.l, right: w - seg.r, top: seg.t + u * 20, textAlign: "center" });
  else if (posicion === "abajo") Object.assign(caja, { left: seg.l, right: w - seg.r, top: h * 0.56, textAlign: "center" });
  else if (posicion === "der") Object.assign(caja, { right: w - seg.r, top: h * 0.3, textAlign: "right" });
  else Object.assign(caja, { left: seg.l, top: h * 0.3, textAlign: "left" });
  const brillo = efecto === "shimmer" ? interpolate((t - inicio) % 1.6, [0, 1.6], [-30, 130]) : -50;
  const rot = (1 - e) * -4 - 1.2;
  const base: React.CSSProperties = { display: "inline-block", fontFamily: FUENTE.sans, fontWeight: 900, fontSize: tam, lineHeight: 1, letterSpacing: -1, textTransform: "uppercase", whiteSpace: "nowrap" };
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: op }}>
      <div style={{ ...caja, transform: `scale(${0.55 + 0.45 * e}) rotate(${rot}deg)` }}>
        <span style={{ position: "relative", display: "inline-block", filter: `drop-shadow(0 ${u * 8}px ${u * 16}px rgba(0,0,0,0.65))` }}>
          <span style={{ ...base, color: COLOR.negro, WebkitTextStroke: `${u * 16}px ${COLOR.negro}` }}>{texto}</span>
          <span
            style={{
              ...base,
              position: "absolute",
              left: 0,
              top: 0,
              backgroundImage: `linear-gradient(100deg, ${COLOR.ambar} 0%, ${COLOR.ambar} ${brillo - 12}%, #FFFFFF ${brillo}%, ${COLOR.ambar} ${brillo + 12}%, ${COLOR.dorado} 100%)`,
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
            }}
          >
            {texto}
          </span>
        </span>
      </div>
    </AbsoluteFill>
  );
};

/** REVELACIÓN / dato importante: destello suave de chispas (sin sonar a tráiler) y, si hay texto, una etiqueta elegante. */
export const Revelacion: React.FC<{ inicio: number; fin: number; texto?: string | null }> = ({ inicio, fin, texto }) => {
  const { t } = useT();
  const { vertical, u, w, h, seg } = useFormato();
  const op = visible(t, inicio, fin, 0.1, 0.4);
  if (op <= 0) return null;
  const cx = vertical ? w * 0.5 : w * 0.5;
  const cy = vertical ? h * 0.3 : h * 0.34;
  const k = (t - inicio) / Math.max(0.1, fin - inicio);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: op }}>
      {Array.from({ length: 9 }, (_, i) => {
        const ang = (i / 9) * Math.PI * 2 + azar(i) * 0.6;
        const r = u * (150 + azar(i + 4) * 180) * interpolate(k, [0, 0.6], [0.2, 1], { ...clamp, easing: SUAVE });
        const s = u * (18 + azar(i + 9) * 30) * (1 - Math.abs(k - 0.35));
        return (
          <div key={i} style={{ position: "absolute", left: cx + Math.cos(ang) * r - s / 2, top: cy + Math.sin(ang) * r * 0.7 - s / 2, opacity: 0.9 }}>
            <Chispa size={Math.max(6, s)} color={i % 3 === 0 ? COLOR.acento : COLOR.destello} />
          </div>
        );
      })}
      {texto ? (
        <div style={{ position: "absolute", left: seg.l, right: w - seg.r, top: cy - u * 60, textAlign: "center", fontFamily: FUENTE.titulo, fontStyle: "italic", fontWeight: 700, fontSize: u * 84, color: COLOR.destello, textShadow: `0 0 ${u * 30}px ${COLOR.ambar}, 0 ${u * 4}px ${u * 12}px #000` }}>
          {texto}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
