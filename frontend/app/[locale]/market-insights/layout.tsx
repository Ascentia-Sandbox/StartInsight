import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Market Insights & Analysis",
  description:
    "In-depth market analysis articles covering startup trends, industry shifts, and emerging opportunities for entrepreneurs.",
  openGraph: {
    title: "Market Insights & Analysis | StartInsight",
    description:
      "In-depth market analysis articles covering startup trends, industry shifts, and emerging opportunities for entrepreneurs.",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "Blog",
  name: "StartInsight Market Insights",
  description:
    "AI-generated market analysis articles covering startup trends, industry shifts, and emerging opportunities. Published every 3 days.",
  url: "https://startinsight.co/market-insights",
  publisher: { "@type": "Organization", name: "StartInsight", url: "https://startinsight.co" },
};

export default function MarketInsightsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      {children}
    </>
  );
}
