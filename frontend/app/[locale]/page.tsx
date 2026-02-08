"use client";

import { useEffect, useState } from "react";
import { useTranslations } from 'next-intl';
import Link from "next/link";
import {
  ArrowRight,
  Lightbulb,
  Search,
  BarChart3,
  Zap,
  CheckCircle2,
  Star,
  TrendingUp,
  Users,
  Rocket,
  Shield,
  Clock,
  Target,
  Play,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useTourContext } from "@/components/tour";
import { config } from "@/lib/env";

interface Insight {
  id: string;
  problem_statement: string;
  proposed_solution: string;
  market_size_estimate: string;
  relevance_score: number;
  founder_fit_score?: number;
  opportunity_score?: number;
  feasibility_score?: number;
  scores?: Record<string, number>;
  created_at: string;
}

interface Trend {
  id: string;
  keyword: string;
  growth_percentage: number;
  category: string;
}

export default function MarketingHomePage() {
  const t = useTranslations('home');
  const tFeatures = useTranslations('home.features');
  const tHow = useTranslations('home.how_it_works');
  const tTestimonials = useTranslations('home.testimonials');
  const tPricing = useTranslations('home.pricing');
  const { startTour, hasCompletedTour } = useTourContext();

  const features = [
    {
      title: tFeatures('feature_1_title'),
      description: tFeatures('feature_1_description'),
      icon: BarChart3,
    },
    {
      title: tFeatures('feature_2_title'),
      description: tFeatures('feature_2_description'),
      icon: Search,
    },
    {
      title: tFeatures('feature_3_title'),
      description: tFeatures('feature_3_description'),
      icon: TrendingUp,
    },
    {
      title: tFeatures('feature_4_title'),
      description: tFeatures('feature_4_description'),
      icon: Rocket,
    },
    {
      title: tFeatures('feature_5_title'),
      description: tFeatures('feature_5_description'),
      icon: Users,
    },
    {
      title: tFeatures('feature_6_title'),
      description: tFeatures('feature_6_description'),
      icon: Shield,
    },
  ];

  const howItWorks = [
    {
      step: 1,
      title: tHow('step_1_title'),
      description: tHow('step_1_description'),
    },
    {
      step: 2,
      title: tHow('step_2_title'),
      description: tHow('step_2_description'),
    },
    {
      step: 3,
      title: tHow('step_3_title'),
      description: tHow('step_3_description'),
    },
  ];

  const testimonials = [
    {
      quote: tTestimonials('quote_1'),
      name: tTestimonials('author_1'),
      company: tTestimonials('company_1'),
      avatar: null,
    },
    {
      quote: tTestimonials('quote_2'),
      name: tTestimonials('author_2'),
      company: tTestimonials('company_2'),
      avatar: null,
    },
    {
      quote: tTestimonials('quote_3'),
      name: tTestimonials('author_3'),
      company: tTestimonials('company_3'),
      avatar: null,
    },
  ];

  const pricingTiers = [
    {
      name: tPricing('tier_free_name'),
      price: tPricing('tier_free_price'),
      features: [tPricing('feature_insights_limit_10'), tPricing('feature_basic_scoring')],
      cta: tPricing('tier_free_cta')
    },
    {
      name: tPricing('tier_starter_name'),
      price: tPricing('tier_starter_price'),
      features: [tPricing('feature_insights_limit_50'), tPricing('feature_full_research')],
      popular: false,
      cta: tPricing('tier_starter_cta')
    },
    {
      name: tPricing('tier_pro_name'),
      price: tPricing('tier_pro_price'),
      features: [tPricing('feature_insights_unlimited'), tPricing('feature_ai_agent'), tPricing('feature_api_access')],
      popular: true,
      cta: tPricing('tier_pro_cta')
    },
    {
      name: tPricing('tier_enterprise_name'),
      price: tPricing('tier_enterprise_price'),
      features: [tPricing('feature_team_seats'), tPricing('feature_custom_research'), tPricing('feature_priority_support')],
      popular: false,
      cta: tPricing('tier_enterprise_cta')
    },
  ];

  const [featuredInsight, setFeaturedInsight] = useState<Insight | null>(null);
  const [recentInsights, setRecentInsights] = useState<Insight[]>([]);
  const [trendingKeywords, setTrendingKeywords] = useState<Trend[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const apiUrl = config.apiUrl;

    // Fetch each independently so one failure doesn't block others
    try {
      const res = await fetch(`${apiUrl}/api/insights/idea-of-the-day`);
      if (res.ok) {
        const data = await res.json();
        if (data) setFeaturedInsight(data);
      }
    } catch { /* backend unavailable */ }

    try {
      const res = await fetch(`${apiUrl}/api/insights?limit=6&sort=newest`);
      if (res.ok) {
        const data = await res.json();
        if (data.insights?.length > 0) setRecentInsights(data.insights.slice(0, 6));
      }
    } catch { /* backend unavailable */ }

    try {
      const res = await fetch(`${apiUrl}/api/trends?limit=6&sort=growth`);
      if (res.ok) {
        const data = await res.json();
        setTrendingKeywords(data.trends || []);
      }
    } catch { /* backend unavailable */ }

    setLoading(false);
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-blue-50 to-white dark:from-blue-950/20 dark:to-background">
        <div className="container mx-auto px-4 py-20 md:py-28 text-center">
          <Badge variant="secondary" className="mb-4">
            <Lightbulb className="h-3 w-3 mr-1" />
            {t('hero.badge')}
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent whitespace-pre-line">
            {t('hero.title')}
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
            {t('hero.subtitle')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center" data-tour="hero-cta">
            <Button asChild size="lg" className="text-lg px-8">
              <Link href="/insights">
                Explore Ideas
                <ArrowRight className="h-5 w-5 ml-2" />
              </Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="text-lg px-8"
              onClick={() => startTour('homepage')}
            >
              <Play className="h-5 w-5 mr-2" />
              {hasCompletedTour('homepage') ? 'Replay Tour' : 'Take a Tour'}
            </Button>
          </div>
        </div>
      </section>

      {/* Idea of the Day */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-8">
          <Badge className="mb-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white border-none">
            <Star className="h-3 w-3 mr-1 fill-white" />
            🌟 Idea of the Day
          </Badge>
        </div>
        {loading ? (
          <Skeleton className="h-64 max-w-3xl mx-auto" />
        ) : featuredInsight ? (
          <Card className="max-w-3xl mx-auto border-2 border-amber-500/30 shadow-lg bg-gradient-to-br from-amber-50/50 to-orange-50/50 dark:from-amber-950/20 dark:to-orange-950/20">
            <CardHeader>
              <div className="flex items-center justify-between mb-2">
                <Badge variant="outline" className="border-amber-500 text-amber-700 dark:text-amber-400">🌟 Today&apos;s Pick</Badge>
                <div className="flex items-center gap-1">
                  <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                  <span className="font-semibold">
                    {Math.round(featuredInsight.relevance_score * 10)}/10
                  </span>
                </div>
              </div>
              <CardTitle className="text-2xl">{featuredInsight.proposed_solution}</CardTitle>
              <CardDescription className="text-base">
                {featuredInsight.market_size_estimate} Market
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">{featuredInsight.problem_statement.split('.').slice(0, 2).join('.')}.</p>
              <div className="flex flex-wrap gap-2 mb-4">
                {featuredInsight.scores &&
                  Object.entries(featuredInsight.scores)
                    .slice(0, 4)
                    .map(([key, value]) => (
                      <Badge key={key} variant="secondary">
                        {key.replace(/_/g, " ")}: {value}/10
                      </Badge>
                    ))}
              </div>
              <Button asChild>
                <Link href={`/insights/${featuredInsight.id}`}>
                  {t('hero.cta_secondary')}
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Card className="max-w-3xl mx-auto">
            <CardContent className="py-12 text-center">
              <Lightbulb className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">
                {t('hero.no_featured_insight')}
              </p>
            </CardContent>
          </Card>
        )}
      </section>

      {/* Trending Keywords */}
      {trendingKeywords.length > 0 && (
        <section className="bg-muted/30 py-12">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold">Trending Now</h3>
              <Button asChild variant="ghost" size="sm">
                <Link href="/trends">
                  View All Trends
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </div>
            <div className="flex flex-wrap gap-3">
              {trendingKeywords.map((trend) => (
                <Badge
                  key={trend.id}
                  variant="outline"
                  className="px-4 py-2 text-sm hover:bg-primary/10 cursor-pointer"
                >
                  <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                  {trend.keyword}
                  <span className="ml-2 text-green-500 text-xs">+{trend.growth_percentage}%</span>
                </Badge>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* How It Works */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">{tHow('section_title')}</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {howItWorks.map((item) => (
            <div key={item.step} className="text-center">
              <div className="w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-xl mx-auto mb-4">
                {item.step}
              </div>
              <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
              <p className="text-muted-foreground">{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="bg-muted/30 py-16">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">{tFeatures('section_title')}</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              {tFeatures('section_subtitle')}
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {features.map((feature) => (
              <Card key={feature.title}>
                <CardContent className="pt-6">
                  <feature.icon className="h-10 w-10 text-primary mb-4" />
                  <h3 className="font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Recent Insights */}
      {recentInsights.length > 0 && (
        <section className="container mx-auto px-4 py-16">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold">Recent Ideas</h2>
              <p className="text-muted-foreground">Fresh opportunities discovered today</p>
            </div>
            <Button asChild variant="outline">
              <Link href="/insights">
                View All
                <ArrowRight className="h-4 w-4 ml-2" />
              </Link>
            </Button>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recentInsights.map((insight) => (
              <Card key={insight.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-lg line-clamp-2">
                      {insight.proposed_solution}
                    </CardTitle>
                    <Badge variant="secondary">{insight.market_size_estimate}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
                    {insight.problem_statement.split('.').slice(0, 2).join('.')}.
                  </p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    <div className="flex items-center gap-1 text-sm">
                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                      <span className="font-medium">
                        {Math.round(insight.relevance_score * 10)}/10
                      </span>
                    </div>
                    {insight.founder_fit_score && insight.founder_fit_score >= 7 && (
                      <Badge variant="outline" className="text-xs border-green-500 text-green-600 dark:text-green-400">
                        <Target className="h-3 w-3 mr-1" />
                        Founder Fit: {insight.founder_fit_score}/10
                      </Badge>
                    )}
                    {insight.feasibility_score && insight.feasibility_score >= 7 && (
                      <Badge variant="outline" className="text-xs border-blue-500 text-blue-600 dark:text-blue-400">
                        Easy Build
                      </Badge>
                    )}
                  </div>
                  <Button asChild variant="outline" size="sm" className="w-full">
                    <Link href={`/insights/${insight.id}`}>View Details</Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Testimonials */}
      <section className="bg-muted/30 py-16">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">{tTestimonials('section_title')}</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {testimonials.map((testimonial) => (
              <Card key={testimonial.name}>
                <CardContent className="pt-6">
                  <p className="text-muted-foreground mb-4">"{testimonial.quote}"</p>
                  <div className="flex items-center gap-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={testimonial.avatar || undefined} />
                      <AvatarFallback>
                        {testimonial.name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium">{testimonial.name}</p>
                      <p className="text-sm text-muted-foreground">{testimonial.company}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="text-center mt-8">
            <Button asChild variant="outline">
              <Link href="/success-stories">
                Read More Stories
                <ArrowRight className="h-4 w-4 ml-2" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Pricing Preview */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">{tPricing('section_title')}</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            {tPricing('section_subtitle')}
          </p>
        </div>
        <div className="grid md:grid-cols-4 gap-6 max-w-5xl mx-auto">
          {pricingTiers.map((tier) => (
            <Card
              key={tier.name}
              className={tier.popular ? "border-primary shadow-lg scale-105" : ""}
            >
              <CardHeader>
                {tier.popular && (
                  <Badge className="w-fit mb-2">Most Popular</Badge>
                )}
                <CardTitle>{tier.name}</CardTitle>
                <p className="text-3xl font-bold">
                  {tier.price}
                  {tier.price !== "Custom" && <span className="text-sm font-normal">/mo</span>}
                </p>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="text-center mt-8">
          <Button asChild size="lg">
            <Link href="/pricing">View Full Pricing</Link>
          </Button>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-primary text-primary-foreground py-16">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            {t('cta.title')}
          </h2>
          <p className="text-lg text-primary-foreground/80 max-w-2xl mx-auto mb-8">
            {t('cta.subtitle')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild size="lg" variant="secondary" className="text-lg px-8">
              <Link href="/auth/signup">
                {t('cta.button')}
                <ArrowRight className="h-5 w-5 ml-2" />
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
