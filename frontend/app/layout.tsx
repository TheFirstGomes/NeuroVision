import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeuroVision — Neuro-Oftalmologia Interativa",
  description:
    "Plataforma educacional de neuro-oftalmologia com visualização anatômica 3D e tutor clínico baseado em IA",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
