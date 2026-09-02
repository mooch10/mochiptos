import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Mochiptos - Inteligencia Inmobiliaria & Mercado CABA",
  description: "Plataforma de análisis de mercado inmobiliario en CABA con Machine Learning y simulaciones financieras.",
  alternates: {
    types: {
      "text/markdown": "/llms.txt",
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="dark">
      <body className={`${inter.className} min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-blue-500 selection:text-white flex flex-col justify-between`}>
        <div>
          <Navbar />
          <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
        <Footer />
      </body>
    </html>
  );
}
