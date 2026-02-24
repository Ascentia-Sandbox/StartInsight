"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Copy, Check, ExternalLink, Code2 } from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

interface Endpoint {
  method: HttpMethod;
  path: string;
  description: string;
}

interface Category {
  id: string;
  label: string;
  icon: string;
  endpoints: Endpoint[];
}

// ─── Data ────────────────────────────────────────────────────────────────────

const categories: Category[] = [
  {
    id: "insights",
    label: "Insights",
    icon: "📊",
    endpoints: [
      {
        method: "GET",
        path: "/api/insights",
        description: "List all insights (filterable by score, source, category)",
      },
      {
        method: "GET",
        path: "/api/insights/{id}",
        description: "Get single insight with full 8-dimension analysis",
      },
      {
        method: "GET",
        path: "/api/insights/{id}/trend-data",
        description: "30-day Google Trends data for an insight",
      },
    ],
  },
  {
    id: "trends",
    label: "Trends",
    icon: "📈",
    endpoints: [
      {
        method: "GET",
        path: "/api/trends",
        description: "List trending keywords (filterable by category)",
      },
      {
        method: "GET",
        path: "/api/pulse",
        description: "Real-time signal stream (SSE)",
      },
      {
        method: "GET",
        path: "/api/signals/stats/summary",
        description: "Signal pipeline statistics",
      },
    ],
  },
  {
    id: "validate",
    label: "Validate",
    icon: "🔬",
    endpoints: [
      {
        method: "POST",
        path: "/api/validate",
        description: "Validate a startup idea — returns radar chart scores",
      },
    ],
  },
  {
    id: "auth",
    label: "Auth",
    icon: "🔑",
    endpoints: [
      {
        method: "POST",
        path: "/api/auth/login",
        description: "Exchange Supabase token for session",
      },
      {
        method: "GET",
        path: "/api/users/me",
        description: "Get current user profile",
      },
    ],
  },
  {
    id: "market-insights",
    label: "Market Insights",
    icon: "📚",
    endpoints: [
      {
        method: "GET",
        path: "/api/market-insights",
        description: "List AI-generated market analysis articles",
      },
      {
        method: "GET",
        path: "/api/market-insights/{slug}",
        description: "Get article by slug",
      },
    ],
  },
];

const QUICK_START = `curl -X GET "https://api.startinsight.co/api/insights?limit=10&min_score=0.8" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"`;

// ─── Sub-components ──────────────────────────────────────────────────────────

