"use client";

import Link from "next/link";
import {
  Sparkles,
  Search,
  BarChart3,
  Zap,
  ArrowRight,
  CheckCircle2,
  TrendingUp,
  Target,
  Lightbulb,
  Layers,
  Globe,
  LineChart,
  Users,
  Rocket,
  Brain,
  Database,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const tourSteps = [
  {
    step: 1,
    title: "Discover Ideas",
    description: "Browse AI-generated startup opportunities based on real market signals and trending topics.",
    icon: Sparkles,
    color: "from-blue-500 to-cyan-500",
    features: [
      "8-dimension scoring for every idea",
      "Filter by market, timing, or competition",
      "Real-time trend integration",
    ],
  },
  {
    step: 2,
    title: "Deep Research",
    description: "Use our 40-step AI Research Agent to validate any idea with comprehensive market analysis.",
    icon: Search,
    color: "from-violet-500 to-purple-500",
    features: [
      "Competitor landscape analysis",
      "Market size estimation (TAM/SAM/SOM)",
      "Customer persona generation",
    ],
  },
  {
    step: 3,
    title: "Build & Launch",
    description: "Export validated ideas directly to AI builders like Lovable, Bolt, and Replit.",
    icon: Rocket,
    color: "from-orange-500 to-red-500",
    features: [
      "One-click export with specs",
      "Brand package generation",
      "Landing page templates",
    ],
  },
];

const platformStats = [
  { label: "Startup Ideas Analyzed", value: "50+", icon: Lightbulb },
  { label: "Data Sources", value: "5+", icon: Database },
  { label: "Scoring Dimensions", value: "8", icon: Target },
  { label: "Trending Keywords", value: "180+", icon: TrendingUp },
];

const useCases = [
  {
    title: "First-Time Founders",
    description: "Find and validate your first startup idea without months of research. Get confidence in your direction with data-backed insights.",
    icon: Sparkles,
    gradient: "from-blue-500/10 to-cyan-500/10",
  },
  {
    title: "Serial Entrepreneurs",
    description: "Rapidly scan for new opportunities and diversify your portfolio. Use AI research to move fast on promising ideas.",
    icon: Search,
    gradient: "from-violet-500/10 to-purple-500/10",
  },
  {
    title: "Venture Studios",
    description: "Generate a pipeline of validated ideas at scale. White-label support for your own branded discovery platform.",
    icon: BarChart3,
    gradient: "from-emerald-500/10 to-green-500/10",
  },
  {
    title: "Indie Hackers",
    description: "Find niche opportunities with low competition. Export directly to no-code builders and ship in days, not months.",
    icon: Zap,
    gradient: "from-amber-500/10 to-orange-500/10",
  },
];

function DiscoveryPreview() {
  const sampleIdeas = [
    { name: "AI Code Review", score: 8.4, market: "$12B", trend: "+24%" },
    { name: "ClimateTech SaaS", score: 7.9, market: "$8.5B", trend: "+31%" },
    { name: "AI Study Tutor", score: 7.6, market: "$5.2B", trend: "+18%" },
  ];

  return (
    <div className="bg-background rounded-xl border shadow-sm p-4 space-y-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold">Top Scored Ideas</span>
        </div>
        <Badge variant="secondary" className="text-xs">Live Data</Badge>
      </div>
      {sampleIdeas.map((idea, i) => (
        <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">
              {i + 1}
            </div>
            <div>
              <p className="font-medium text-sm">{idea.name}</p>
              <p className="text-xs text-muted-foreground">Market: {idea.market}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="font-bold text-sm text-primary">{idea.score}/10</p>
            <p className="text-xs text-green-600">{idea.trend}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function ResearchPreview() {
  const dimensions = [
    { name: "Opportunity", score: 9, color: "bg-blue-500" },
    { name: "Problem", score: 8, color: "bg-violet-500" },
    { name: "Feasibility", score: 7, color: "bg-emerald-500" },
    { name: "Timing", score: 9, color: "bg-amber-500" },
    { name: "GTM", score: 7, color: "bg-rose-500" },
    { name: "Revenue", score: 8, color: "bg-cyan-500" },
  ];

  return (
    <div className="bg-background rounded-xl border shadow-sm p-4 space-y-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold">Research Report</span>
        </div>
        <Badge variant="outline" className="text-xs">AI-Generated</Badge>
      </div>
      <div className="space-y-2">
        {dimensions.map((dim, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-20">{dim.name}</span>
            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
              <div className={`h-full ${dim.color} rounded-full transition-all`} style={{ width: `${dim.score * 10}%` }} />
            </div>
            <span className="text-xs font-medium w-6 text-right">{dim.score}</span>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-2 pt-2 border-t">
        <div className="text-center">
          <p className="text-xs text-muted-foreground">TAM</p>
          <p className="text-sm font-bold text-blue-600">$12B</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-muted-foreground">SAM</p>
          <p className="text-sm font-bold text-green-600">$3.2B</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-muted-foreground">SOM</p>
          <p className="text-sm font-bold text-violet-600">$180M</p>
        </div>
      </div>
    </div>
  );
}

function TrendsPreview() {
  const trends = [
    { keyword: "AI Agents", volume: "135K", growth: "+42%", status: "Rising" },
    { keyword: "MCP Protocol", volume: "89K", growth: "+67%", status: "Breakout" },
    { keyword: "Vibe Coding", volume: "45K", growth: "+120%", status: "Breakout" },
    { keyword: "AI Wearables", volume: "72K", growth: "+28%", status: "Rising" },
  ];

  return (
    <div className="bg-background rounded-xl border shadow-sm p-4 space-y-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold">Trending Now</span>
        </div>
        <Badge variant="secondary" className="text-xs">Real-time</Badge>
      </div>
      {trends.map((trend, i) => (
        <div key={i} className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50 transition-colors">
          <div className="flex items-center gap-2">
            <LineChart className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-sm font-medium">{trend.keyword}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground">{trend.volume}/mo</span>
            <span className="text-xs font-medium text-green-600">{trend.growth}</span>
            <Badge variant={trend.status === "Breakout" ? "default" : "outline"} className="text-[10px] px-1.5 py-0">
              {trend.status}
            </Badge>
          </div>
        </div>
      ))}
    </div>
  );
}

function BuildPreview() {
  const builders = [
    { name: "Lovable", status: "Ready", type: "Full-Stack" },
    { name: "Bolt", status: "Ready", type: "Rapid MVP" },
    { name: "Replit", status: "Ready", type: "Code IDE" },
    { name: "v0 by Vercel", status: "Ready", type: "UI/Frontend" },
  ];

  return (
    <div className="bg-background rounded-xl border shadow-sm p-4 space-y-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold">Export to Builder</span>
        </div>
        <Badge variant="outline" className="text-xs">One-Click</Badge>
      </div>
      <div className="space-y-2">
        {builders.map((builder, i) => (
          <div key={i} className="flex items-center justify-between p-3 rounded-lg border hover:border-primary/50 hover:bg-primary/5 transition-all cursor-pointer">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                {builder.name[0]}
              </div>
              <div>
                <p className="font-medium text-sm">{builder.name}</p>
                <p className="text-xs text-muted-foreground">{builder.type}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-green-600 font-medium">{builder.status}</span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function PlatformTourPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Hero Section */}
      <section className="container mx-auto px-4 pt-16 pb-12 text-center">
        <Badge variant="secondary" className="mb-4">Platform Tour</Badge>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          See StartInsight in Action
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
          Discover how AI-powered idea discovery can transform your entrepreneurial journey.
        </p>

        {/* Stats Banner */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto mb-10">
          {platformStats.map((stat) => (
            <div key={stat.label} className="flex flex-col items-center p-4 rounded-xl bg-muted/50 border">
              <stat.icon className="h-5 w-5 text-primary mb-2" />
              <span className="text-2xl font-bold">{stat.value}</span>
              <span className="text-xs text-muted-foreground text-center">{stat.label}</span>
            </div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button asChild size="lg">
            <Link href="/auth/signup">Start Free Trial</Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/insights">Browse Live Ideas</Link>
          </Button>
        </div>
      </section>

      {/* How It Works - Enhanced with icons and gradients */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">How It Works</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            From discovery to launch in three simple steps.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {tourSteps.map((step, index) => (
            <div key={step.step} className="relative">
              {/* Connector line */}
              {index < tourSteps.length - 1 && (
                <div className="hidden md:block absolute top-12 left-[calc(50%+3rem)] w-[calc(100%-3rem)] h-0.5 bg-gradient-to-r from-border to-border/0" />
              )}
              <Card className="relative overflow-hidden">
                <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${step.color}`} />
                <CardHeader className="pt-8 text-center">
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center mx-auto mb-4`}>
                    <step.icon className="h-7 w-7 text-white" />
                  </div>
                  <div className="text-xs font-medium text-muted-foreground mb-1">STEP {step.step}</div>
                  <CardTitle className="text-xl">{step.title}</CardTitle>
                  <CardDescription className="mt-2">{step.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {step.features.map((feature, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm">
                        <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      </section>

      {/* Interactive Feature Tabs with Live Previews */}
      <section className="container mx-auto px-4 py-16 bg-muted/30">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Explore the Platform</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Dive deeper into each area of the platform with live previews.
          </p>
        </div>
        <Tabs defaultValue="discovery" className="max-w-5xl mx-auto">
          <TabsList className="grid w-full grid-cols-4 mb-8">
            <TabsTrigger value="discovery">Discovery</TabsTrigger>
            <TabsTrigger value="research">Research</TabsTrigger>
            <TabsTrigger value="trends">Trends</TabsTrigger>
            <TabsTrigger value="build">Build</TabsTrigger>
          </TabsList>
          <TabsContent value="discovery">
            <Card>
              <CardContent className="pt-6">
                <div className="grid md:grid-cols-2 gap-8 items-start">
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <Brain className="h-5 w-5 text-primary" />
                      <h3 className="text-xl font-semibold">AI-Powered Idea Discovery</h3>
                    </div>
                    <p className="text-muted-foreground mb-4">
                      Our AI analyzes millions of conversations across Reddit, Hacker News, and Product Hunt
                      to identify emerging pain points and market opportunities.
                    </p>
                    <ul className="space-y-2 mb-6">
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>8-dimension scoring system</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>Real-time market signals</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>Validated demand indicators</span>
                      </li>
                    </ul>
                    <Button asChild>
                      <Link href="/insights">
                        Browse Ideas
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </Link>
                    </Button>
                  </div>
                  <DiscoveryPreview />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="research">
            <Card>
              <CardContent className="pt-6">
                <div className="grid md:grid-cols-2 gap-8 items-start">
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <Search className="h-5 w-5 text-primary" />
                      <h3 className="text-xl font-semibold">40-Step AI Research Agent</h3>
                    </div>
                    <p className="text-muted-foreground mb-4">
                      Get comprehensive market analysis in minutes. Our AI Research Agent performs
                      deep competitive analysis, market sizing, and customer persona generation.
                    </p>
                    <ul className="space-y-2 mb-6">
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>Competitor landscape mapping</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>TAM/SAM/SOM calculations</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>Detailed persona profiles</span>
                      </li>
                    </ul>
                    <Button asChild>
                      <Link href="/research">
                        Try Research Agent
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </Link>
                    </Button>
                  </div>
                  <ResearchPreview />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="trends">
            <Card>
              <CardContent className="pt-6">
                <div className="grid md:grid-cols-2 gap-8 items-start">
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <TrendingUp className="h-5 w-5 text-primary" />
                      <h3 className="text-xl font-semibold">Real-Time Trend Analysis</h3>
                    </div>
                    <p className="text-muted-foreground mb-4">
                      Track 180+ trending keywords with search volume, growth rates, and
                      7-day predictions. Catch opportunities before they go mainstream.
                    </p>
                    <ul className="space-y-2 mb-6">
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>Google Trends integration</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>AI-powered predictions</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>Business implications</span>
                      </li>
                    </ul>
                    <Button asChild>
                      <Link href="/trends">
                        Explore Trends
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </Link>
                    </Button>
                  </div>
                  <TrendsPreview />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="build">
            <Card>
              <CardContent className="pt-6">
                <div className="grid md:grid-cols-2 gap-8 items-start">
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <Zap className="h-5 w-5 text-primary" />
                      <h3 className="text-xl font-semibold">One-Click Builder Export</h3>
                    </div>
                    <p className="text-muted-foreground mb-4">
                      Export validated ideas directly to Lovable, Bolt, Replit, and more.
                      Turn concepts into working prototypes without writing code.
                    </p>
                    <ul className="space-y-2 mb-6">
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>5 builder integrations</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>Auto-generated specs</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span>Brand package export</span>
                      </li>
                    </ul>
                    <Button asChild>
                      <Link href="/auth/signup">
                        Start Building
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </Link>
                    </Button>
                  </div>
                  <BuildPreview />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </section>

      {/* Use Cases - Enhanced with gradients */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Built for Every Founder</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Whether you&apos;re just starting out or scaling your portfolio.
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {useCases.map((useCase) => (
            <Card key={useCase.title} className="overflow-hidden hover:shadow-lg transition-shadow">
              <div className={`h-2 bg-gradient-to-r ${useCase.gradient}`} />
              <CardContent className="pt-6">
                <div className="p-3 rounded-xl bg-primary/10 w-fit mb-4">
                  <useCase.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold mb-2">{useCase.title}</h3>
                <p className="text-sm text-muted-foreground">{useCase.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Social Proof Section */}
      <section className="container mx-auto px-4 py-16 bg-muted/30">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold mb-4">Trusted by Founders Worldwide</h2>
          <p className="text-muted-foreground mb-8">
            From idea to launch, StartInsight helps founders make data-driven decisions.
          </p>
          <div className="grid grid-cols-3 gap-8">
            <div>
              <div className="text-3xl font-bold text-primary">50+</div>
              <div className="text-sm text-muted-foreground">AI-Scored Ideas</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary">5+</div>
              <div className="text-sm text-muted-foreground">Data Sources</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary">40</div>
              <div className="text-sm text-muted-foreground">Research Steps</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Card className="max-w-2xl mx-auto bg-primary text-primary-foreground">
          <CardContent className="pt-8 pb-8">
            <h2 className="text-2xl font-bold mb-2">Ready to Get Started?</h2>
            <p className="mb-6 text-primary-foreground/80">
              Join founders discovering their next big idea with AI-powered insights.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button asChild size="lg" variant="secondary">
                <Link href="/auth/signup">Start Free Trial</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="border-primary-foreground/30 text-primary-foreground hover:bg-primary-foreground/10">
                <Link href="/insights">Browse Ideas First</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
