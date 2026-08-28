import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Mochiptos - Inteligencia Inmobiliaria & Mercado CABA",
  description: "Plataforma de análisis de mercado inmobiliario en CABA con Machine Learning y simulaciones financieras.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="dark">
      <body className={`${inter.className} min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-blue-500 selection:text-white`}>
        <Navbar />
        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>
        <footer className="border-t border-slate-800/80 bg-slate-950 py-8 text-center text-xs text-slate-500">
          <p>© 2026 Mochiptos - Inteligencia Inmobiliaria. Todos los derechos reservados.</p>
        </footer>
      </body>
    </html>
  );
}
