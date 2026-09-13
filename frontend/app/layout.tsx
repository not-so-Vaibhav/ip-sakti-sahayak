import type { Metadata, Viewport } from "next";
import { Cormorant_Garamond, Playfair_Display, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const sans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-cormorant",
  display: "swap",
});

export const metadata: Metadata = {
  title: "IP-SAKTI Sahayak | Ayurveda IP & Regulatory Intelligence",
  description: "Authoritative, cited, bilingual AI guidance on Indian and International Intellectual Property, Biodiversity Access and Benefit Sharing (ABS), and Ayurvedic formulation regulations.",
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/icon.png", type: "image/png" },
    ],
    apple: [
      { url: "/apple-icon.png", type: "image/png" },
    ],
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${sans.variable} ${playfair.variable} ${cormorant.variable} h-full antialiased overflow-x-hidden`}
    >
      <body className="min-h-full flex flex-col font-sans overflow-x-hidden w-full max-w-full">
        {children}
      </body>
    </html>
  );
}

