import type { Metadata } from "next";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Providers } from "../providers";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { ThemeProvider } from "@/components/theme-provider";
import { TourProvider, FloatingTourButton } from "@/components/tour";
import { Toaster } from "@/components/ui/sonner";
import { CommandPalette } from "@/components/command-palette";
import { locales, type Locale } from '@/i18n';

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://startinsight.app";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;

  return {
    metadataBase: new URL(siteUrl),
    title: {
      default: "StartInsight - AI-Powered Startup Idea Discovery",
      template: "%s | StartInsight",
    },
    description:
      "Discover your next million-dollar startup idea. AI analyzes millions of conversations to surface validated opportunities with 8-dimension scoring and 40-step research.",
    keywords: [
      "startup ideas",
      "business ideas",
      "AI startup discovery",
      "market research",
      "startup validation",
      "idea validation",
      "entrepreneurship",
      "SaaS ideas",
      "indie hacker",
      "startup trends",
    ],
    authors: [{ name: "StartInsight" }],
    creator: "StartInsight",
    publisher: "StartInsight",
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
    openGraph: {
      type: "website",
      locale: locale === "en" ? "en_US" : locale,
      url: locale === "en" ? siteUrl : `${siteUrl}/${locale}`,
      siteName: "StartInsight",
      title: "StartInsight - AI-Powered Startup Idea Discovery",
      description:
        "Discover your next million-dollar startup idea. AI analyzes millions of conversations to surface validated opportunities.",
      images: [
        {
          url: `${siteUrl}/og-image.png`,
          width: 1200,
          height: 630,
          alt: "StartInsight - AI-Powered Startup Idea Discovery",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: "StartInsight - AI-Powered Startup Idea Discovery",
      description:
        "Discover your next million-dollar startup idea with AI-powered market intelligence.",
      images: [`${siteUrl}/og-image.png`],
      creator: "@startinsight",
    },
    verification: {
      google: process.env.GOOGLE_SITE_VERIFICATION,
    },
    alternates: {
      canonical: siteUrl,
    },
  };
}

export default async function LocaleLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}>) {
  const { locale } = await params;

  // Ensure the locale is valid
  const isValidLocale = (locale: string): locale is Locale => {
    return locales.includes(locale as Locale);
  };

  if (!isValidLocale(locale)) {
    notFound();
  }

  // Fetch messages for the locale
  const messages = await getMessages({ locale });

  return (
    <NextIntlClientProvider messages={messages}>
      <ThemeProvider>
        <Providers>
          <TourProvider>
            <a href="#main-content" className="skip-to-content">
              Skip to main content
            </a>
            <Header />
            <main id="main-content">{children}</main>
            <Footer />
            <FloatingTourButton />
            <CommandPalette />
            <Toaster />
          </TourProvider>
        </Providers>
      </ThemeProvider>
    </NextIntlClientProvider>
  );
}
