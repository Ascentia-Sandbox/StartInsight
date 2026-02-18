"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  ArrowLeft, Clock, Eye, Calendar, Share2, Twitter, Linkedin,
  Copy, CheckCircle2, BookOpen, TrendingUp, ChevronUp, BarChart3,
  Megaphone, ArrowRight, Hash, Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
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
  created_at: string;
}

// Category config matching the listing page
const categoryConfig: Record<string, { icon: typeof TrendingUp; gradient: string; accent: string; bg: string }> = {
  Trends: {
    icon: TrendingUp,
    gradient: "from-blue-600 via-cyan-500 to-blue-700",
    accent: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  },
  Analysis: {
    icon: BarChart3,
    gradient: "from-violet-600 via-purple-500 to-violet-700",
    accent: "text-violet-600 dark:text-violet-400",
    bg: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
  },
  Guides: {
    icon: BookOpen,
    gradient: "from-emerald-600 via-green-500 to-emerald-700",
    accent: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  },
  "Case Studies": {
    icon: BarChart3,
    gradient: "from-rose-600 via-pink-500 to-rose-700",
    accent: "text-rose-600 dark:text-rose-400",
    bg: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  },
  Announcements: {
    icon: Megaphone,
    gradient: "from-amber-600 via-orange-500 to-amber-700",
    accent: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  },
};

const defaultCategoryConfig = {
  icon: TrendingUp,
  gradient: "from-primary via-primary/80 to-primary",
  accent: "text-primary",
  bg: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300",
};

function getCatConfig(category: string) {
  return categoryConfig[category] || defaultCategoryConfig;
}

