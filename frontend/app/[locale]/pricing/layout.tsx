import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing Plans",
  description:
    "Start free, scale as you grow. StartInsight offers flexible pricing from free exploration to enterprise-grade startup intelligence.",
  openGraph: {
    title: "Pricing Plans | StartInsight",
    description:
      "Start free, scale as you grow. StartInsight offers flexible pricing from free exploration to enterprise-grade startup intelligence.",
  },
};

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
