import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Platform Tour",
  description:
    "Take an interactive tour of StartInsight. See how our AI analyzes market signals and generates actionable startup opportunities.",
  openGraph: {
    title: "Platform Tour | StartInsight",
    description:
      "Take an interactive tour of StartInsight. See how our AI analyzes market signals and generates actionable startup opportunities.",
  },
};

export default function PlatformTourLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
