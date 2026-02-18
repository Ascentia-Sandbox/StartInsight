import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In",
  description:
    "Sign in to your StartInsight account to access AI-powered startup discovery and market intelligence.",
  openGraph: {
    title: "Sign In | StartInsight",
    description:
      "Sign in to your StartInsight account to access AI-powered startup discovery and market intelligence.",
  },
};

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