function MethodBadge({ method }: { method: HttpMethod }) {
  const colours: Record<HttpMethod, string> = {
    GET: "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300",
    POST: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
    PATCH: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
    DELETE: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  };
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-[11px] font-mono font-semibold tracking-wide ${colours[method]}`}
    >
      {method}
    </span>
  );
}

function EndpointCard({ endpoint }: { endpoint: Endpoint }) {
  return (
    <div className="border-l-4 border-teal-500 bg-white dark:bg-slate-900 rounded-r-lg px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-2 shadow-sm">
      <MethodBadge method={endpoint.method} />
      <code className="font-mono text-sm text-slate-800 dark:text-slate-200 flex-1">
        {endpoint.path}
      </code>
      <span className="text-sm text-slate-500 dark:text-slate-400 sm:text-right">
        {endpoint.description}
      </span>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function ApiDocsPage() {
  const [activeCategory, setActiveCategory] = useState<string>("insights");
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(QUICK_START);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const active = categories.find((c) => c.id === activeCategory) ?? categories[0];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* ── Hero ─────────────────────────────────────────────── */}
      <div className="bg-gradient-to-br from-teal-900 via-slate-900 to-slate-800 text-white">
        <div className="container mx-auto px-4 py-14 max-w-5xl">
          <Badge className="mb-4 bg-amber-500/20 text-amber-300 border-amber-500/30 text-xs font-semibold tracking-widest uppercase">
            API
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 leading-tight">
            Public API
          </h1>
          <p className="text-lg text-teal-200 max-w-2xl">
            232+ endpoints. Real-time startup intelligence at your fingertips.
          </p>

          {/* Swagger CTA */}
          <div className="mt-8 inline-flex items-center gap-3 bg-teal-600/30 border border-teal-500/40 rounded-xl px-5 py-4">
            <Code2 className="w-5 h-5 text-teal-300 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-white">
                Full Interactive Documentation
              </p>
              <p className="text-xs text-teal-300">
                Explore all 232 endpoints with live request builder
              </p>
            </div>
            <Link
              href="https://api.startinsight.co/docs"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button
                size="sm"
                className="bg-teal-500 hover:bg-teal-400 text-white shrink-0"
              >
                Open Swagger
                <ExternalLink className="w-3.5 h-3.5 ml-1.5" />
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* ── Main content ────────────────────────────────────── */}
      <div className="container mx-auto px-4 py-10 max-w-5xl">
        <div className="flex flex-col lg:flex-row gap-8">

          {/* Sidebar */}
          <aside className="lg:w-52 shrink-0">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3 px-1">
              Categories
            </p>
            <nav className="space-y-1">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
                    activeCategory === cat.id
                      ? "bg-teal-50 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  <span>{cat.icon}</span>
                  {cat.label}
                </button>
              ))}
            </nav>
          </aside>

          {/* Right panel */}
          <div className="flex-1 space-y-8">

            {/* Endpoint cards */}
            <section>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
                {active.icon} {active.label}
              </h2>
              <div className="space-y-3">
                {active.endpoints.map((ep) => (
                  <EndpointCard key={ep.path} endpoint={ep} />
                ))}
              </div>
            </section>

            {/* Authentication */}
            <section className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-3">
                Authentication
              </h2>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                All endpoints require a bearer token in every request:
              </p>
              <pre className="bg-slate-100 dark:bg-slate-800 rounded-lg px-4 py-2 text-sm font-mono text-teal-700 dark:text-teal-300 overflow-x-auto">
                Authorization: Bearer YOUR_API_KEY
              </pre>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-3">
                Get your API key:{" "}
                <Link
                  href="/settings"
                  className="text-teal-600 dark:text-teal-400 underline underline-offset-2 hover:text-teal-500"
                >
                  startinsight.co/settings
                </Link>{" "}
                → API Keys tab
              </p>
              <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                {[
                  ["Free", "100 req/day"],
                  ["Starter", "1K/day"],
                  ["Pro", "10K/day"],
                  ["Enterprise", "Unlimited"],
                ].map(([plan, limit]) => (
                  <div
                    key={plan}
                    className="bg-slate-50 dark:bg-slate-800 rounded-lg px-3 py-2 text-center"
                  >
                    <p className="font-semibold text-slate-700 dark:text-slate-300">
                      {plan}
                    </p>
                    <p className="text-slate-500 dark:text-slate-400">{limit}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* Quick start */}
            <section className="bg-white dark:bg-slate-900 rounded-xl border border-teal-300 dark:border-teal-700 p-6">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  Quick Start
                </h2>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-teal-600 dark:hover:text-teal-400 transition-colors"
                  aria-label="Copy to clipboard"
                >
                  {copied ? (
                    <Check className="w-3.5 h-3.5 text-teal-500" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
              <pre className="bg-slate-950 text-teal-300 rounded-lg px-4 py-4 text-sm font-mono overflow-x-auto leading-relaxed border-l-4 border-teal-500">
                {QUICK_START}
              </pre>
            </section>

            {/* Swagger CTA card */}
            <section className="bg-gradient-to-r from-teal-600 to-teal-700 rounded-xl p-6 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <p className="font-bold text-lg">Full Interactive Documentation</p>
                <p className="text-teal-100 text-sm mt-0.5">
                  Explore all 232 endpoints with live request builder and response
                  examples.
                </p>
              </div>
              <Link
                href="https://api.startinsight.co/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0"
              >
                <Button className="bg-white text-teal-700 hover:bg-teal-50 font-semibold">
                  Open Swagger UI
                  <ExternalLink className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </section>

          </div>
        </div>
      </div>
    </div>
  );
}
