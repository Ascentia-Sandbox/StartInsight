import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Startup Reports",
  description:
    "Generate detailed startup research reports with AI. Market analysis, competitor landscapes, and actionable recommendations.",
  openGraph: {
    title: "Startup Reports | StartInsight",
    description:
      "Generate detailed startup research reports with AI. Market analysis, competitor landscapes, and actionable recommendations.",
  },
};

export default function ReportsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
