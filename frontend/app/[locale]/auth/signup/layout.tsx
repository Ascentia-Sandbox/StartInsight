import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Create Account",
  description:
    "Join StartInsight for free. Start discovering AI-analyzed startup ideas with 8-dimension scoring today.",
  openGraph: {
    title: "Create Account | StartInsight",
    description:
      "Join StartInsight for free. Start discovering AI-analyzed startup ideas with 8-dimension scoring today.",
  },
};

export default function SignupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
