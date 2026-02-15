import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Frequently Asked Questions",
  description:
    "Get answers to common questions about StartInsight's AI-powered startup discovery platform, pricing, features, and security.",
  openGraph: {
    title: "Frequently Asked Questions | StartInsight",
    description:
      "Get answers to common questions about StartInsight's AI-powered startup discovery platform, pricing, features, and security.",
  },
};

export default function FaqLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
