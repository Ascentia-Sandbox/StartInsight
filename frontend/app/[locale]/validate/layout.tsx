import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Validate Your Startup Idea",
  description:
    "Use AI to validate your startup idea with market analysis, competitor research, and viability scoring across 8 dimensions.",
  openGraph: {
    title: "Validate Your Startup Idea | StartInsight",
    description:
      "Use AI to validate your startup idea with market analysis, competitor research, and viability scoring across 8 dimensions.",
  },
};

export default function ValidateLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
