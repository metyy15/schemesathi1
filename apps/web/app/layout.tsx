import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SchemeSathi - India's Government Benefits Navigator",
  description: "AI-powered navigator to discover and check eligibility for Indian government schemes",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
