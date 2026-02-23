import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Providers from "@/components/Providers";
import { Toaster } from "sonner"; // Import Toaster

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "GoalOS Enterprise",
  description: "Sistema de Inversión Deportiva Inteligente",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <Providers>
          <Toaster position="top-center" richColors /> {/* Add Toaster here */}
          {children}
        </Providers>
      </body>
    </html>
  );
}