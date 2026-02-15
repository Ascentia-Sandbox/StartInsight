import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Startup Trends & Market Signals",
  description:
    "Track emerging startup trends and market signals from Reddit, Hacker News, Product Hunt, and Google Trends in real-time.",
  openGraph: {
    title: "Startup Trends & Market Signals | StartInsight",
    description:
      "Track emerging startup trends and market signals from Reddit, Hacker News, Product Hunt, and Google Trends in real-time.",
  },
};

export default function TrendsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
