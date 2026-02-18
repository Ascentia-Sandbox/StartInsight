"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { TrendingUp, BarChart3, BookOpen, Megaphone, Clock, Eye, ArrowRight, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { config } from "@/lib/env";

interface MarketInsight {
  id: string;
  title: string;
  slug: string;
  summary: string;
  content: string;
  category: string;
  author_name: string;
  author_avatar_url: string | null;
  cover_image_url: string | null;
  reading_time_minutes: number;
  view_count: number;
  is_featured: boolean;
  published_at: string | null;
}

interface InsightsResponse {
  articles: MarketInsight[];
  total: number;
  limit: number;
  offset: number;
}

const categories = ["All", "Trends", "Analysis", "Guides", "Announcements"];

const categoryConfig: Record<string, { icon: typeof TrendingUp; gradient: string; accent: string }> = {
  Trends: { icon: TrendingUp, gradient: "from-blue-500/15 via-cyan-500/10 to-blue-600/5", accent: "text-blue-600 dark:text-blue-400" },
  Analysis: { icon: BarChart3, gradient: "from-violet-500/15 via-purple-500/10 to-violet-600/5", accent: "text-violet-600 dark:text-violet-400" },
  Guides: { icon: BookOpen, gradient: "from-emerald-500/15 via-green-500/10 to-emerald-600/5", accent: "text-emerald-600 dark:text-emerald-400" },
  Announcements: { icon: Megaphone, gradient: "from-amber-500/15 via-orange-500/10 to-amber-600/5", accent: "text-amber-600 dark:text-amber-400" },
  "Case Studies": { icon: BarChart3, gradient: "from-rose-500/15 via-pink-500/10 to-rose-600/5", accent: "text-rose-600 dark:text-rose-400" },
};

const defaultCategoryConfig = { icon: TrendingUp, gradient: "from-primary/15 via-primary/10 to-primary/5", accent: "text-primary" };

function getCategoryConfig(category: string) {
  return categoryConfig[category] || defaultCategoryConfig;
}

