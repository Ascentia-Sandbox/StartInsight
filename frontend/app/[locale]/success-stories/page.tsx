"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Trophy, TrendingUp, Users, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { config } from "@/lib/env";

interface SuccessStory {
  id: string;
  founder_name: string;
  company_name: string;
  tagline: string;
  idea_summary: string;
  journey_narrative: string;
  metrics: {
    mrr?: number;
    users?: number;
    funding?: string;
    growth?: string;
  };
  timeline: Array<{
    date: string;
    milestone: string;
  }>;
  avatar_url: string | null;
  company_logo_url: string | null;
  is_featured: boolean;
}

interface StoriesResponse {
  stories: SuccessStory[];
  total: number;
  limit: number;
  offset: number;
}

export default function SuccessStoriesPage() {
  const [stories, setStories] = useState<SuccessStory[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const limit = 10;

  useEffect(() => {
    fetchStories();
  }, [page]);

  const fetchStories = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("limit", limit.toString());
      params.append("offset", (page * limit).toString());

      const response = await fetch(
        `${config.apiUrl}/api/success-stories?${params}`
      );
      const data: StoriesResponse = await response.json();
      setStories(data.stories);
      setTotal(data.total);
    } catch (error) {
      console.error("Failed to fetch stories:", error);
      setStories([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const formatMRR = (mrr: number) => {
    if (mrr >= 1000000) return `$${(mrr / 1000000).toFixed(1)}M`;
    if (mrr >= 1000) return `$${(mrr / 1000).toFixed(0)}K`;
    return `$${mrr}`;
  };

  const formatUsers = (users: number) => {
    if (users >= 1000000) return `${(users / 1000000).toFixed(1)}M`;
    if (users >= 1000) return `${(users / 1000).toFixed(0)}K`;
    return users.toString();
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {stories.length > 0 && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "CollectionPage",
              name: "Startup Success Stories",
              url: "https://startinsight.app/success-stories",
              mainEntity: {
                "@type": "ItemList",
                itemListElement: stories.map((s, i) => ({
                  "@type": "ListItem",
                  position: i + 1,
                  item: {
                    "@type": "Article",
                    headline: s.title,
                    url: `https://startinsight.app/success-stories/${s.id}`,
                  },
                })),
              },
            }),
          }}
        />
      )}
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Badge variant="secondary" className="mb-4">Success Stories</Badge>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Real Founders, Real Results
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Discover how founders used StartInsight to find and validate their million-dollar startup ideas.
        </p>
      </section>

      {/* Stats */}
      <section className="container mx-auto px-4 pb-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
          <Card className="text-center">
            <CardContent className="pt-6">
              <Trophy className="h-8 w-8 text-primary mx-auto mb-2" />
              <div className="text-2xl font-bold">12</div>
              <p className="text-sm text-muted-foreground">Curated Stories</p>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="pt-6">
              <DollarSign className="h-8 w-8 text-green-500 mx-auto mb-2" />
              <div className="text-2xl font-bold">$2.4M</div>
              <p className="text-sm text-muted-foreground">Ideas Validated</p>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="pt-6">
              <Users className="h-8 w-8 text-blue-500 mx-auto mb-2" />
              <div className="text-2xl font-bold">1,000+</div>
              <p className="text-sm text-muted-foreground">Founders Joined</p>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="pt-6">
              <TrendingUp className="h-8 w-8 text-purple-500 mx-auto mb-2" />
              <div className="text-2xl font-bold">8</div>
              <p className="text-sm text-muted-foreground">Scoring Dimensions</p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Stories Grid */}
      <section className="container mx-auto px-4 pb-16">
        {loading ? (
          <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
            {[...Array(4)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="flex items-center gap-4">
                    <Skeleton className="h-16 w-16 rounded-full" />
                    <div>
                      <Skeleton className="h-6 w-32" />
                      <Skeleton className="h-4 w-24 mt-2" />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-24 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : stories.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Trophy className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Success stories coming soon</h3>
            <p className="text-muted-foreground max-w-md mb-6">
              We&apos;re curating inspiring founder journeys and startup success stories from around the world.
            </p>
            <Button asChild variant="outline">
              <Link href="/insights">Browse Startup Insights</Link>
            </Button>
          </div>
        ) : (
          <>
            <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
              {stories.map((story) => (
                <Card key={story.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader className="pb-2">
                    <div className="flex items-start gap-4">
                      <Avatar className="h-16 w-16">
                        <AvatarImage src={story.avatar_url || undefined} alt={story.founder_name} />
                        <AvatarFallback className="text-lg">
                          {story.founder_name.split(" ").map(n => n[0]).join("")}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-lg">{story.founder_name}</CardTitle>
                          {story.is_featured && (
                            <Badge variant="secondary" className="text-xs">Featured</Badge>
                          )}
                        </div>
                        <CardDescription className="flex items-center gap-2">
                          {story.company_logo_url && (
                            <img
                              src={story.company_logo_url}
                              alt={story.company_name}
                              className="h-5 w-5 rounded object-cover"
                            />
                          )}
                          {story.company_name}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm font-medium mb-2">{story.tagline}</p>
                    <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
                      {story.idea_summary}
                    </p>

                    {/* Metrics */}
                    <div className="flex gap-4 mb-4">
                      {story.metrics.mrr && (
                        <div className="text-center">
                          <div className="text-lg font-bold text-green-600">
                            {formatMRR(story.metrics.mrr)}
                          </div>
                          <span className="text-xs text-muted-foreground">MRR</span>
                        </div>
                      )}
                      {story.metrics.users && (
                        <div className="text-center">
                          <div className="text-lg font-bold text-blue-600">
                            {formatUsers(story.metrics.users)}
                          </div>
                          <span className="text-xs text-muted-foreground">Users</span>
                        </div>
                      )}
                      {story.metrics.funding && (
                        <div className="text-center">
                          <div className="text-lg font-bold text-purple-600">
                            {story.metrics.funding}
                          </div>
                          <span className="text-xs text-muted-foreground">Funding</span>
                        </div>
                      )}
                    </div>

                    <Button asChild className="w-full">
                      <Link href={`/success-stories/${story.id}`}>Read Full Story</Link>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center gap-2 mt-8">
                <Button
                  variant="outline"
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                >
                  Previous
                </Button>
                <span className="flex items-center px-4 text-sm text-muted-foreground">
                  Page {page + 1} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Card className="max-w-2xl mx-auto bg-primary text-primary-foreground">
          <CardContent className="pt-8 pb-8">
            <h2 className="text-2xl font-bold mb-2">Ready to Start Your Journey?</h2>
            <p className="mb-6 text-primary-foreground/80">
              Join thousands of founders who discovered their successful startup ideas with us.
            </p>
            <Button asChild size="lg" variant="secondary">
              <Link href="/auth/signup">Start Your Story</Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
