import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Platform Features",
  description:
    "Explore StartInsight's powerful features: AI research agents, 8-dimension scoring, real-time signals, builder integrations, and team collaboration.",
  openGraph: {
    title: "Platform Features | StartInsight",
    description:
      "Explore StartInsight's powerful features: AI research agents, 8-dimension scoring, real-time signals, builder integrations, and team collaboration.",
  },
};

export default function FeaturesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