function formatDate(dateString: string | null) {
  if (!dateString) return "";
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function FeaturedArticle({ article }: { article: MarketInsight }) {
  const config = getCategoryConfig(article.category);
  const Icon = config.icon;

  return (
    <Link href={`/market-insights/${article.slug}`} className="block group">
      <Card className="overflow-hidden border-2 border-primary/20 hover:border-primary/40 transition-all duration-300 hover:shadow-xl">
        <div className={`bg-gradient-to-br ${config.gradient} p-8 md:p-12`}>
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-2">
              <Badge className="bg-primary text-primary-foreground">Featured</Badge>
              <Badge variant="outline">{article.category}</Badge>
            </div>
            <div className={`p-3 rounded-xl bg-background/60 backdrop-blur-sm ${config.accent}`}>
              <Icon className="h-6 w-6" />
            </div>
          </div>
          <h2 className="text-2xl md:text-3xl font-bold mb-3 group-hover:text-primary transition-colors line-clamp-2">
            {article.title}
          </h2>
          <p className="text-muted-foreground text-lg mb-6 line-clamp-2">{article.summary}</p>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>{article.author_name}</span>
              <span>{formatDate(article.published_at)}</span>
              <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{article.reading_time_minutes} min</span>
              <span className="flex items-center gap-1"><Eye className="h-3.5 w-3.5" />{article.view_count}</span>
            </div>
            <span className="flex items-center gap-1 text-sm font-medium text-primary group-hover:gap-2 transition-all">
              Read article <ArrowRight className="h-4 w-4" />
            </span>
          </div>
        </div>
      </Card>
    </Link>
  );
}

function ArticleCard({ article }: { article: MarketInsight }) {
  const config = getCategoryConfig(article.category);
  const Icon = config.icon;

  return (
    <Link href={`/market-insights/${article.slug}`} className="block group h-full">
      <Card className="h-full overflow-hidden hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
        <div className={`bg-gradient-to-br ${config.gradient} p-5 flex items-center justify-between`}>
          <Badge variant="outline" className="bg-background/60 backdrop-blur-sm">
            {article.category}
          </Badge>
          <div className={`p-2 rounded-lg bg-background/60 backdrop-blur-sm ${config.accent}`}>
            <Icon className="h-4 w-4" />
          </div>
        </div>
        <CardContent className="p-5 flex flex-col flex-1">
          <h3 className="font-semibold text-lg mb-2 group-hover:text-primary transition-colors line-clamp-2">
            {article.title}
          </h3>
          <p className="text-sm text-muted-foreground mb-4 line-clamp-3 flex-1">{article.summary}</p>
          <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t">
            <div className="flex items-center gap-3">
              <span>{formatDate(article.published_at)}</span>
              <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{article.reading_time_minutes} min</span>
            </div>
            <span className="flex items-center gap-1"><Eye className="h-3 w-3" />{article.view_count}</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

export default function MarketInsightsPage() {
  const [articles, setArticles] = useState<MarketInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("All");
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const limit = 12;

  useEffect(() => {
    fetchArticles();
  }, [category, page]);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (category !== "All") params.append("category", category);
      params.append("limit", limit.toString());
      params.append("offset", (page * limit).toString());

      const response = await fetch(
        `${config.apiUrl}/api/market-insights?${params}`
      );
      const data: InsightsResponse = await response.json();
      setArticles(data.articles);
      setTotal(data.total);
    } catch (error) {
      console.error("Failed to fetch articles:", error);
      setArticles([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(total / limit);
  const featured = articles.find(a => a.is_featured);
  const rest = featured ? articles.filter(a => a.id !== featured.id) : articles;

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {articles.length > 0 && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "CollectionPage",
              name: "Market Insights & Analysis",
              url: "https://startinsight.app/market-insights",
              mainEntity: {
                "@type": "ItemList",
                itemListElement: articles.slice(0, 10).map((a, i) => ({
                  "@type": "ListItem",
                  position: i + 1,
                  item: {
                    "@type": "Article",
                    headline: a.title,
                    description: a.summary,
                    url: `https://startinsight.app/market-insights/${a.slug}`,
                  },
                })),
              },
            }),
          }}
        />
      )}
      {/* Hero Section */}
      <section className="container mx-auto px-4 pt-16 pb-10 text-center">
        <Badge variant="secondary" className="mb-4">Market Intelligence</Badge>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Startup Trends & Market Analysis
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Data-driven insights on emerging markets, growth opportunities, and strategic moves for founders.
        </p>
      </section>

      {/* Category Filter */}
      <section className="container mx-auto px-4 pb-8">
        <Tabs
          value={category}
          onValueChange={(value) => { setCategory(value); setPage(0); }}
          className="max-w-2xl mx-auto"
        >
          <TabsList className="grid w-full grid-cols-5">
            {categories.map((cat) => (
              <TabsTrigger key={cat} value={cat}>{cat}</TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </section>

      {/* Articles */}
      <section className="container mx-auto px-4 pb-16 max-w-6xl">
        {loading ? (
          <div className="space-y-6">
            <Skeleton className="h-64 w-full rounded-lg" />
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <Card key={i}>
                  <Skeleton className="h-16 w-full" />
                  <div className="p-5 space-y-3">
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-2/3" />
                  </div>
                </Card>
              ))}
            </div>
          </div>
        ) : articles.length === 0 ? (
          category !== "All" ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <BookOpen className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No articles found</h3>
              <p className="text-muted-foreground max-w-md mb-4">
                No articles found in &ldquo;{category}&rdquo;. Try viewing all categories.
              </p>
              <Button variant="outline" onClick={() => setCategory("All")}>View All Articles</Button>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Market insights are being generated</h3>
              <p className="text-muted-foreground max-w-md mb-6">
                Our AI publishes in-depth market analysis articles covering emerging sectors and opportunities.
              </p>
              <Button asChild variant="outline">
                <Link href="/features">Explore Features</Link>
              </Button>
            </div>
          )
        ) : (
          <div className="space-y-8">
            {/* Featured article (first page only) */}
            {featured && page === 0 && <FeaturedArticle article={featured} />}

            {/* Article grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {rest.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 pt-4">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                {Array.from({ length: totalPages }, (_, i) => (
                  <Button
                    key={i}
                    variant={page === i ? "default" : "outline"}
                    size="icon"
                    onClick={() => setPage(i)}
                    className="w-10 h-10"
                  >
                    {i + 1}
                  </Button>
                ))}
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Newsletter CTA */}
      <section className="container mx-auto px-4 pb-16">
        <Card className="max-w-3xl mx-auto bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5 border-primary/20">
          <CardContent className="py-10 text-center">
            <h2 className="text-2xl font-bold mb-2">Turn Insights Into Action</h2>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              Discover validated startup ideas backed by market data. Join founders who build smarter.
            </p>
            <Button asChild size="lg">
              <Link href="/auth/signup">Get Started Free</Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
