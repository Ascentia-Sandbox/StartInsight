import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Browse Startup Ideas",
  description:
    "Explore AI-analyzed startup opportunities with 8-dimension scoring. Filter by market, category, and viability to find your next venture.",
  openGraph: {
    title: "Browse Startup Ideas | StartInsight",
    description:
      "Explore AI-analyzed startup opportunities with 8-dimension scoring. Filter by market, category, and viability to find your next venture.",
  },
};

export default function InsightsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
