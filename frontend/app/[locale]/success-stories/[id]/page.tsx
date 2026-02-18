"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, TrendingUp, Users, DollarSign, Calendar, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
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
  created_at: string;
}

export default function SuccessStoryDetailPage() {
  const params = useParams();
  const [story, setStory] = useState<SuccessStory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (params.id) {
      fetchStory(params.id as string);
    }
  }, [params.id]);

  const fetchStory = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${config.apiUrl}/api/success-stories/${id}`
      );
      if (!response.ok) {
        throw new Error("Story not found");
      }
      const data = await response.json();
      setStory(data);
    } catch (error) {
      console.error("Failed to fetch story:", error);
      setError("Failed to load success story");
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <Skeleton className="h-8 w-32 mb-8" />
          <div className="flex items-center gap-6 mb-8">
            <Skeleton className="h-24 w-24 rounded-full" />
            <div>
              <Skeleton className="h-8 w-48 mb-2" />
              <Skeleton className="h-6 w-32" />
            </div>
          </div>
          <Skeleton className="h-48 w-full mb-8" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (error || !story) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
        <div className="container mx-auto px-4 py-16 text-center">
          <h1 className="text-2xl font-bold mb-4">Story Not Found</h1>
          <p className="text-muted-foreground mb-6">{error || "This success story could not be found."}</p>
          <Button asChild>
            <Link href="/success-stories">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Stories
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Back Button */}
        <Button variant="ghost" asChild className="mb-8">
          <Link href="/success-stories">
            <ArrowLeft className="h-4 w-4 mr-2" />
            All Success Stories
          </Link>
        </Button>

        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center gap-6 mb-8">
          <Avatar className="h-24 w-24">
            <AvatarImage src={story.avatar_url || undefined} alt={story.founder_name} />
            <AvatarFallback className="text-2xl">
              {story.founder_name.split(" ").map(n => n[0]).join("")}
            </AvatarFallback>
          </Avatar>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <h1 className="text-3xl font-bold">{story.founder_name}</h1>
              {story.is_featured && <Badge>Featured</Badge>}
            </div>
            <div className="flex items-center gap-2 text-lg text-muted-foreground">
              {story.company_logo_url && (
                <img
                  src={story.company_logo_url}
                  alt={story.company_name}
                  className="h-6 w-6 rounded object-cover"
                />
              )}
              <span className="font-medium">{story.company_name}</span>
            </div>
            <p className="text-muted-foreground mt-1">{story.tagline}</p>
          </div>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {story.metrics.mrr && (
            <Card>
              <CardContent className="pt-6 text-center">
                <DollarSign className="h-6 w-6 text-green-500 mx-auto mb-2" />
                <div className="text-2xl font-bold text-green-600">
                  {formatMRR(story.metrics.mrr)}
                </div>
                <p className="text-sm text-muted-foreground">Monthly Revenue</p>
              </CardContent>
            </Card>
          )}
          {story.metrics.users && (
            <Card>
              <CardContent className="pt-6 text-center">
                <Users className="h-6 w-6 text-blue-500 mx-auto mb-2" />
                <div className="text-2xl font-bold text-blue-600">
                  {formatUsers(story.metrics.users)}
                </div>
                <p className="text-sm text-muted-foreground">Active Users</p>
              </CardContent>
            </Card>
          )}
          {story.metrics.funding && (
            <Card>
              <CardContent className="pt-6 text-center">
                <TrendingUp className="h-6 w-6 text-purple-500 mx-auto mb-2" />
                <div className="text-2xl font-bold text-purple-600">
                  {story.metrics.funding}
                </div>
                <p className="text-sm text-muted-foreground">Total Funding</p>
              </CardContent>
            </Card>
          )}
          {story.metrics.growth && (
            <Card>
              <CardContent className="pt-6 text-center">
                <TrendingUp className="h-6 w-6 text-orange-500 mx-auto mb-2" />
                <div className="text-2xl font-bold text-orange-600">
                  {story.metrics.growth}
                </div>
                <p className="text-sm text-muted-foreground">MoM Growth</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Idea Summary */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>The Idea</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{story.idea_summary}</p>
          </CardContent>
        </Card>

        {/* Journey Narrative */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>The Journey</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              {story.journey_narrative.split("\n\n").map((paragraph, index) => (
                <p key={index} className="text-muted-foreground mb-4">
                  {paragraph}
                </p>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Timeline */}
        {story.timeline && story.timeline.length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Milestones</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {story.timeline.map((item, index) => (
                  <div key={index} className="relative">
                    <div className="flex items-start gap-4">
                      <div className="flex flex-col items-center">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground">
                          <CheckCircle2 className="h-4 w-4" />
                        </div>
                        {index < story.timeline.length - 1 && (
                          <div className="w-0.5 h-12 bg-border mt-2" />
                        )}
                      </div>
                      <div className="flex-1 pb-8">
                        <div className="flex items-center gap-2 mb-1">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">{item.date}</span>
                        </div>
                        <p className="font-medium">{item.milestone}</p>
                      </div>
                    </div>
                    {index < story.timeline.length - 1 && (
                      <Progress
                        value={100}
                        className="absolute left-4 top-8 w-0.5 h-12 -translate-x-1/2"
                      />
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* CTA */}
        <Card className="bg-primary text-primary-foreground">
          <CardContent className="pt-8 pb-8 text-center">
            <h2 className="text-2xl font-bold mb-2">Inspired by {story.founder_name}'s Story?</h2>
            <p className="mb-6 text-primary-foreground/80">
              Start your own journey and find your million-dollar startup idea.
            </p>
            <Button asChild size="lg" variant="secondary">
              <Link href="/auth/signup">Start Your Journey</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
