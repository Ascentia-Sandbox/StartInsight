"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Check, X, Zap, Crown, Code2 } from "lucide-react";
import { getSupabaseClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Explore global startup ideas",
    icon: Zap,
    features: [
      { name: "Browse global startup ideas", included: true },
      { name: "Basic 4-dimension scoring", included: true },
      { name: "3 free premium reports", included: true },
      { name: "Community trends access", included: true },
      { name: "Save up to 10 insights", included: true },
      { name: "Full analysis reports", included: false },
      { name: "Asia-specific intelligence", included: false },
      { name: "API access", included: false },
    ],
    cta: "Get Started Free",
    href: "/auth/signup",
    popular: false,
  },
  {
    name: "Pro",
    price: "$19",
    period: "/month",
    description: "Full analysis for serious founders",
    icon: Crown,
    features: [
      { name: "Unlimited premium reports", included: true },
      { name: "8-dimension AI scoring", included: true },
      { name: "Full trends + 7-day forecast", included: true },
      { name: "AI research agent (10/mo)", included: true },
      { name: "Asia-specific intelligence", included: true },
      { name: "Accelerator matching", included: true },
      { name: "Export to PDF/CSV", included: true },
      { name: "Priority support", included: true },
    ],
    cta: "Start 14-Day Trial",
    href: "/auth/signup?plan=pro",
    popular: true,
    savings: "Most Popular",
  },
  {
    name: "API",
    price: "$49",
    period: "/month",
    description: "Programmatic access for builders",
    icon: Code2,
    features: [
      { name: "Everything in Pro", included: true },
      { name: "1,000 API calls per month", included: true },
      { name: "Programmatic access to idea data", included: true },
      { name: "Webhook integrations", included: true },
      { name: "Team collaboration (10 seats)", included: true },
      { name: "Dedicated support", included: true },
    ],
    cta: "Start 14-Day Trial",
    href: "/auth/signup?plan=api",
    popular: false,
  },
];

const faqs = [
  {
    question: "Can I switch plans anytime?",
    answer: "Yes! You can upgrade or downgrade your plan at any time. When upgrading, you'll be charged the prorated difference. When downgrading, your new rate takes effect at the next billing cycle.",
  },
  {
    question: "What payment methods do you accept?",
    answer: "We accept all major credit cards (Visa, Mastercard, American Express) through our secure Stripe payment processor.",
  },
  {
    question: "What are the 3 free premium reports?",
    answer: "New users get 3 free premium reports — full analysis including Business Model Canvas, failure analysis, market sizing, and accelerator matches. After 3 reports, upgrade to Pro for unlimited access.",
  },
  {
    question: "What happens to my data if I cancel?",
    answer: "Your data remains accessible for 30 days after cancellation. You can export all your saved ideas, research, and insights during this period. After 30 days, data is permanently deleted.",
  },
  {
    question: "Do you offer refunds?",
    answer: "We offer a 30-day money-back guarantee for annual plans. If you're not satisfied within the first 30 days, contact us for a full refund. Monthly plans can be cancelled anytime.",
  },
];

