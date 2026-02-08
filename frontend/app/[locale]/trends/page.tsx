"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { TrendingUp, TrendingDown, Search, ArrowUpDown, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { config } from "@/lib/env";

interface Trend {
  id: string;
  keyword: string;
  category: string;
  search_volume: number;
  growth_percentage: number;
  business_implications: string;
  trend_data: Record<string, unknown> | null;
  source: string;
  is_featured: boolean;
}

interface TrendsResponse {
  trends: Trend[];
  total: number;
  limit: number;
  offset: number;
}

const sortOptions = [
  { value: "recent", label: "Most Recent" },
  { value: "volume", label: "Highest Volume" },
  { value: "growth", label: "Highest Growth" },
];

export default function TrendsPage() {
  const [trends, setTrends] = useState<Trend[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [sort, setSort] = useState("recent");
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const limit = 12;

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchTrends();
  }, [search, category, sort, page]);

  const fetchCategories = async () => {
    try {
      const response = await fetch(
        `${config.apiUrl}/api/trends/categories`
      );
      const data = await response.json();
      setCategories(data);
    } catch (error) {
      console.error("Failed to fetch categories:", error);
    }
  };

  const fetchTrends = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (category !== "All") params.append("category", category);
      params.append("sort", sort);
      params.append("limit", limit.toString());
      params.append("offset", (page * limit).toString());

      const response = await fetch(
        `${config.apiUrl}/api/trends?${params}`
      );
      const data: TrendsResponse = await response.json();
      setTrends(data.trends);
      setTotal(data.total);
    } catch (error) {
      console.error("Failed to fetch trends:", error);
      setTrends([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(0)}K`;
    return volume.toString();
  };

  const getGrowthBadge = (growth: number) => {
    if (growth >= 100) return { label: "Explosive", variant: "default" as const, color: "text-green-600" };
    if (growth >= 50) return { label: "Surging", variant: "default" as const, color: "text-green-500" };
    if (growth >= 20) return { label: "Growing", variant: "secondary" as const, color: "text-blue-500" };
    if (growth >= 0) return { label: "Stable", variant: "outline" as const, color: "text-gray-500" };
    if (growth >= -20) return { label: "Declining", variant: "outline" as const, color: "text-orange-500" };
    return { label: "Fading", variant: "destructive" as const, color: "text-red-500" };
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Badge variant="secondary" className="mb-4">Trends Database</Badge>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          180+ Trending Business Opportunities
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Real-time search volume and growth data to identify emerging markets and validate your ideas.
        </p>
      </section>

      {/* Filters */}
      <section className="container mx-auto px-4 pb-8">
        <div className="flex flex-col md:flex-row gap-4 max-w-4xl mx-auto">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search keywords..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
              className="pl-10"
            />
          </div>
          <Select
            value={category}
            onValueChange={(value) => {
              setCategory(value);
              setPage(0);
            }}
          >
            <SelectTrigger className="w-full md:w-[180px]">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All">All Categories</SelectItem>
              {categories.map((cat) => (
                <SelectItem key={cat} value={cat}>
                  {cat}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={sort}
            onValueChange={(value) => {
              setSort(value);
              setPage(0);
            }}
          >
            <SelectTrigger className="w-full md:w-[160px]">
              <ArrowUpDown className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              {sortOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </section>

      {/* Trends Table/Grid */}
      <section className="container mx-auto px-4 pb-16">
        {loading ? (
          <Card className="max-w-5xl mx-auto overflow-hidden">
            <div className="divide-y">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="flex items-center gap-4 px-6 py-3">
                  <Skeleton className="h-5 w-40" />
                  <Skeleton className="h-5 w-16 ml-auto" />
                  <Skeleton className="h-5 w-16" />
                  <Skeleton className="h-5 w-16" />
                  <Skeleton className="h-5 w-16" />
                </div>
              ))}
            </div>
          </Card>
        ) : trends.length === 0 ? (
          <div className="text-center py-16">
            <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground mb-4">
              {search || category !== "All"
                ? "No trends found matching your criteria."
                : "No trends available yet. Check back soon!"}
            </p>
            {(search || category !== "All") && (
              <Button
                variant="outline"
                onClick={() => {
                  setSearch("");
                  setCategory("All");
                }}
              >
                Clear Filters
              </Button>
            )}
          </div>
        ) : (
          <>
            <div className="text-sm text-muted-foreground text-center mb-6">
              Showing {trends.length} of {total} trends
            </div>
            <Card className="max-w-5xl mx-auto overflow-hidden">
              {/* Table Header */}
              <div className="hidden md:grid md:grid-cols-[2fr_1fr_1fr_1fr_auto] gap-4 px-6 py-3 bg-muted/50 border-b text-sm font-medium text-muted-foreground">
                <span>Keyword</span>
                <span className="text-center">Search Volume</span>
                <span className="text-center">Growth</span>
                <span className="text-center">Status</span>
                <span className="w-20 text-center">Category</span>
              </div>

              <div className="divide-y">
                {trends.map((trend) => {
                  const growthInfo = getGrowthBadge(trend.growth_percentage);
                  return (
                    <div key={trend.id} className="flex flex-col md:grid md:grid-cols-[2fr_1fr_1fr_1fr_auto] gap-2 md:gap-4 px-6 py-3 items-start md:items-center hover:bg-muted/30 transition-colors">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium truncate">{trend.keyword}</span>
                          {trend.is_featured && (
                            <Badge variant="secondary" className="text-xs shrink-0">Hot</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground truncate mt-0.5">
                          {trend.business_implications}
                        </p>
                      </div>
                      <div className="text-center">
                        <span className="font-semibold">{formatVolume(trend.search_volume)}</span>
                        <span className="text-xs text-muted-foreground ml-1">monthly</span>
                      </div>
                      <div className="text-center flex items-center justify-center gap-1">
                        {trend.growth_percentage >= 0 ? (
                          <TrendingUp className={`h-4 w-4 ${growthInfo.color}`} />
                        ) : (
                          <TrendingDown className={`h-4 w-4 ${growthInfo.color}`} />
                        )}
                        <span className={`font-semibold ${growthInfo.color}`}>
                          {trend.growth_percentage > 0 ? "+" : ""}
                          {trend.growth_percentage.toFixed(0)}%
                        </span>
                      </div>
                      <div className="text-center">
                        <Badge variant={growthInfo.variant}>{growthInfo.label}</Badge>
                      </div>
                      <Badge variant="outline" className="w-20 justify-center shrink-0">
                        {trend.category}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            </Card>

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
            <h2 className="text-2xl font-bold mb-2">Turn Trends into Business Ideas</h2>
            <p className="mb-6 text-primary-foreground/80">
              Our AI analyzes trends and generates validated startup opportunities.
            </p>
            <Button asChild size="lg" variant="secondary">
              <Link href="/auth/signup">Generate Ideas from Trends</Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
