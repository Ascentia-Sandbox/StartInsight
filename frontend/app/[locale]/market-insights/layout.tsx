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

export default function MarketInsightsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
