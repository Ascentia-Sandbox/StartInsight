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

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "Dataset",
  name: "StartInsight Startup Ideas Database",
  description:
    "500+ AI-analyzed startup opportunities scored across 8 dimensions. Updated every 6 hours from Reddit, Product Hunt, Google Trends, Twitter/X, and Hacker News.",
  url: "https://startinsight.co/insights",
  creator: { "@type": "Organization", name: "StartInsight", url: "https://startinsight.co" },
  variableMeasured: [
    "Opportunity Score", "Problem Severity", "Feasibility",
    "Why Now (Timing)", "Revenue Potential", "Execution Difficulty",
    "Go-To-Market", "Founder Fit",
  ],
  temporalCoverage: "2026/..",
  isAccessibleForFree: true,
};

export default function InsightsLayout({
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
