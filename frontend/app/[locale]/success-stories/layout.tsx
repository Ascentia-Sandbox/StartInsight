import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Startup Success Stories",
  description:
    "Real startup success stories and case studies. Learn how founders turned AI-discovered ideas into successful businesses.",
  openGraph: {
    title: "Startup Success Stories | StartInsight",
    description:
      "Real startup success stories and case studies. Learn how founders turned AI-discovered ideas into successful businesses.",
  },
};

export default function SuccessStoriesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
