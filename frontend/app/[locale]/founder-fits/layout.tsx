import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Founder Fits",
  description:
    "Discover startup ideas matched to your skills and experience. AI-powered founder-idea matching for better outcomes.",
  openGraph: {
    title: "Founder Fits | StartInsight",
    description:
      "Discover startup ideas matched to your skills and experience. AI-powered founder-idea matching for better outcomes.",
  },
};

export default function FounderFitsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
