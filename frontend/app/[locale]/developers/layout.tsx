import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Developer API",
  description:
    "Build on StartInsight's API. 230+ REST endpoints for startup intelligence, trend data, and market signals.",
  openGraph: {
    title: "Developer API | StartInsight",
    description:
      "Build on StartInsight's API. 230+ REST endpoints for startup intelligence, trend data, and market signals.",
  },
};

export default function DevelopersLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
