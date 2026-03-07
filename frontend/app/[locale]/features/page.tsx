"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getSupabaseClient } from "@/lib/supabase/client";
import {
  Sparkles,
  Search,
  BarChart3,
  TrendingUp,
  Zap,
  Users,
  Shield,
  Globe,
  Layers,
  Download,
  Bell,
  Code,
  Building2,
  Clock,
  CheckCircle2,
  Star,
  Target,
  Lightbulb,
  MessageSquare,
  Workflow,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const featureCategories = [
  {
    id: "discovery",
    name: "Discovery",
    features: [
      {
        icon: Sparkles,
        title: "AI Idea Generation",
        description: "Generate validated startup ideas from real market signals. Our AI analyzes millions of conversations to surface opportunities others miss.",
        badge: "Core",
      },
      {
        icon: BarChart3,
        title: "8-Dimension Scoring",
        description: "Every idea is scored across 8 critical dimensions: market size, competition, timing, technical feasibility, monetization potential, and more.",
        badge: "Unique",
      },
      {
        icon: TrendingUp,
        title: "Trend Analysis",
        description: "Track 180+ trending keywords with search volume, growth rates, and business implications updated in real-time.",
        badge: null,
      },
      {
        icon: Globe,
        title: "Multi-Source Data",
        description: "Aggregate insights from Reddit, Hacker News, Product Hunt, Twitter/X, Google Trends, and industry reports.",
        badge: null,
      },
    ],
  },
  {
    id: "research",
    name: "Research",
    features: [
      {
        icon: Search,
        title: "40-Step AI Research Agent",
        description: "Deep competitive analysis, market sizing, customer personas, and technical requirements—delivered in minutes, not weeks.",
        badge: "Pro",
      },
      {
        icon: Target,
        title: "Competitor Tracking",
        description: "Automatically monitor competitors with weekly snapshots, change detection, and market positioning analysis.",
        badge: "Pro",
      },
      {
        icon: Lightbulb,
        title: "Trend Predictions",
        description: "AI-powered 7-day forecasts help you catch trends before they go mainstream.",
        badge: "Pro",
      },
      {
        icon: MessageSquare,
        title: "Community Signals",
        description: "Analyze sentiment and engagement from startup communities to validate market demand.",
        badge: null,
      },
    ],
  },
  {
    id: "build",
    name: "Build",
    features: [
      {
        icon: Zap,
        title: "Builder Integrations",
        description: "One-click export to Lovable, Bolt, Replit, and more. Turn validated ideas into working prototypes instantly.",
        badge: "Pro",
      },
      {
        icon: Download,
        title: "Export Options",
        description: "Export research to PDF, CSV, or JSON. Perfect for sharing with co-founders, investors, or your team.",
        badge: null,
      },
      {
        icon: Workflow,
        title: "Brand Generator",
        description: "Generate brand names, taglines, and visual identity recommendations for your startup idea.",
        badge: null,
      },
      {
        icon: Code,
        title: "Landing Page Builder",
        description: "Create landing pages to validate demand before building your full product.",
        badge: "Pro",
      },
    ],
  },
  {
    id: "collaborate",
    name: "Collaborate",
    features: [
      {
        icon: Users,
        title: "Team Workspaces",
        description: "Share ideas, leave comments, and collaborate with your co-founders and team members.",
        badge: "Pro",
      },
      {
        icon: Bell,
        title: "Smart Notifications",
        description: "Get alerts when new opportunities match your criteria or when saved ideas show significant changes.",
        badge: null,
      },
      {
        icon: Clock,
        title: "Real-Time Updates",
        description: "Live updates via SSE ensure you're always working with the latest data.",
        badge: null,
      },
      {
        icon: Layers,
        title: "Saved Collections",
        description: "Organize ideas into collections, rate them, and track your evaluation progress.",
        badge: null,
      },
    ],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    features: [
      {
        icon: Building2,
        title: "White-Label",
        description: "Full white-label support with custom branding, domains, and UI themes for agencies.",
        badge: "Enterprise",
      },
      {
        icon: Code,
        title: "API Access",
        description: "RESTful API with 130+ endpoints. Build custom integrations and workflows.",
        badge: "Enterprise",
      },
      {
        icon: Shield,
        title: "Enterprise Security",
        description: "SSO, audit logs, data residency options, and dedicated support for enterprise teams.",
        badge: "Enterprise",
      },
      {
        icon: Star,
        title: "Priority Support",
        description: "Dedicated account manager, SLA guarantees, and custom onboarding.",
        badge: "Enterprise",
      },
    ],
  },
];

export default function FeaturesPage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await getSupabaseClient().auth.getSession();
      setIsLoggedIn(!!session);
    };
    void checkAuth();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Badge variant="secondary" className="mb-4">Features</Badge>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Everything You Need to Find & Validate Ideas
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
          From AI-powered discovery to one-click prototyping, StartInsight gives you the complete toolkit for startup ideation.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button asChild size="lg">
            <Link href={isLoggedIn ? "/dashboard" : "/auth/signup"}>
              {isLoggedIn ? "Go to Dashboard" : "Start Free Trial"}
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/pricing">View Pricing</Link>
          </Button>
        </div>
      </section>

      {/* Feature Tabs */}
      <section className="container mx-auto px-4 pb-16">
        <Tabs defaultValue="discovery" className="max-w-5xl mx-auto">
          <TabsList className="grid w-full grid-cols-5 mb-8">
            {featureCategories.map((category) => (
              <TabsTrigger key={category.id} value={category.id}>
                {category.name}
              </TabsTrigger>
            ))}
          </TabsList>
          {featureCategories.map((category) => (
            <TabsContent key={category.id} value={category.id}>
              <div className="grid md:grid-cols-2 gap-6">
                {category.features.map((feature) => (
                  <Card key={feature.title}>
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <div className="p-2 rounded-lg bg-primary/10 w-fit">
                          <feature.icon className="h-6 w-6 text-primary" />
                        </div>
                        {feature.badge && (
                          <Badge
                            variant={
                              feature.badge === "Unique"
                                ? "default"
                                : feature.badge === "Enterprise"
                                ? "secondary"
                                : "outline"
                            }
                          >
                            {feature.badge}
                          </Badge>
                        )}
                      </div>
                      <CardTitle className="mt-4">{feature.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CardDescription>{feature.description}</CardDescription>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </section>

      {/* Comparison Section */}
      <section className="container mx-auto px-4 py-16 bg-muted/30">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Why Choose StartInsight?</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            See how we compare to doing market research manually.
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="text-red-500">Manual Research</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                "2-4 weeks per idea validation",
                "Scattered data across tools",
                "Subjective scoring",
                "No trend predictions",
                "Manual competitor tracking",
                "No builder integrations",
              ].map((item, index) => (
                <div key={index} className="flex items-center gap-2 text-muted-foreground">
                  <div className="h-2 w-2 rounded-full bg-red-500" />
                  <span>{item}</span>
                </div>
              ))}
            </CardContent>
          </Card>
          <Card className="border-primary">
            <CardHeader>
              <CardTitle className="text-primary">With StartInsight</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                "Ideas validated in minutes",
                "All data in one dashboard",
                "8-dimension AI scoring",
                "7-day trend predictions",
                "Automated competitor monitoring",
                "One-click to Lovable/Bolt/Replit",
              ].map((item, index) => (
                <div key={index} className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <span>{item}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Card className="max-w-2xl mx-auto bg-primary text-primary-foreground">
          <CardContent className="pt-8 pb-8">
            <h2 className="text-2xl font-bold mb-2">Ready to Discover Your Next Big Idea?</h2>
            <p className="mb-6 text-primary-foreground/80">
              Join 10,000+ founders using AI-powered idea discovery.
            </p>
            <Button asChild size="lg" variant="secondary">
              <Link href={isLoggedIn ? "/dashboard" : "/auth/signup"}>
              {isLoggedIn ? "Go to Dashboard" : "Start Free Trial"}
            </Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
