import type { Metadata } from "next";
import { Geist, Geist_Mono, Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://kaplun.tech"),
  title: {
    default: "Kaplun — AI Creator-Led Growth Partner",
    template: "%s | Kaplun",
  },
  description:
    "The AI creator-led growth partner. We pair state-of-the-art AI discovery with a senior in-house team to source, activate, and amplify high-ROI influencer campaigns.",
  keywords: [
    "Creator Marketing",
    "Influencer Sourcing Engine",
    "AI Growth Partner",
    "DTC Influencer Agency",
    "Affiliate Programme Management",
    "Creator Ad Creative",
    "TikTok & Meta Creator Ads",
    "Kaplun",
  ],
  authors: [{ name: "Kaplun", url: "https://kaplun.tech" }],
  creator: "Kaplun",
  publisher: "Kaplun",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  alternates: {
    canonical: "https://kaplun.tech",
  },
  openGraph: {
    title: "Kaplun — AI Creator-Led Growth Partner",
    description:
      "Scale your brand with AI creator discovery, done-for-you seeding, automated affiliate management, and whitelisted creator ads. Shortlists in 24 hours.",
    url: "https://kaplun.tech",
    siteName: "Kaplun",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Kaplun — AI Creator-Led Growth Partner",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Kaplun — AI Creator-Led Growth Partner",
    description:
      "AI creator discovery + senior in-house team to ship high-performing influencer campaigns in days.",
    images: ["/og-image.png"],
    creator: "@kapluntech",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  icons: {
    icon: "/favicon.ico",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://kaplun.tech/#organization",
      name: "Kaplun",
      url: "https://kaplun.tech",
      logo: "https://kaplun.tech/og-image.png",
      description:
        "The AI creator-led growth partner pairing AI discovery with senior in-house team execution for DTC brands.",
    },
    {
      "@type": "WebSite",
      "@id": "https://kaplun.tech/#website",
      url: "https://kaplun.tech",
      name: "Kaplun",
      publisher: {
        "@id": "https://kaplun.tech/#organization",
      },
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} ${inter.variable} h-full antialiased`}
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="min-h-full flex flex-col" suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
