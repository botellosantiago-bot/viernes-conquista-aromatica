import React from "react";
import { Composition } from "remotion";
import { Conquista, calcularMetadatos } from "./Conquista";
import type { PropsConquista } from "./kit";

/**
 * Dos composiciones con el MISMO contenido: una para YouTube largo y lives (16:9) y otra para Shorts, Reels y TikTok (9:16).
 * La duración la fija el plan resuelto de cada video (calcularMetadatos).
 */
export const Root: React.FC = () => (
  <>
    <Composition id="Conquista16x9" component={Conquista} width={1920} height={1080} fps={30} durationInFrames={30} defaultProps={{ slug: "demo" } as PropsConquista} calculateMetadata={calcularMetadatos} />
    <Composition id="Conquista9x16" component={Conquista} width={1080} height={1920} fps={30} durationInFrames={30} defaultProps={{ slug: "demo" } as PropsConquista} calculateMetadata={calcularMetadatos} />
  </>
);
