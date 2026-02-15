"use client";

import Link from "next/link";
import { Check, X, Zap, Crown, Building2, Rocket } from "lucide-react";
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
    description: "Perfect for exploring startup ideas",
    icon: Rocket,
    features: [
      { name: "5 idea generations/month", included: true },
      { name: "Basic 4-dimension scoring", included: true },
      { name: "Community trends access", included: true },
      { name: "Email support", included: true },
      { name: "AI research agent", included: false },
      { name: "Builder integrations", included: false },
      { name: "Team collaboration", included: false },
      { name: "API access", included: false },
    ],
    cta: "Get Started Free",
    href: "/auth/signup",
    popular: false,
  },
  {
    name: "Starter",
    price: "$19",
    period: "/month",
    description: "For solo founders validating ideas",
    icon: Zap,
    features: [
      { name: "50 idea generations/month", included: true },
      { name: "8-dimension scoring", included: true },
      { name: "Full trends database", included: true },
      { name: "Priority email support", included: true },
      { name: "AI research agent (10/mo)", included: true },
      { name: "Builder integrations", included: false },
      { name: "Team collaboration", included: false },
      { name: "API access", included: false },
    ],
    cta: "Start 14-Day Trial",
    href: "/auth/signup?plan=starter",
    popular: false,
    savings: "Save $150/mo vs competitors",
  },
  {
    name: "Pro",
    price: "$49",
    period: "/month",
    description: "For serious founders building businesses",
    icon: Crown,
    features: [
      { name: "Unlimited idea generations", included: true },
      { name: "8-dimension scoring", included: true },
      { name: "Full trends + predictions", included: true },
      { name: "24/7 priority support", included: true },
      { name: "AI research agent (50/mo)", included: true },
      { name: "Builder integrations (5)", included: true },
      { name: "Team collaboration (5 seats)", included: true },
      { name: "API access (10K calls)", included: false },
    ],
    cta: "Start 14-Day Trial",
    href: "/auth/signup?plan=pro",
    popular: true,
    savings: "Save $500/mo vs Datadog",
  },
  {
    name: "Enterprise",
    price: "$299",
    period: "/month",
    description: "For agencies and large teams",
    icon: Building2,
    features: [
      { name: "Unlimited everything", included: true },
      { name: "White-label branding", included: true },
      { name: "Custom domain", included: true },
      { name: "Dedicated account manager", included: true },
      { name: "AI research agent (unlimited)", included: true },
      { name: "All builder integrations", included: true },
      { name: "Unlimited team seats", included: true },
      { name: "API access (unlimited)", included: true },
    ],
    cta: "Contact Sales",
    href: "/contact?plan=enterprise",
    popular: false,
    savings: "Save $5K+/mo vs building in-house",
  },
];

const faqs = [
  {
    question: "Can I switch plans anytime?",
    answer: "Yes! You can upgrade or downgrade your plan at any time. When upgrading, you'll be charged the prorated difference. When downgrading, your new rate takes effect at the next billing cycle.",
  },
  {
    question: "What payment methods do you accept?",
    answer: "We accept all major credit cards (Visa, Mastercard, American Express) through our secure Stripe payment processor. Enterprise customers can also pay via invoice.",
  },
  {
    question: "Is there a free trial?",
    answer: "Yes! Both Starter and Pro plans come with a 14-day free trial. No credit card required to start. You'll only be charged if you decide to continue after the trial.",
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
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "StartInsight",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    url: "https://startinsight.app/pricing",
    offers: [
      { "@type": "Offer", name: "Free", price: "0", priceCurrency: "USD", description: "5 idea generations/month, basic scoring" },
      { "@type": "Offer", name: "Starter", price: "19", priceCurrency: "USD", billingIncrement: "MON", description: "50 ideas/month, 8-dimension scoring, AI research" },
      { "@type": "Offer", name: "Pro", price: "49", priceCurrency: "USD", billingIncrement: "MON", description: "Unlimited ideas, full research, builder integrations, team" },
      { "@type": "Offer", name: "Enterprise", price: "299", priceCurrency: "USD", billingIncrement: "MON", description: "White-label, dedicated support, custom integrations" },
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
          <span>14-day free trial</span>
          <span className="mx-2">|</span>
          <Check className="h-4 w-4 text-green-500" />
          <span>Cancel anytime</span>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="container mx-auto px-4 pb-16">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
          {tiers.map((tier) => (
            <Card
              key={tier.name}
              className={`relative flex flex-col ${
                tier.popular ? "border-primary shadow-lg scale-105" : ""
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
                {tier.savings && (
                  <Badge variant="outline" className="w-full justify-center mb-4 text-green-600 border-green-600">
                    {tier.savings}
                  </Badge>
                )}
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
                  <Link href={tier.href}>{tier.cta}</Link>
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
          <table className="w-full max-w-5xl mx-auto border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left py-4 px-4 font-medium">Feature</th>
                <th className="text-center py-4 px-4 font-medium">Free</th>
                <th className="text-center py-4 px-4 font-medium">Starter</th>
                <th className="text-center py-4 px-4 font-medium bg-primary/5">Pro</th>
                <th className="text-center py-4 px-4 font-medium">Enterprise</th>
              </tr>
            </thead>
            <tbody>
              {[
                { feature: "Idea Generations", free: "5/mo", starter: "50/mo", pro: "Unlimited", enterprise: "Unlimited" },
                { feature: "Scoring Dimensions", free: "4", starter: "8", pro: "8", enterprise: "8 + Custom" },
                { feature: "AI Research Reports", free: "-", starter: "10/mo", pro: "50/mo", enterprise: "Unlimited" },
                { feature: "Trend Predictions", free: "-", starter: "-", pro: "7-day", enterprise: "30-day" },
                { feature: "Builder Integrations", free: "-", starter: "-", pro: "5", enterprise: "All" },
                { feature: "Team Seats", free: "1", starter: "1", pro: "5", enterprise: "Unlimited" },
                { feature: "API Calls", free: "-", starter: "-", pro: "10K/mo", enterprise: "Unlimited" },
                { feature: "Data Retention", free: "7 days", starter: "30 days", pro: "1 year", enterprise: "Unlimited" },
                { feature: "Support", free: "Email", starter: "Priority", pro: "24/7", enterprise: "Dedicated" },
                { feature: "White-Label", free: "-", starter: "-", pro: "-", enterprise: "Yes" },
              ].map((row) => (
                <tr key={row.feature} className="border-b hover:bg-muted/50">
                  <td className="py-3 px-4 text-sm">{row.feature}</td>
                  <td className="py-3 px-4 text-center text-sm text-muted-foreground">{row.free}</td>
                  <td className="py-3 px-4 text-center text-sm">{row.starter}</td>
                  <td className="py-3 px-4 text-center text-sm bg-primary/5 font-medium">{row.pro}</td>
                  <td className="py-3 px-4 text-center text-sm">{row.enterprise}</td>
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
              Join 10,000+ founders who discovered their startup ideas with StartInsight.
            </p>
            <Button asChild size="lg" variant="secondary">
              <Link href="/auth/signup">Start Free Trial</Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
