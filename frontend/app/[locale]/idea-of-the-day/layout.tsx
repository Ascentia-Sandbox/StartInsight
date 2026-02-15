import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Idea of the Day",
  description:
    "Today's top AI-selected startup opportunity. A fresh, validated business idea delivered daily with full analysis.",
  openGraph: {
    title: "Idea of the Day | StartInsight",
    description:
      "Today's top AI-selected startup opportunity. A fresh, validated business idea delivered daily with full analysis.",
  },
};

export default function IdeaOfTheDayLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