export default function MarketInsightDetailPage() {
  const params = useParams();
  const [article, setArticle] = useState<MarketInsight | null>(null);
  const [recentArticles, setRecentArticles] = useState<MarketInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [readProgress, setReadProgress] = useState(0);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [toc, setToc] = useState<Array<{ id: string; text: string; level: number }>>([]);
  const [activeSection, setActiveSection] = useState<string>("");
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (params.slug) {
      fetchArticle(params.slug as string);
      fetchRecentArticles();
    }
  }, [params.slug]);

  // Reading progress, scroll-to-top, and active section tracking
  const handleScroll = useCallback(() => {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    setReadProgress(docHeight > 0 ? Math.min((scrollTop / docHeight) * 100, 100) : 0);
    setShowScrollTop(scrollTop > 500);

    // Active section tracking for TOC
    if (toc.length > 0) {
      let current = "";
      for (const item of toc) {
        const el = document.getElementById(item.id);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= 100) current = item.id;
        }
      }
      setActiveSection(current);
    }
  }, [toc]);

  useEffect(() => {
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  // Extract TOC from content
  useEffect(() => {
    if (!article?.content) return;
    const headings: Array<{ id: string; text: string; level: number }> = [];
    const lines = article.content.split("\n");
    for (const line of lines) {
      const match = line.match(/^(#{2,3})\s+(.+)/);
      if (match) {
        const level = match[1].length;
        const text = match[2].replace(/\*\*/g, "").trim();
        const id = text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
        headings.push({ id, text, level });
      }
    }
    setToc(headings);
  }, [article?.content]);

  const fetchArticle = async (slug: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${config.apiUrl}/api/market-insights/${slug}`
      );
      if (!response.ok) throw new Error("Article not found");
      const data = await response.json();
      setArticle(data);
    } catch (err) {
      console.error("Failed to fetch article:", err);
      setError("Failed to load article");
    } finally {
      setLoading(false);
    }
  };

  const fetchRecentArticles = async () => {
    try {
      const response = await fetch(
        `${config.apiUrl}/api/market-insights/recent?limit=4`
      );
      const data = await response.json();
      setRecentArticles(data);
    } catch (err) {
      console.error("Failed to fetch recent articles:", err);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const copyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const shareOnTwitter = () => {
    if (!article) return;
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(article.title);
    window.open(`https://twitter.com/intent/tweet?url=${url}&text=${text}`, "_blank");
  };

  const shareOnLinkedIn = () => {
    const url = encodeURIComponent(window.location.href);
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, "_blank");
  };

  const scrollToTop = () => window.scrollTo({ top: 0, behavior: "smooth" });

  // --- Loading State ---
  if (loading) {
    return (
      <div className="min-h-screen">
        <div className="h-[360px] bg-gradient-to-b from-muted/60 to-background animate-pulse" />
        <div className="container mx-auto px-4 -mt-16 max-w-4xl relative z-10">
          <div className="bg-background rounded-2xl border shadow-sm p-8 space-y-4">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-4/5" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-3/4" />
            <div className="flex items-center gap-4 pt-4">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
            </div>
          </div>
          <div className="mt-10 space-y-4">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-32 w-full rounded-lg" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-5/6" />
          </div>
        </div>
      </div>
    );
  }

  // --- Error State ---
  if (error || !article) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-sm">
          <div className="mx-auto mb-6 h-20 w-20 rounded-2xl bg-muted flex items-center justify-center">
            <BookOpen className="h-10 w-10 text-muted-foreground/40" />
          </div>
          <h1 className="text-2xl font-bold mb-2">Article Not Found</h1>
          <p className="text-muted-foreground mb-8">
            {error || "This article could not be found or may have been removed."}
          </p>
          <Button asChild>
            <Link href="/market-insights">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Articles
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const catConfig = getCatConfig(article.category);
  const CatIcon = catConfig.icon;
  const relatedArticles = recentArticles.filter((a) => a.slug !== article.slug).slice(0, 3);

  return (
    <>
      {/* Reading Progress Bar */}
      <div className="fixed top-0 left-0 right-0 z-50 h-0.5">
        <div
          className={`h-full bg-gradient-to-r ${catConfig.gradient} transition-all duration-150 ease-out`}
          style={{ width: `${readProgress}%` }}
        />
      </div>

      <div className="min-h-screen bg-background">
        <article>
          {/* Category Gradient Hero Header */}
          <div className={`relative bg-gradient-to-br ${catConfig.gradient} overflow-hidden`}>
            {/* Decorative pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-10 left-10 h-64 w-64 rounded-full bg-white/20 blur-3xl" />
              <div className="absolute bottom-0 right-20 h-48 w-48 rounded-full bg-white/15 blur-2xl" />
              <div className="absolute top-1/2 left-1/3 h-32 w-32 rounded-full bg-white/10 blur-xl" />
            </div>

            <div className="relative container mx-auto px-4 pt-8 pb-24 max-w-4xl">
              {/* Breadcrumb */}
              <nav className="flex items-center gap-2 text-sm text-white/70 mb-8">
                <Link href="/market-insights" className="hover:text-white transition-colors flex items-center gap-1.5">
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Market Insights
                </Link>
                <span>/</span>
                <span className="text-white/90">{article.category}</span>
              </nav>

              {/* Badges */}
              <div className="flex flex-wrap items-center gap-2 mb-5">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 backdrop-blur-sm text-white text-sm font-medium">
                  <CatIcon className="h-3.5 w-3.5" />
                  {article.category}
                </span>
                {article.is_featured && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-yellow-400/25 backdrop-blur-sm text-yellow-100 text-sm font-medium">
                    <TrendingUp className="h-3.5 w-3.5" />
                    Featured
                  </span>
                )}
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-sm text-white/90 text-xs font-medium border border-white/20">
                  <Sparkles className="h-3 w-3" />
                  AI-generated, human-reviewed
                </span>
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-white/15 backdrop-blur-sm text-white/80 text-xs">
                  <Clock className="h-3 w-3" />
                  {article.reading_time_minutes} min read
                </span>
              </div>

              {/* Title - large serif */}
              <h1 className="text-3xl sm:text-4xl md:text-5xl md:leading-[1.1] text-white tracking-tight mb-4 max-w-3xl">
                {article.title}
              </h1>

              {/* Summary */}
              <p className="text-lg md:text-xl text-white/80 leading-relaxed max-w-2xl">
                {article.summary}
              </p>
            </div>
          </div>

          {/* Floating Meta Card (simplified) */}
          <div className="container mx-auto px-4 max-w-4xl -mt-8 relative z-10 mb-10">
            <div className="bg-background rounded-xl border-l-4 border shadow-sm p-5 md:p-6" style={{ borderLeftColor: 'hsl(var(--primary))' }}>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                {/* Author + Meta */}
                <div className="flex items-center gap-3">
                  <Avatar className="h-11 w-11 ring-2 ring-background shadow-md">
                    <AvatarImage src={article.author_avatar_url || undefined} />
                    <AvatarFallback className={`bg-gradient-to-br ${catConfig.gradient} text-white text-sm font-semibold`}>
                      {article.author_name.split(" ").map((n) => n[0]).join("")}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-semibold text-sm">{article.author_name}</p>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDate(article.published_at)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {article.reading_time_minutes} min read
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="h-3 w-3" />
                        {article.view_count.toLocaleString()} views
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Content + Sidebar */}
          <div className="container mx-auto px-4 pb-16 max-w-5xl">
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_220px] gap-12">
              {/* Main Content */}
              <div className="min-w-0" ref={contentRef}>
                <div className="prose dark:prose-invert max-w-none
                  prose-headings:scroll-mt-24
                  prose-h2:text-2xl prose-h2:mt-12 prose-h2:mb-6 prose-h2:pb-4 prose-h2:border-b prose-h2:border-border/30 prose-h2:font-normal
                  prose-h3:text-xl prose-h3:mt-10 prose-h3:mb-4 prose-h3:font-semibold
                  prose-h4:text-lg prose-h4:mt-8 prose-h4:mb-3 prose-h4:font-semibold
                  prose-p:text-[17px] prose-p:text-foreground/90 prose-p:leading-[1.8] prose-p:mb-6
                  prose-li:text-[17px] prose-li:text-foreground/90 prose-li:leading-[1.75] prose-li:my-2
                  prose-ul:my-6 prose-ol:my-6
                  prose-strong:text-foreground prose-strong:font-semibold
                  prose-blockquote:border-l-4 prose-blockquote:border-l-primary/40 prose-blockquote:bg-primary/[0.02] prose-blockquote:py-4 prose-blockquote:px-6 prose-blockquote:rounded-r-xl prose-blockquote:not-italic prose-blockquote:my-8 prose-blockquote:text-foreground/80
                  prose-table:border-collapse prose-table:rounded-xl prose-table:overflow-hidden prose-table:my-8 prose-table:w-full
                  prose-thead:bg-muted/80
                  prose-th:p-3 prose-th:text-left prose-th:font-semibold prose-th:text-sm prose-th:border prose-th:border-border/50 prose-th:bg-muted/60
                  prose-td:p-3 prose-td:border prose-td:border-border/40 prose-td:text-[15px]
                  prose-tr:even:bg-muted/20
                  prose-a:text-primary prose-a:font-medium prose-a:no-underline hover:prose-a:underline prose-a:decoration-primary/30
                  prose-code:bg-muted prose-code:px-2 prose-code:py-0.5 prose-code:rounded-md prose-code:text-sm prose-code:font-medium prose-code:before:content-none prose-code:after:content-none
                  prose-img:rounded-xl prose-img:shadow-lg prose-img:my-8
                  prose-hr:border-border/20 prose-hr:my-12">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h2: ({ children, ...props }) => {
                        const text = String(children).replace(/\*\*/g, "");
                        const id = text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
                        return <h2 id={id} {...props}>{children}</h2>;
                      },
                      h3: ({ children, ...props }) => {
                        const text = String(children).replace(/\*\*/g, "");
                        const id = text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
                        return <h3 id={id} {...props}>{children}</h3>;
                      },
                      table: ({ children, ...props }) => (
                        <div className="overflow-x-auto my-8 rounded-lg border border-border/50">
                          <table className="w-full" {...props}>{children}</table>
                        </div>
                      ),
                    }}
                  >
                    {article.content}
                  </ReactMarkdown>
                </div>

                {/* Tags / Category Section */}
                <div className="mt-14 pt-8 border-t">
                  <div className="flex flex-wrap items-center gap-2">
                    <Hash className="h-4 w-4 text-muted-foreground" />
                    <Badge variant="secondary" className="font-normal">{article.category}</Badge>
                    <Badge variant="secondary" className="font-normal">Market Research</Badge>
                    <Badge variant="secondary" className="font-normal">Startup Trends</Badge>
                  </div>
                </div>

                {/* Author Bio Card */}
                <div className="mt-8 p-6 rounded-xl border bg-gradient-to-r from-muted/30 to-muted/10">
                  <div className="flex items-start gap-4">
                    <Avatar className="h-14 w-14 ring-2 ring-background shadow-sm">
                      <AvatarImage src={article.author_avatar_url || undefined} />
                      <AvatarFallback className={`bg-gradient-to-br ${catConfig.gradient} text-white font-semibold`}>
                        {article.author_name.split(" ").map((n) => n[0]).join("")}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-1">Written by</p>
                      <p className="font-semibold text-lg">{article.author_name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-xs gap-1">
                          <Sparkles className="h-3 w-3" />
                          AI-generated, human-reviewed
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                        Bringing you data-driven market analysis to help founders spot the next big opportunity.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Share Bar (bottom) */}
                <div className="mt-8 flex items-center justify-between p-4 rounded-xl border bg-muted/20">
                  <p className="text-sm font-medium text-muted-foreground">Found this useful? Share it with your network</p>
                  <div className="flex items-center gap-1.5">
                    <Button variant="outline" size="sm" className="gap-1.5 h-8" onClick={shareOnTwitter}>
                      <Twitter className="h-3.5 w-3.5" /> Post
                    </Button>
                    <Button variant="outline" size="sm" className="gap-1.5 h-8" onClick={shareOnLinkedIn}>
                      <Linkedin className="h-3.5 w-3.5" /> Share
                    </Button>
                    <Button variant="outline" size="sm" className="gap-1.5 h-8" onClick={copyLink}>
                      {copied ? <CheckCircle2 className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                      {copied ? "Copied" : "Link"}
                    </Button>
                  </div>
                </div>
              </div>

              {/* Sidebar */}
              <aside className="hidden lg:block">
                <div className="sticky top-20 space-y-6">
                  {/* Table of Contents */}
                  {toc.length > 2 && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
                        <BookOpen className="h-3.5 w-3.5" />
                        On this page
                      </p>
                      <nav className="space-y-0.5">
                        {toc.map((item) => (
                          <a
                            key={item.id}
                            href={`#${item.id}`}
                            className={`block text-[13px] py-1 transition-colors border-l-2 ${
                              item.level === 3 ? "pl-5" : "pl-3"
                            } ${
                              activeSection === item.id
                                ? `border-l-primary font-semibold text-foreground`
                                : "border-l-transparent text-muted-foreground hover:text-foreground hover:border-l-muted-foreground/40"
                            }`}
                          >
                            {item.text}
                          </a>
                        ))}
                      </nav>
                    </div>
                  )}

                  {/* Reading Progress */}
                  <div className="pt-4 border-t border-border/40">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-medium text-muted-foreground">
                        Progress
                      </p>
                      <span className="text-xs text-muted-foreground font-medium tabular-nums">
                        {Math.round(readProgress)}%
                      </span>
                    </div>
                    <div className="h-0.5 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full bg-gradient-to-r ${catConfig.gradient} rounded-full transition-all duration-300`}
                        style={{ width: `${readProgress}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1.5">
                      {Math.max(0, Math.ceil(article.reading_time_minutes * (1 - readProgress / 100)))} min left
                    </p>
                  </div>

                  {/* Quick Share */}
                  <div className="pt-4 border-t border-border/40">
                    <p className="text-xs font-medium text-muted-foreground mb-3 flex items-center gap-1.5">
                      <Share2 className="h-3 w-3" />
                      Share
                    </p>
                    <div className="flex gap-1.5">
                      <Button variant="outline" size="icon" className="h-8 w-8 rounded-lg" onClick={shareOnTwitter}>
                        <Twitter className="h-3.5 w-3.5" />
                      </Button>
                      <Button variant="outline" size="icon" className="h-8 w-8 rounded-lg" onClick={shareOnLinkedIn}>
                        <Linkedin className="h-3.5 w-3.5" />
                      </Button>
                      <Button variant="outline" size="icon" className="h-8 w-8 rounded-lg" onClick={copyLink}>
                        {copied ? <CheckCircle2 className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                      </Button>
                    </div>
                  </div>
                </div>
              </aside>
            </div>
          </div>

          {/* Related Articles */}
          {relatedArticles.length > 0 && (
            <div className="border-t bg-muted/10">
              <div className="container mx-auto px-4 py-14 max-w-6xl">
                <div className="flex items-center justify-between mb-8">
                  <div>
                    <h2 className="text-2xl font-bold">Continue Reading</h2>
                    <p className="text-sm text-muted-foreground mt-1">More market intelligence for founders</p>
                  </div>
                  <Button asChild variant="ghost" className="gap-1.5 text-muted-foreground">
                    <Link href="/market-insights">
                      All articles <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </div>
                <div className="grid md:grid-cols-3 gap-6">
                  {relatedArticles.map((recent) => {
                    const rConfig = getCatConfig(recent.category);
                    const RIcon = rConfig.icon;
                    return (
                      <Link key={recent.id} href={`/market-insights/${recent.slug}`}>
                        <Card className="h-full overflow-hidden hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group">
                          {/* Category gradient header strip */}
                          <div className={`bg-gradient-to-r ${rConfig.gradient} p-4 flex items-center justify-between`}>
                            <Badge variant="secondary" className="bg-white/20 text-white border-0 backdrop-blur-sm text-xs">
                              {recent.category}
                            </Badge>
                            <div className="p-1.5 rounded-lg bg-white/20 backdrop-blur-sm text-white">
                              <RIcon className="h-3.5 w-3.5" />
                            </div>
                          </div>
                          <CardContent className="p-5">
                            <h3 className="font-semibold text-base leading-snug line-clamp-2 group-hover:text-primary transition-colors mb-2">
                              {recent.title}
                            </h3>
                            <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                              {recent.summary}
                            </p>
                            <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t">
                              <div className="flex items-center gap-3">
                                <span>{recent.author_name}</span>
                                <span className="flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {recent.reading_time_minutes} min
                                </span>
                              </div>
                              <span className="text-primary opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 font-medium">
                                Read <ArrowRight className="h-3 w-3" />
                              </span>
                            </div>
                          </CardContent>
                        </Card>
                      </Link>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* CTA Section */}
          <div className="border-t">
            <div className="container mx-auto px-4 py-20 max-w-3xl text-center">
              <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r ${catConfig.gradient} text-white text-sm font-medium mb-5`}>
                <TrendingUp className="h-4 w-4" />
                Turn insights into action
              </div>
              <h2 className="text-3xl md:text-4xl font-bold mb-4 tracking-tight">
                Discover Startup Ideas Based on These Trends
              </h2>
              <p className="text-lg text-muted-foreground mb-8 max-w-lg mx-auto leading-relaxed">
                Our AI analyzes market signals and generates validated business opportunities you can start building today.
              </p>
              <div className="flex items-center justify-center gap-3">
                <Button asChild size="lg" className="px-8">
                  <Link href="/auth/signup">Start Free Trial</Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="px-8">
                  <Link href="/insights">Browse Ideas</Link>
                </Button>
              </div>
            </div>
          </div>
        </article>

        {/* Scroll to Top */}
        <button
          onClick={scrollToTop}
          className={`fixed bottom-6 right-6 z-40 h-10 w-10 rounded-full bg-foreground text-background shadow-lg flex items-center justify-center hover:scale-110 transition-all duration-200 ${
            showScrollTop ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4 pointer-events-none"
          }`}
          aria-label="Scroll to top"
        >
          <ChevronUp className="h-5 w-5" />
        </button>
      </div>
    </>
  );
}
