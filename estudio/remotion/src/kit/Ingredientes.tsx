import React from "react";
import { AbsoluteFill, Img, spring, staticFile } from "remotion";
import { COLOR, FUENTE } from "./theme";
import { useFormato, useT, visible } from "./core";
import type { Medio } from "./tipos";

type Item = { nombre: string; t: number; foto?: Medio | null };

/**
 * FRANJA DE INGREDIENTES. "Tiene manzana, lavanda y canela": una franja horizontal con la foto de cada nota y su nombre grande.
 * Cada nota aparece EN el instante en que Arturo la dice, y solo las que dijo (plan.py no deja pasar una nota que no se oye).
 * Sin foto, la nota se muestra con un círculo de color y su inicial: nunca se inventa una imagen del ingrediente.
 */
const TONOS = ["#C8553D", "#8E6BBF", "#B8742E", "#5E8C61", "#D1A23A", "#B04A6F"];

export const FranjaIngredientes: React.FC<{ items: Item[]; inicio: number; fin: number }> = ({ items, inicio, fin }) => {
  const { t, f, fps } = useT();
  const { vertical, u, w, h, seg } = useFormato();
  const op = visible(t, inicio, fin, 0.2, 0.35);
  if (op <= 0 || !items.length) return null;
  const alto = u * (vertical ? 250 : 180);
  const yTop = vertical ? seg.b - u * 212 - alto : h - 200 - alto; // arriba de los subtítulos, lo más lejos posible de la cara
  const ancho = Math.min(seg.r - seg.l, items.length * u * (vertical ? 300 : 340));
  const izq = vertical ? seg.l + (seg.r - seg.l - ancho) / 2 : (w - ancho) / 2;
  const celda = ancho / items.length;
  const largo = Math.max(...items.map((x) => x.nombre.length));
  const letra = Math.min(u * (vertical ? 52 : 44), (celda - u * 16) / (largo * 0.8)); // los nombres largos se achican para no chocar
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: op }}>
      <div style={{ position: "absolute", left: izq - u * 24, top: yTop, width: ancho + u * 48, height: alto, borderRadius: u * 36, background: `linear-gradient(180deg, rgba(20,16,12,0.78), rgba(20,16,12,0.9))`, border: `${u * 2}px solid ${COLOR.ambar}55`, boxShadow: `0 ${u * 14}px ${u * 40}px rgba(0,0,0,0.5)` }} />
      {items.map((it, i) => {
        const e = spring({ frame: f - Math.round(it.t * fps), fps, config: { damping: 14, stiffness: 190, mass: 0.7 } });
        const diam = alto * (vertical ? 0.5 : 0.46);
        const tono = TONOS[i % TONOS.length];
        return (
          <div key={i} style={{ position: "absolute", left: izq + celda * i, top: yTop, width: celda, height: alto, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: u * 10, opacity: Math.min(1, e * 1.4), transform: `translateY(${(1 - e) * u * 40}px) scale(${0.6 + 0.4 * e})` }}>
            {it.foto && it.foto.tipo === "imagen" ? (
              <Img src={staticFile(it.foto.src)} style={{ width: diam, height: diam, objectFit: "cover", borderRadius: "50%", border: `${u * 4}px solid ${COLOR.ambar}` }} />
            ) : (
              <div style={{ width: diam, height: diam, borderRadius: "50%", background: `radial-gradient(circle at 35% 30%, ${tono}, ${COLOR.negroSuave})`, border: `${u * 4}px solid ${COLOR.ambar}`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FUENTE.titulo, fontWeight: 900, fontSize: diam * 0.5, color: COLOR.crema }}>
                {it.nombre.slice(0, 1).toUpperCase()}
              </div>
            )}
            <div style={{ fontFamily: FUENTE.sans, fontWeight: 900, fontSize: letra, color: COLOR.crema, textTransform: "uppercase", letterSpacing: 0.5, textShadow: "0 3px 10px #000" }}>{it.nombre}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
