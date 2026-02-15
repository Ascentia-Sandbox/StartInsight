import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Startup Tools Directory",
  description:
    "Curated directory of essential startup tools for founders. Find the best tools for payments, analytics, no-code, marketing, and more.",
  openGraph: {
    title: "Startup Tools Directory | StartInsight",
    description:
      "Curated directory of essential startup tools for founders. Find the best tools for payments, analytics, no-code, marketing, and more.",
  },
};

export default function ToolsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
