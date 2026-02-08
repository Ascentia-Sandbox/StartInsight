"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink, Search, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
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

interface Tool {
  id: string;
  name: string;
  tagline: string;
  description: string;
  category: string;
  pricing: string;
  website_url: string;
  logo_url: string | null;
  is_featured: boolean;
}

interface ToolsResponse {
  tools: Tool[];
  total: number;
  limit: number;
  offset: number;
}

const categories = [
  "All",
  "Payments",
  "No-Code",
  "Analytics",
  "Marketing",
  "Design",
  "Development",
  "AI/ML",
  "Communication",
  "Productivity",
];

const pricingOptions = ["All", "Free", "Freemium", "Paid"];

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [pricing, setPricing] = useState("All");
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const limit = 12;

  useEffect(() => {
    fetchTools();
  }, [search, category, pricing, page]);

  const fetchTools = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (category !== "All") params.append("category", category);
      if (pricing !== "All") params.append("pricing", pricing);
      params.append("limit", limit.toString());
      params.append("offset", (page * limit).toString());

      const response = await fetch(
        `${config.apiUrl}/api/tools?${params}`
      );
      const data: ToolsResponse = await response.json();
      setTools(data.tools);
      setTotal(data.total);
    } catch (error) {
      console.error("Failed to fetch tools:", error);
      // Show placeholder data for development
      setTools([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const getPricingBadgeVariant = (pricing: string) => {
    if (pricing.toLowerCase().includes("free")) return "secondary";
    if (pricing.toLowerCase().includes("freemium")) return "outline";
    return "default";
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Badge variant="secondary" className="mb-4">Tools Library</Badge>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          54 Tools to Build Your Startup
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Curated collection of essential tools for payments, marketing, development, and more.
        </p>
      </section>

      {/* Filters */}
      <section className="container mx-auto px-4 pb-8">
        <div className="flex flex-col md:flex-row gap-4 max-w-4xl mx-auto">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search tools..."
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
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              {categories.map((cat) => (
                <SelectItem key={cat} value={cat}>
                  {cat}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={pricing}
            onValueChange={(value) => {
              setPricing(value);
              setPage(0);
            }}
          >
            <SelectTrigger className="w-full md:w-[140px]">
              <SelectValue placeholder="Pricing" />
            </SelectTrigger>
            <SelectContent>
              {pricingOptions.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </section>

      {/* Tools Grid */}
      <section className="container mx-auto px-4 pb-16">
        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {[...Array(6)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-12 w-12 rounded-lg" />
                  <Skeleton className="h-6 w-32 mt-2" />
                  <Skeleton className="h-4 w-full mt-2" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-20 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : tools.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-muted-foreground mb-4">
              {search || category !== "All" || pricing !== "All"
                ? "No tools found matching your criteria."
                : "No tools available yet. Check back soon!"}
            </p>
            {(search || category !== "All" || pricing !== "All") && (
              <Button
                variant="outline"
                onClick={() => {
                  setSearch("");
                  setCategory("All");
                  setPricing("All");
                }}
              >
                Clear Filters
              </Button>
            )}
          </div>
        ) : (
          <>
            <div className="text-sm text-muted-foreground text-center mb-6">
              Showing {tools.length} of {total} tools
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
              {tools.map((tool) => (
                <Card key={tool.id} className="group hover:shadow-lg transition-shadow">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        {tool.logo_url ? (
                          <img
                            src={tool.logo_url}
                            alt={tool.name}
                            className="h-12 w-12 rounded-lg object-cover"
                          />
                        ) : (
                          <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-bold text-lg">
                            {tool.name[0]}
                          </div>
                        )}
                        <div>
                          <CardTitle className="text-lg">{tool.name}</CardTitle>
                          <Badge variant={getPricingBadgeVariant(tool.pricing)} className="mt-1">
                            {tool.pricing}
                          </Badge>
                        </div>
                      </div>
                      {tool.is_featured && (
                        <Badge variant="secondary" className="text-xs">Featured</Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="mb-2">{tool.tagline}</CardDescription>
                    <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
                      {tool.description}
                    </p>
                    <div className="flex items-center justify-between">
                      <Badge variant="outline">{tool.category}</Badge>
                      <Button asChild variant="ghost" size="sm">
                        <a
                          href={tool.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1"
                        >
                          Visit
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </Button>
                    </div>
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
        <Card className="max-w-2xl mx-auto">
          <CardContent className="pt-8 pb-8">
            <h2 className="text-2xl font-bold mb-2">Know a Great Tool?</h2>
            <p className="text-muted-foreground mb-6">
              Help fellow founders by suggesting tools that helped you build your startup.
            </p>
            <Button asChild>
              <Link href="/contact?subject=tool-suggestion">Suggest a Tool</Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
