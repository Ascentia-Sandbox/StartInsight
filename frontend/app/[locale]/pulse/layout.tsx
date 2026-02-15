import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Market Pulse",
  description:
    "Real-time startup market pulse. Track signals, trending keywords, and emerging opportunities as they happen.",
  openGraph: {
    title: "Market Pulse | StartInsight",
    description:
      "Real-time startup market pulse. Track signals, trending keywords, and emerging opportunities as they happen.",
  },
};

export default function PulseLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
