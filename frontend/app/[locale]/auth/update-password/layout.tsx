import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Update Password | StartInsight",
  description: "Set a new password for your StartInsight account.",
};

export default function UpdatePasswordLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
