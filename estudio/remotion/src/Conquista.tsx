import React from "react";
import { AbsoluteFill, Audio, interpolate, staticFile } from "remotion";
import type { CalculateMetadataFunction } from "remotion";
import {
  Aplausos,
  ApoyoCompleto,
  BrilloRiser,
  CierreCanal,
  clamp,
  COLOR,
  EfectosRafaguiza,
  Efectos,
  FranjaIngredientes,
  GolpeSiempre,
  Musica,
  PalabraClave,
  Revelacion,
  Rotulo,
  SplitApoyo,
  Subtitulos,
  TituloRafaguiza,
  Transiciones,
  useT,
  Veredicto,
  VideoArturo,
  ahoraImpacto,
} from "./kit";
import type { PlanResuelto, PropsConquista } from "./kit";
import type { Transicion } from "./kit/Transiciones";

/**
 * LA COMPOSICIÓN. Lee el plan resuelto de public/trabajo/<slug>/plan.resuelto.json (lo escribe scripts/plan.py) y pone cada cosa
 * en su segundo. Sirve para 16:9 (1920x1080) y 9:16 (1080x1920): todo el kit mide el lienzo con useVideoConfig.
 * Capas, de abajo hacia arriba: video de Arturo, apoyos/gráficos (dentro de Transiciones y del temblor del PUM),
 * y encima los subtítulos y los textos de firma. `stem` deja oír solo una parte (voz / fx / música) para medir el audio en QA.
 */
export const calcularMetadatos: CalculateMetadataFunction<PropsConquista> = async ({ props }) => {
  const r = await fetch(staticFile(`trabajo/${props.slug}/plan.resuelto.json`));
  if (!r.ok) throw new Error(`No encuentro el plan resuelto de «${props.slug}». Corre primero: python scripts/plan.py ${props.slug}`);
  const plan = (await r.json()) as PlanResuelto;
  return { durationInFrames: Math.max(1, Math.round((plan.duracion_base + plan.cola) * plan.fps)), fps: plan.fps, props: { ...props, plan } };
};

const Escena: React.FC<{ plan: PlanResuelto; stem: NonNullable<PropsConquista["stem"]> }> = ({ plan, stem }) => {
  const { t } = useT();
  const zoom = plan.beats.filter((b) => b.tipo === "zoom") as Extract<PlanResuelto["beats"][number], { tipo: "zoom" }>[];
  let escala = 1;
  for (const z of zoom) {
    if (t >= z.inicio && t <= z.fin) escala = interpolate(t, [z.inicio, (z.inicio + z.fin) / 2, z.fin], [1, z.escala, z.escala * 0.985 + 0.015], clamp);
  }
  const transiciones: Transicion[] = plan.beats.filter((b) => b.tipo === "transicion").map((b) => ({ estilo: (b as { estilo: Transicion["estilo"] }).estilo, inicio: b.inicio }));
  return (
    <Transiciones lista={transiciones}>
      <VideoArturo plan={plan} stem={stem} escala={escala} />
      {plan.firma.oler_bien.map((o, i) => (
        <BrilloRiser key={`br${i}`} o={o} />
      ))}
      {plan.beats.map((b, i) => {
        switch (b.tipo) {
          case "split":
            return <SplitApoyo key={i} plan={plan} stem={stem} archivo={b.archivo} ilustracion={b.ilustracion} inicio={b.inicio} fin={b.fin} modo={b.modo === "pip" ? "pip" : "split"} etiqueta={b.etiqueta} ia={b.ia} />;
          case "apoyo":
            return <ApoyoCompleto key={i} archivo={b.archivo} ilustracion={b.ilustracion} inicio={b.inicio} fin={b.fin} etiqueta={b.etiqueta} ia={b.ia} />;
          case "ingredientes":
            return <FranjaIngredientes key={i} items={b.items} inicio={b.inicio} fin={b.fin} />;
          case "veredicto":
            return <Veredicto key={i} titulo={b.titulo} puntos={b.puntos} inicio={b.inicio} fin={b.fin} lado={b.lado} />;
          case "rotulo":
            return <Rotulo key={i} texto={b.texto} sub={b.sub} inicio={b.inicio} fin={b.fin} />;
          case "palabra":
            return <PalabraClave key={i} texto={b.texto} inicio={b.inicio} fin={b.fin} efecto={b.efecto} lado={b.lado} />;
          case "revelacion":
            return <Revelacion key={i} inicio={b.inicio} fin={b.fin} texto={b.texto} />;
          default:
            return null;
        }
      })}
      {plan.firma.rafaguiza ? <EfectosRafaguiza r={plan.firma.rafaguiza} /> : null}
    </Transiciones>
  );
};

export const Conquista: React.FC<PropsConquista> = ({ plan, stem = "todo" }) => {
  const { t } = useT();
  if (!plan) return null;
  const total = Math.round((plan.duracion_base + plan.cola) * plan.fps);
  const tTotal = total / plan.fps;
  const imp = ahoraImpacto(t, plan.firma.oler_bien.map((o) => o.pum));
  const ocultarSubs: [number, number][] = [
    ...plan.firma.oler_bien.map((o) => [o.siempre, o.frase_fin + 0.45] as [number, number]),
    ...(plan.firma.rafaguiza ? ([[plan.firma.rafaguiza.inicio, plan.firma.rafaguiza.fin + 0.45]] as [number, number][]) : []),
  ];
  const aplauso = plan.firma.aplausos[0];
  const mega = plan.firma.cierre?.megafono;
  return (
    <AbsoluteFill style={{ background: COLOR.negro }}>
      <Musica plan={plan} stem={stem} total={total} />
      <Efectos plan={plan} stem={stem} />
      {mega && (stem === "todo" || stem === "voz") ? <Audio src={staticFile(mega.voz)} name="voz (con el tramo de megáfono)" /> : null}
      <AbsoluteFill style={{ transform: `translate(${imp.x}px, ${imp.y}px) scale(${imp.s})` }}>
        <Escena plan={plan} stem={stem} />
        {aplauso ? <Aplausos t0={aplauso.t} dur={aplauso.dur} /> : null}
      </AbsoluteFill>
      {plan.firma.cierre ? <CierreCanal c={plan.firma.cierre} /> : null}
      <Subtitulos palabras={plan.palabras} ocultar={ocultarSubs} />
      {plan.firma.oler_bien.map((o, i) => (
        <GolpeSiempre key={`gs${i}`} o={o} />
      ))}
      {plan.firma.rafaguiza ? <TituloRafaguiza r={plan.firma.rafaguiza} /> : null}
      {plan.cola > 0 ? <AbsoluteFill style={{ background: COLOR.negro, opacity: interpolate(t, [tTotal - 1.4, tTotal - 0.1], [0, 1], clamp), pointerEvents: "none" }} /> : null}
    </AbsoluteFill>
  );
};
