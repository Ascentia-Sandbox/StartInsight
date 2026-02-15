"use client";

import Link from "next/link";
import { Lightbulb, Target, Users, Zap, Globe, Heart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const values = [
  {
    icon: Lightbulb,
    title: "Innovation First",
    description: "We believe everyone deserves access to the insights that make great businesses.",
  },
  {
    icon: Target,
    title: "Data-Driven Decisions",
    description: "Replace guesswork with real market intelligence and validated opportunities.",
  },
  {
    icon: Users,
    title: "Founder-Focused",
    description: "Built by founders, for founders. We understand the startup journey intimately.",
  },
  {
    icon: Zap,
    title: "Speed to Market",
    description: "Go from idea to validated concept in hours, not months.",
  },
  {
    icon: Globe,
    title: "Global Perspective",
    description: "Analyze trends across markets and geographies for worldwide opportunities.",
  },
  {
    icon: Heart,
    title: "Democratized Access",
    description: "Make enterprise-grade market intelligence accessible to everyone.",
  },
];

const milestones = [
  { year: "2024", event: "StartInsight founded with a mission to democratize startup discovery" },
  { year: "2024", event: "Launched AI-powered idea generation and 8-dimension scoring" },
  { year: "2024", event: "Reached 1,000 founders using the platform" },
  { year: "2025", event: "Introduced 40-step AI Research Agent" },
  { year: "2025", event: "Builder integrations with Lovable, Bolt, and Replit" },
  { year: "2025", event: "10,000+ founders and $50M+ in ideas launched" },
];

const orgJsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "StartInsight",
  url: "https://startinsight.app",
  description: "AI-powered startup idea discovery platform helping entrepreneurs find, validate, and build their next venture.",
  foundingDate: "2024",
  sameAs: ["https://twitter.com/startinsight"],
};

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(orgJsonLd) }}
      />
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Badge variant="secondary" className="mb-4">About Us</Badge>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Democratizing Startup Discovery
        </h1>
        <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
          We believe great startup ideas shouldn't be limited to those with insider access.
          StartInsight uses AI to surface market opportunities that anyone can build into successful businesses.
        </p>
      </section>

      {/* Mission Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-2 gap-12 items-center max-w-5xl mx-auto">
          <div>
            <h2 className="text-3xl font-bold mb-4">Our Mission</h2>
            <p className="text-muted-foreground mb-4">
              The best startup ideas often come from deep market insights—understanding what
              people need before they know they need it. Traditionally, these insights were
              reserved for well-connected VCs and serial entrepreneurs.
            </p>
            <p className="text-muted-foreground mb-4">
              We're changing that. StartInsight analyzes millions of conversations, trends,
              and market signals to surface opportunities that are validated by real demand.
              Whether you're a first-time founder or a seasoned entrepreneur, you deserve
              access to the same quality of market intelligence.
            </p>
            <p className="text-muted-foreground">
              Our AI doesn't just generate ideas—it validates them against real market data,
              scores them across 8 critical dimensions, and provides the research you need
              to move forward with confidence.
            </p>
          </div>
          <Card className="bg-primary text-primary-foreground">
            <CardContent className="pt-8 pb-8 text-center">
              <div className="text-5xl font-bold mb-2">10,000+</div>
              <p className="text-primary-foreground/80 mb-6">Founders discovering ideas</p>
              <div className="text-5xl font-bold mb-2">$50M+</div>
              <p className="text-primary-foreground/80 mb-6">In launched businesses</p>
              <div className="text-5xl font-bold mb-2">85%</div>
              <p className="text-primary-foreground/80">Ideas that find product-market fit</p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Values Section */}
      <section className="container mx-auto px-4 py-16 bg-muted/30">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Our Values</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            These principles guide everything we do at StartInsight.
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {values.map((value) => (
            <Card key={value.title}>
              <CardContent className="pt-6">
                <value.icon className="h-10 w-10 text-primary mb-4" />
                <h3 className="text-lg font-semibold mb-2">{value.title}</h3>
                <p className="text-muted-foreground text-sm">{value.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Timeline Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Our Journey</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            From a simple idea to a platform used by thousands of founders.
          </p>
        </div>
        <div className="max-w-2xl mx-auto">
          {milestones.map((milestone, index) => (
            <div key={index} className="flex gap-4 mb-6">
              <div className="flex flex-col items-center">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">
                  {milestone.year}
                </div>
                {index < milestones.length - 1 && (
                  <div className="w-0.5 h-full bg-border mt-2" />
                )}
              </div>
              <div className="flex-1 pb-6">
                <p className="text-muted-foreground">{milestone.event}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Team Section */}
      <section className="container mx-auto px-4 py-16 bg-muted/30">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Built by Founders, for Founders</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Our team has collectively launched 12 startups, raised $40M, and experienced
            the pain of idea validation firsthand. We built the tool we wished we had.
          </p>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Card className="max-w-2xl mx-auto bg-primary text-primary-foreground">
          <CardContent className="pt-8 pb-8">
            <h2 className="text-2xl font-bold mb-2">Ready to Find Your Next Big Idea?</h2>
            <p className="mb-6 text-primary-foreground/80">
              Join 10,000+ founders who are discovering validated startup opportunities.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button asChild size="lg" variant="secondary">
                <Link href="/auth/signup">Start Free</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="bg-transparent border-primary-foreground/20 hover:bg-primary-foreground/10">
                <Link href="/contact">Talk to Us</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
