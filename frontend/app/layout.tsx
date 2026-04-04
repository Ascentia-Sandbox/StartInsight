import type { Metadata } from "next";
import { Instrument_Serif, JetBrains_Mono } from "next/font/google";
import localFont from "next/font/local";
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { PostHogProvider } from "@/components/PostHogProvider";
import "./globals.css";

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument-serif",
  subsets: ["latin"],
  weight: "400",
  // 'optional' prevents font-swap from delaying LCP — system serif used on first load
  // font applies on subsequent navigations (cached). Better LCP than 'swap'.
  display: 'optional',
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: 'optional',
});

// Self-hosted Satoshi — eliminates the render-blocking fontshare CDN stylesheet
const satoshi = localFont({
  src: [
    { path: '../public/fonts/satoshi-400.woff2', weight: '400', style: 'normal' },
    { path: '../public/fonts/satoshi-500.woff2', weight: '500', style: 'normal' },
    { path: '../public/fonts/satoshi-700.woff2', weight: '700', style: 'normal' },
  ],
  variable: '--font-satoshi',
  display: 'optional',
});

export const metadata: Metadata = {
  title: "StartInsight - AI-Powered Startup Idea Discovery",
  description:
    "Discover validated startup ideas with 8-dimension AI scoring. Browse 3 free premium reports, then upgrade for unlimited access to market sizing, execution plans, and competitive analysis.",
  icons: {
    icon: [
      { url: '/icon.svg', type: 'image/svg+xml' },
      { url: '/favicon.ico', sizes: '32x32' },
    ],
    apple: [{ url: '/apple-icon', sizes: '180x180' }],
  },
  verification: {
    google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION || "UWZN9hurnOBJbiCTS9PCG9wkk-ctOS2y-h0N05MV7K0",
  },
};

// Root Layout wraps ALL routes including those outside [locale].
// The [locale]/layout.tsx adds providers, header, etc. (no html/body).
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const orgSchema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "StartInsight",
    url: "https://startinsight.co",
    logo: "https://startinsight.co/icon.svg",
    description: "AI-powered startup idea discovery platform",
    sameAs: ["https://twitter.com/startinsight"],
  };

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(orgSchema) }}
        />
      </head>
      <body className={`${satoshi.variable} ${instrumentSerif.variable} ${jetbrainsMono.variable} antialiased`}>
        <PostHogProvider>
          {children}
          <Analytics />
          <SpeedInsights />
        </PostHogProvider>
      </body>
    </html>
  );
}
