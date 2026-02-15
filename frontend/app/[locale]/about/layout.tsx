import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About StartInsight",
  description:
    "Learn about StartInsight's mission to democratize startup discovery. AI-powered market intelligence for entrepreneurs worldwide.",
  openGraph: {
    title: "About StartInsight | StartInsight",
    description:
      "Learn about StartInsight's mission to democratize startup discovery. AI-powered market intelligence for entrepreneurs worldwide.",
  },
};

export default function AboutLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