export default function PricingPage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await getSupabaseClient().auth.getSession();
      setIsLoggedIn(!!session);
    };
    void checkAuth();
  }, []);

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "StartInsight",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    url: "https://startinsight.co/pricing",
    offers: [
      { "@type": "Offer", name: "Free", price: "0", priceCurrency: "USD", description: "Browse global ideas, 3 free premium reports, basic scoring" },
      { "@type": "Offer", name: "Pro", price: "19", priceCurrency: "USD", billingIncrement: "MON", description: "Unlimited reports, 8-dimension scoring, Asia intelligence, research agent" },
      { "@type": "Offer", name: "API", price: "49", priceCurrency: "USD", billingIncrement: "MON", description: "Everything in Pro plus 1,000 API calls/month, webhooks, team collaboration" },
    ],
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Badge variant="secondary" className="mb-4">Simple Pricing</Badge>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Choose Your Plan
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
          Start free and scale as you grow. All plans include our core AI-powered idea discovery.
        </p>
        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <Check className="h-4 w-4 text-green-500" />
          <span>No credit card required</span>
          <span className="mx-2">|</span>
          <Check className="h-4 w-4 text-green-500" />
          <span>3 free premium reports</span>
          <span className="mx-2">|</span>
          <Check className="h-4 w-4 text-green-500" />
          <span>Cancel anytime</span>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="container mx-auto px-4 pb-16">
        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {tiers.map((tier) => (
            <Card
              key={tier.name}
              className={`relative flex flex-col ${
                tier.popular ? "border-primary shadow-lg scale-105 order-first md:order-none" : ""
              }`}
            >
              {tier.popular && (
                <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">
                  Most Popular
                </Badge>
              )}
              <CardHeader className="text-center pb-2">
                <div className="mx-auto mb-2 p-3 rounded-full bg-primary/10 w-fit">
                  <tier.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-xl">{tier.name}</CardTitle>
                <CardDescription>{tier.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <div className="text-center mb-6">
                  <span className="text-4xl font-bold">{tier.price}</span>
                  <span className="text-muted-foreground">{tier.period}</span>
                </div>
                <ul className="space-y-3">
                  {tier.features.map((feature) => (
                    <li key={feature.name} className="flex items-center gap-2 text-sm">
                      {feature.included ? (
                        <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                      ) : (
                        <X className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      )}
                      <span className={feature.included ? "" : "text-muted-foreground"}>
                        {feature.name}
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button
                  asChild
                  className="w-full"
                  variant={tier.popular ? "default" : "outline"}
                >
                  <Link href={isLoggedIn ? "/billing" : tier.href}>
                    {isLoggedIn ? "Manage Plan" : tier.cta}
                  </Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </section>

      {/* Feature Comparison Table */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-8">Compare All Features</h2>
        <div className="overflow-x-auto">
          <table className="w-full max-w-4xl mx-auto border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left py-4 px-4 font-medium">Feature</th>
                <th className="text-center py-4 px-4 font-medium">Free</th>
                <th className="text-center py-4 px-4 font-medium bg-primary/5">Pro</th>
                <th className="text-center py-4 px-4 font-medium">API</th>
              </tr>
            </thead>
            <tbody>
              {[
                { feature: "Premium Reports", free: "3 total", pro: "Unlimited", api: "Unlimited" },
                { feature: "Scoring Dimensions", free: "4", pro: "8", api: "8" },
                { feature: "AI Research Agent", free: "-", pro: "10/mo", api: "Unlimited" },
                { feature: "Trend Forecasts", free: "-", pro: "7-day", api: "7-day" },
                { feature: "Asia Intelligence", free: "-", pro: "Yes", api: "Yes" },
                { feature: "Accelerator Matching", free: "-", pro: "Yes", api: "Yes" },
                { feature: "Export (PDF/CSV)", free: "-", pro: "Yes", api: "Yes" },
                { feature: "API Calls", free: "-", pro: "-", api: "1,000/mo" },
                { feature: "Team Seats", free: "1", pro: "5", api: "10" },
                { feature: "Support", free: "Email", pro: "Priority", api: "Dedicated" },
              ].map((row) => (
                <tr key={row.feature} className="border-b hover:bg-muted/50">
                  <td className="py-3 px-4 text-sm">{row.feature}</td>
                  <td className="py-3 px-4 text-center text-sm text-muted-foreground">{row.free}</td>
                  <td className="py-3 px-4 text-center text-sm bg-primary/5 font-medium">{row.pro}</td>
                  <td className="py-3 px-4 text-center text-sm">{row.api}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="container mx-auto px-4 py-16 max-w-3xl">
        <h2 className="text-3xl font-bold text-center mb-8">Frequently Asked Questions</h2>
        <Accordion type="single" collapsible className="w-full">
          {faqs.map((faq, index) => (
            <AccordionItem key={index} value={`item-${index}`}>
              <AccordionTrigger className="text-left">
                {faq.question}
              </AccordionTrigger>
              <AccordionContent className="text-muted-foreground">
                {faq.answer}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Card className="max-w-2xl mx-auto bg-primary text-primary-foreground">
          <CardContent className="pt-8 pb-8">
            <h2 className="text-2xl font-bold mb-2">Ready to Find Your Next Big Idea?</h2>
            <p className="mb-6 text-primary-foreground/80">
              Start discovering startup opportunities backed by data, not hype.
            </p>
            <Button asChild size="lg" variant="secondary">
              <Link href={isLoggedIn ? "/dashboard" : "/auth/signup"}>
                {isLoggedIn ? "Go to Dashboard" : "Get Started Free"}
              </Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
