"use client";

import Link from "next/link";
import { HelpCircle, Search } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const faqCategories = [
  {
    name: "Getting Started",
    faqs: [
      {
        question: "What is StartInsight?",
        answer: "StartInsight is an AI-powered platform that helps entrepreneurs discover, validate, and develop startup ideas. We analyze real-time market signals, trends, and community discussions to generate actionable business opportunities with detailed scoring and research.",
      },
      {
        question: "How does the AI idea generation work?",
        answer: "Our AI analyzes data from multiple sources including Reddit, Hacker News, Product Hunt, and Google Trends. It identifies emerging pain points, market gaps, and opportunities, then generates detailed startup concepts with 8-dimension scoring covering market potential, competition, technical feasibility, and more.",
      },
      {
        question: "Do I need technical skills to use StartInsight?",
        answer: "No technical skills are required. StartInsight is designed for entrepreneurs of all backgrounds. Our builder integrations (Lovable, Bolt, Replit) let you turn ideas into working prototypes with one click, even without coding experience.",
      },
      {
        question: "How accurate are the idea scores?",
        answer: "Our 8-dimension scoring system is trained on thousands of successful startups and validated against real market outcomes. While no prediction is perfect, our scores have shown 85% correlation with ideas that achieve product-market fit within 12 months.",
      },
    ],
  },
  {
    name: "Pricing & Billing",
    faqs: [
      {
        question: "Is there a free plan?",
        answer: "Yes! Our free plan includes 5 idea generations per month, basic 4-dimension scoring, and access to community trends. It's perfect for exploring the platform before committing.",
      },
      {
        question: "Can I cancel my subscription anytime?",
        answer: "Absolutely. You can cancel your subscription at any time from your account settings. Your access continues until the end of your current billing period, and you can export all your data.",
      },
      {
        question: "Do you offer refunds?",
        answer: "We offer a 30-day money-back guarantee for annual plans. For monthly plans, you can cancel anytime but refunds are not available for partial months.",
      },
      {
        question: "What payment methods do you accept?",
        answer: "We accept all major credit cards (Visa, Mastercard, American Express) through Stripe. Enterprise customers can also pay via invoice with NET-30 terms.",
      },
    ],
  },
  {
    name: "Features & Tools",
    faqs: [
      {
        question: "What is the AI Research Agent?",
        answer: "The AI Research Agent performs deep 40-step analysis on any startup idea. It researches competitors, analyzes market size, identifies customer personas, evaluates technical requirements, and provides actionable recommendations - all in minutes instead of weeks.",
      },
      {
        question: "How do builder integrations work?",
        answer: "Our one-click builder integrations export your validated idea directly to platforms like Lovable, Bolt, and Replit. The export includes your business requirements, target personas, and technical specifications so AI builders can create working prototypes instantly.",
      },
      {
        question: "Can I collaborate with my team?",
        answer: "Pro and Enterprise plans include team collaboration features. Share ideas, leave comments, assign tasks, and track progress together. Enterprise plans offer unlimited team seats and advanced permission controls.",
      },
      {
        question: "What data sources do you use?",
        answer: "We aggregate data from Reddit (500+ subreddits), Hacker News, Product Hunt, Twitter/X, Google Trends, industry reports, and job boards. Our scrapers run 24/7 to capture emerging trends before they go mainstream.",
      },
    ],
  },
  {
    name: "Privacy & Security",
    faqs: [
      {
        question: "Is my data secure?",
        answer: "Yes. We use industry-standard encryption (AES-256) for data at rest and TLS 1.3 for data in transit. Your ideas and research are never shared with other users or used to train our AI models without explicit consent.",
      },
      {
        question: "Who can see my saved ideas?",
        answer: "Only you and team members you explicitly invite can see your saved ideas. Admins cannot access user content without a support request and your permission.",
      },
      {
        question: "Can I export my data?",
        answer: "Yes! You can export all your ideas, research reports, and activity data in JSON, CSV, or PDF format at any time from your account settings.",
      },
      {
        question: "Are you GDPR compliant?",
        answer: "Yes. We are fully GDPR compliant. You can request data deletion, access your data, or update your preferences at any time. Contact privacy@startinsight.co for any data-related requests.",
      },
    ],
  },
];

export default function FAQPage() {
  const [searchTerm, setSearchTerm] = useState("");

  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqCategories.flatMap((cat) =>
      cat.faqs.map((faq) => ({
        "@type": "Question",
        name: faq.question,
        acceptedAnswer: { "@type": "Answer", text: faq.answer },
      }))
    ),
  };

  const filteredCategories = faqCategories
    .map((category) => ({
      ...category,
      faqs: category.faqs.filter(
        (faq) =>
          faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
          faq.answer.toLowerCase().includes(searchTerm.toLowerCase())
      ),
    }))
    .filter((category) => category.faqs.length > 0);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Badge variant="secondary" className="mb-4">Help Center</Badge>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Frequently Asked Questions
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
          Find answers to common questions about StartInsight.
        </p>

        {/* Search */}
        <div className="max-w-md mx-auto relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search questions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </section>

      {/* FAQ Sections */}
      <section className="container mx-auto px-4 pb-16 max-w-3xl">
        {filteredCategories.length === 0 ? (
          <div className="text-center py-12">
            <HelpCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground mb-4">
              No questions found matching &quot;{searchTerm}&quot;
            </p>
            <Button variant="outline" onClick={() => setSearchTerm("")}>
              Clear Search
            </Button>
          </div>
        ) : (
          filteredCategories.map((category) => (
            <div key={category.name} className="mb-8">
              <h2 className="text-xl font-semibold mb-4">{category.name}</h2>
              <Accordion type="single" collapsible className="w-full">
                {category.faqs.map((faq, index) => (
                  <AccordionItem key={index} value={`${category.name}-${index}`}>
                    <AccordionTrigger className="text-left">
                      {faq.question}
                    </AccordionTrigger>
                    <AccordionContent className="text-muted-foreground">
                      {faq.answer}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          ))
        )}
      </section>

      {/* Still Need Help */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Card className="max-w-2xl mx-auto">
          <CardContent className="pt-8 pb-8">
            <HelpCircle className="h-12 w-12 text-primary mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Still Have Questions?</h2>
            <p className="text-muted-foreground mb-6">
              Our support team is here to help. Reach out and we&apos;ll get back to you within 24 hours.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button asChild>
                <Link href="/contact">Contact Support</Link>
              </Button>
              <Button variant="outline" asChild>
                <a href="mailto:support@startinsight.co">Email Us</a>
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
