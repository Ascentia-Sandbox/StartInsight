"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { ExternalLink, Search, Filter, Calculator, DollarSign, TrendingUp, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
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
  affiliate_url: string | null;
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

  // Market calculator state
  const [tamInput, setTamInput] = useState("1000000000");
  const [samPercent, setSamPercent] = useState([30]);
  const [somPercent, setSomPercent] = useState([10]);

  const tamValue = Number(tamInput.replace(/[^0-9]/g, "")) || 0;
  const samValue = tamValue * (samPercent[0] / 100);
  const somValue = samValue * (somPercent[0] / 100);

  const formatCurrency = useCallback((value: number) => {
    if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
    return `$${value.toLocaleString()}`;
  }, []);

  const formatTamInput = (raw: string) => {
    const digits = raw.replace(/[^0-9]/g, "");
    if (!digits) return "";
    return Number(digits).toLocaleString();
  };

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
          {total > 0 ? total : ''} Tools to Build Your Startup
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
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{tool.category}</Badge>
                        {tool.affiliate_url && (
                          <Badge variant="secondary" className="text-xs">Sponsored</Badge>
                        )}
                      </div>
                      <Button asChild variant="ghost" size="sm">
                        <a
                          href={tool.affiliate_url ?? tool.website_url}
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

      {/* Market Size Calculator */}
      <section id="market-calculator" className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <Badge variant="secondary" className="mb-4">
              <Calculator className="h-3 w-3 mr-1" />
              Calculator
            </Badge>
            <h2 className="text-3xl font-bold mb-2">Market Size Calculator</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Estimate your Total Addressable Market (TAM), Serviceable Addressable Market (SAM), and Serviceable Obtainable Market (SOM).
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Inputs */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Inputs</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    Total Addressable Market (TAM)
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
                    <Input
                      value={formatTamInput(tamInput)}
                      onChange={(e) => setTamInput(e.target.value.replace(/[^0-9]/g, ""))}
                      placeholder="1,000,000,000"
                      className="pl-7"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">Total market revenue opportunity</p>
                </div>

                <Separator />

                <div className="space-y-3">
                  <label className="text-sm font-medium flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Target className="h-4 w-4 text-muted-foreground" />
                      SAM % of TAM
                    </span>
                    <span className="text-primary font-bold">{samPercent[0]}%</span>
                  </label>
                  <Slider
                    value={samPercent}
                    onValueChange={setSamPercent}
                    min={1}
                    max={100}
                    step={1}
                  />
                  <p className="text-xs text-muted-foreground">% of TAM your product can serve</p>
                </div>

                <Separator />

                <div className="space-y-3">
                  <label className="text-sm font-medium flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-muted-foreground" />
                      SOM % of SAM
                    </span>
                    <span className="text-primary font-bold">{somPercent[0]}%</span>
                  </label>
                  <Slider
                    value={somPercent}
                    onValueChange={setSomPercent}
                    min={1}
                    max={100}
                    step={1}
                  />
                  <p className="text-xs text-muted-foreground">% of SAM you can realistically capture</p>
                </div>
              </CardContent>
            </Card>

            {/* Results */}
            <div className="space-y-4">
              <Card className="border-2">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-muted-foreground">TAM</span>
                    <Badge variant="outline">Total Addressable Market</Badge>
                  </div>
                  <div className="text-3xl font-bold">{formatCurrency(tamValue)}</div>
                  <p className="text-xs text-muted-foreground mt-1">Entire market demand</p>
                </CardContent>
              </Card>

              <Card className="border-2 border-primary/30">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-muted-foreground">SAM</span>
                    <Badge variant="secondary">Serviceable Addressable</Badge>
                  </div>
                  <div className="text-3xl font-bold text-primary">{formatCurrency(samValue)}</div>
                  <p className="text-xs text-muted-foreground mt-1">{samPercent[0]}% of TAM you can serve</p>
                </CardContent>
              </Card>

              <Card className="border-2 border-primary/60 bg-primary/5">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-muted-foreground">SOM</span>
                    <Badge>Serviceable Obtainable</Badge>
                  </div>
                  <div className="text-3xl font-bold text-primary">{formatCurrency(somValue)}</div>
                  <p className="text-xs text-muted-foreground mt-1">{somPercent[0]}% of SAM you can capture</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
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
