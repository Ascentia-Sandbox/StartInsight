import Link from "next/link";
import { Shield } from "lucide-react";

export const metadata = {
  title: "Privacy Policy",
  description: "Privacy Policy for StartInsight — how we collect, use, and protect your data.",
};

const sections = [
  {
    title: "1. Introduction",
    content: `StartInsight ("we", "us", or "our") respects your privacy and is committed to protecting your personal data. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our Service. Please read this policy carefully.`,
  },
  {
    title: "2. Information We Collect",
    content: `We collect information you provide directly to us, such as when you create an account (name, email address), payment information (processed securely by Stripe — we do not store card numbers), and content you submit to the platform. We also collect usage data automatically, including IP addresses, browser type, pages visited, and interaction logs to improve the Service.`,
  },
  {
    title: "3. How We Use Your Information",
    content: `We use collected information to: (a) provide, operate, and maintain the Service; (b) personalise AI-generated insights and recommendations; (c) process transactions and send billing communications; (d) send product updates and newsletters (you can opt out at any time); (e) respond to support requests; (f) detect and prevent fraud or abuse; and (g) comply with legal obligations.`,
  },
  {
    title: "4. AI Processing of Your Data",
    content: `To deliver personalised startup insights, our AI systems process the information you provide — including your industry preferences, quiz responses, and saved ideas. This processing is used solely to generate relevant recommendations for you. We do not sell your personal data to third parties for advertising purposes.`,
  },
  {
    title: "5. Sharing Your Information",
    content: `We may share your information with: (a) service providers who assist in operating our platform (e.g., Stripe for payments, Supabase for database hosting, Vercel for hosting) under strict data processing agreements; (b) law enforcement or government authorities when required by law; and (c) a successor entity in the event of a merger or acquisition, with prior notice to you.`,
  },
  {
    title: "6. Cookies and Tracking",
    content: `We use cookies and similar tracking technologies to improve your experience. Essential cookies are required for the Service to function. Analytics cookies help us understand how users interact with the platform (you may opt out via your browser settings). We do not use third-party advertising cookies.`,
  },
  {
    title: "7. Data Retention",
    content: `We retain your personal data for as long as your account is active or as needed to provide the Service. If you delete your account, we will delete or anonymise your personal data within 30 days, except where retention is required by law or for legitimate business purposes (e.g., fraud prevention).`,
  },
  {
    title: "8. Your Rights",
    content: `Depending on your location, you may have the right to: access the personal data we hold about you; correct inaccurate data; request deletion of your data; restrict or object to processing; and data portability. To exercise these rights, contact us at privacy@startinsight.co. We will respond within 30 days.`,
  },
  {
    title: "9. Data Security",
    content: `We implement appropriate technical and organisational measures to protect your personal data against unauthorised access, loss, destruction, or alteration. This includes encryption in transit (TLS) and at rest, access controls, and regular security reviews. However, no internet transmission is completely secure and we cannot guarantee absolute security.`,
  },
  {
    title: "10. Children's Privacy",
    content: `The Service is not directed to individuals under the age of 16. We do not knowingly collect personal data from children. If you believe we have inadvertently collected such data, please contact us immediately and we will delete it promptly.`,
  },
  {
    title: "11. International Data Transfers",
    content: `Your data may be processed in countries other than the one in which you reside, including Australia, the United States, and the European Union. We ensure appropriate safeguards are in place for such transfers in accordance with applicable data protection laws.`,
  },
  {
    title: "12. Changes to This Policy",
    content: `We may update this Privacy Policy periodically. We will notify you of significant changes by posting the new policy on this page and updating the "Last Updated" date. For material changes, we will also send an email notification to your registered address.`,
  },
  {
    title: "13. Contact Us",
    content: `For privacy-related inquiries, please contact our Data Protection Officer at privacy@startinsight.co or write to us via our contact page. We aim to respond to all requests within 30 days.`,
  },
];

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <section className="border-b bg-muted/30">
        <div className="container mx-auto px-4 py-16 text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 mb-6">
            <Shield className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight mb-4">Privacy Policy</h1>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            We take your privacy seriously. Here&apos;s how we handle your data.
          </p>
          <p className="text-sm text-muted-foreground mt-4">Last updated: February 20, 2026</p>
        </div>
      </section>

      {/* Content */}
      <section className="container mx-auto px-4 py-12">
        <div className="max-w-3xl mx-auto space-y-10">
          {sections.map((section) => (
            <div key={section.title}>
              <h2 className="text-xl font-semibold mb-3">{section.title}</h2>
              <p className="text-muted-foreground leading-relaxed">{section.content}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer note */}
      <section className="border-t bg-muted/30">
        <div className="container mx-auto px-4 py-8 text-center">
          <p className="text-sm text-muted-foreground">
            Privacy questions?{" "}
            <Link href="/contact" className="text-primary underline underline-offset-4">
              Contact our team
            </Link>{" "}
            or email{" "}
            <a href="mailto:privacy@startinsight.co" className="text-primary underline underline-offset-4">
              privacy@startinsight.co
            </a>
          </p>
        </div>
      </section>
    </div>
  );
}
