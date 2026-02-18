import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contact Us",
  description:
    "Get in touch with the StartInsight team. We typically respond within 24 hours to all inquiries.",
  openGraph: {
    title: "Contact Us | StartInsight",
    description:
      "Get in touch with the StartInsight team. We typically respond within 24 hours to all inquiries.",
  },
};

export default function ContactLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
