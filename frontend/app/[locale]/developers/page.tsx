"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import {
  Code2,
  Key,
  Zap,
  Shield,
  BookOpen,
  Terminal,
  Webhook,
  BarChart3,
  ChevronRight,
  Copy,
  Check,
  ExternalLink,
  Sparkles,
  Clock,
  Users,
  Database,
} from "lucide-react";

// API Endpoints data
const apiEndpoints = [
  {
    method: "GET",
    path: "/api/insights",
    description: "List all insights with pagination and filters",
    auth: "API Key",
    rateLimit: "100/min",
  },
  {
    method: "GET",
    path: "/api/insights/{id}",
    description: "Get a single insight by ID",
    auth: "API Key",
    rateLimit: "100/min",
  },
  {
    method: "POST",
    path: "/api/insights",
    description: "Create a new insight (triggers AI analysis)",
    auth: "API Key + Pro",
    rateLimit: "10/min",
  },
  {
    method: "GET",
    path: "/api/trends",
    description: "List trending keywords with growth metrics",
    auth: "Public",
    rateLimit: "60/min",
  },
  {
    method: "GET",
    path: "/api/trends/predictions",
    description: "Get AI-powered trend predictions",
    auth: "API Key",
    rateLimit: "30/min",
  },
  {
    method: "GET",
    path: "/api/tools",
    description: "List all tools in the directory",
    auth: "Public",
    rateLimit: "60/min",
  },
  {
    method: "GET",
    path: "/api/success-stories",
    description: "List founder success stories",
    auth: "Public",
    rateLimit: "60/min",
  },
  {
    method: "POST",
    path: "/api/research",
    description: "Start an AI research request",
    auth: "API Key + Pro",
    rateLimit: "5/min",
  },
];

// Pricing tiers
const pricingTiers = [
  {
    name: "Free",
    price: "$0",
    requests: "1,000/month",
    features: [
      "Public endpoints only",
      "60 req/min rate limit",
      "Community support",
      "Basic documentation",
    ],
  },
  {
    name: "Developer",
    price: "$29/mo",
    requests: "50,000/month",
    features: [
      "All public + authenticated endpoints",
      "100 req/min rate limit",
      "Email support",
      "Webhook notifications",
      "Usage analytics",
    ],
  },
  {
    name: "Pro",
    price: "$99/mo",
    requests: "500,000/month",
    features: [
      "All endpoints including AI research",
      "300 req/min rate limit",
      "Priority support",
      "Custom webhooks",
      "Sandbox environment",
      "SLA 99.9%",
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    requests: "Unlimited",
    features: [
      "Dedicated infrastructure",
      "Custom rate limits",
      "Dedicated support",
      "Custom integrations",
      "SOC 2 compliance",
      "SLA 99.99%",
    ],
  },
];

// Code examples
const codeExamples = {
  curl: `curl -X GET "https://api.startinsight.ai/api/insights" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"`,
  python: `import requests

response = requests.get(
    "https://api.startinsight.ai/api/insights",
    headers={
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    }
)

insights = response.json()
print(f"Found {len(insights['data'])} insights")`,
  javascript: `const response = await fetch(
  'https://api.startinsight.ai/api/insights',
  {
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY',
      'Content-Type': 'application/json'
    }
  }
);

const insights = await response.json();
console.log(\`Found \${insights.data.length} insights\`);`,
};

export default function DevelopersPage() {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState("curl");

  const copyToClipboard = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const getMethodColor = (method: string) => {
    switch (method) {
      case "GET":
        return "bg-green-100 text-green-700";
      case "POST":
        return "bg-blue-100 text-blue-700";
      case "PUT":
        return "bg-yellow-100 text-yellow-700";
      case "PATCH":
        return "bg-orange-100 text-orange-700";
      case "DELETE":
        return "bg-red-100 text-red-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
      {/* Hero Section */}
      <div className="border-b border-slate-700 bg-slate-900/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-16">
          <div className="max-w-4xl mx-auto text-center">
            <Badge className="mb-4 bg-blue-500/10 text-blue-400 border-blue-500/20">
              Developer Portal
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Build with the StartInsight API
            </h1>
            <p className="text-xl text-slate-300 mb-8">
              Access 230+ endpoints to integrate startup insights, trend
              predictions, and AI-powered research into your applications.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
                <Key className="w-4 h-4 mr-2" />
                Get API Key
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-slate-600 text-slate-300 hover:bg-slate-800"
              >
                <BookOpen className="w-4 h-4 mr-2" />
                View Documentation
              </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-12">
              <div className="text-center">
                <div className="text-3xl font-bold text-white">230+</div>
                <div className="text-slate-400">API Endpoints</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-white">99.9%</div>
                <div className="text-slate-400">Uptime SLA</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-white">&lt;100ms</div>
                <div className="text-slate-400">Avg Response</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-white">1M+</div>
                <div className="text-slate-400">API Calls/Day</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-12">
        <Tabs defaultValue="quickstart" className="space-y-8">
          <TabsList className="bg-slate-800 border border-slate-700">
            <TabsTrigger value="quickstart">Quick Start</TabsTrigger>
            <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
            <TabsTrigger value="webhooks">Webhooks</TabsTrigger>
            <TabsTrigger value="pricing">Pricing</TabsTrigger>
          </TabsList>

          {/* Quick Start Tab */}
          <TabsContent value="quickstart" className="space-y-8">
            {/* Authentication */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Shield className="w-5 h-5 text-blue-400" />
                  Authentication
                </CardTitle>
                <CardDescription className="text-slate-400">
                  All authenticated requests require an API key in the
                  Authorization header
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm">
                  <div className="flex items-center justify-between">
                    <code className="text-green-400">
                      Authorization: Bearer YOUR_API_KEY
                    </code>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-slate-400 hover:text-white"
                      onClick={() =>
                        copyToClipboard(
                          "Authorization: Bearer YOUR_API_KEY",
                          "auth"
                        )
                      }
                    >
                      {copiedCode === "auth" ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Code Examples */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Terminal className="w-5 h-5 text-green-400" />
                  Code Examples
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Get started in your preferred language
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs
                  value={selectedLanguage}
                  onValueChange={setSelectedLanguage}
                >
                  <TabsList className="bg-slate-900 border border-slate-700 mb-4">
                    <TabsTrigger value="curl">cURL</TabsTrigger>
                    <TabsTrigger value="python">Python</TabsTrigger>
                    <TabsTrigger value="javascript">JavaScript</TabsTrigger>
                  </TabsList>

                  {Object.entries(codeExamples).map(([lang, code]) => (
                    <TabsContent key={lang} value={lang}>
                      <div className="relative">
                        <pre className="bg-slate-900 rounded-lg p-4 overflow-x-auto">
                          <code className="text-slate-300 text-sm">{code}</code>
                        </pre>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="absolute top-2 right-2 text-slate-400 hover:text-white"
                          onClick={() => copyToClipboard(code, lang)}
                        >
                          {copiedCode === lang ? (
                            <Check className="w-4 h-4" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </TabsContent>
                  ))}
                </Tabs>
              </CardContent>
            </Card>

            {/* Feature Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="pt-6">
                  <Sparkles className="w-10 h-10 text-purple-400 mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">
                    AI-Powered Research
                  </h3>
                  <p className="text-slate-400 text-sm">
                    Trigger automated 40-step research analysis on any startup
                    idea via API
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="pt-6">
                  <BarChart3 className="w-10 h-10 text-blue-400 mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">
                    Trend Predictions
                  </h3>
                  <p className="text-slate-400 text-sm">
                    Access 7-day ahead trend forecasts with confidence intervals
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="pt-6">
                  <Webhook className="w-10 h-10 text-green-400 mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">
                    Real-time Webhooks
                  </h3>
                  <p className="text-slate-400 text-sm">
                    Get notified instantly when new insights match your criteria
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Endpoints Tab */}
          <TabsContent value="endpoints">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">API Endpoints</CardTitle>
                <CardDescription className="text-slate-400">
                  Core endpoints for insights, trends, and research
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-700">
                      <TableHead className="text-slate-400">Method</TableHead>
                      <TableHead className="text-slate-400">Endpoint</TableHead>
                      <TableHead className="text-slate-400">
                        Description
                      </TableHead>
                      <TableHead className="text-slate-400">Auth</TableHead>
                      <TableHead className="text-slate-400">
                        Rate Limit
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {apiEndpoints.map((endpoint, index) => (
                      <TableRow key={index} className="border-slate-700">
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={getMethodColor(endpoint.method)}
                          >
                            {endpoint.method}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-sm text-slate-300">
                          {endpoint.path}
                        </TableCell>
                        <TableCell className="text-slate-400">
                          {endpoint.description}
                        </TableCell>
                        <TableCell className="text-slate-400">
                          {endpoint.auth}
                        </TableCell>
                        <TableCell className="text-slate-400">
                          {endpoint.rateLimit}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div className="mt-4 text-center">
                  <Button variant="outline" className="border-slate-600">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    View Full API Reference
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Webhooks Tab */}
          <TabsContent value="webhooks">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Webhook className="w-5 h-5 text-green-400" />
                  Webhook Events
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Subscribe to real-time events from the StartInsight platform
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    {
                      event: "insight.created",
                      description: "New insight is created",
                    },
                    {
                      event: "insight.analyzed",
                      description: "AI analysis is complete",
                    },
                    {
                      event: "trend.spike",
                      description: "Trend velocity exceeds threshold",
                    },
                    {
                      event: "research.completed",
                      description: "Research request is finished",
                    },
                  ].map((webhook, index) => (
                    <div
                      key={index}
                      className="bg-slate-900 rounded-lg p-4 border border-slate-700"
                    >
                      <code className="text-green-400 text-sm">
                        {webhook.event}
                      </code>
                      <p className="text-slate-400 text-sm mt-1">
                        {webhook.description}
                      </p>
                    </div>
                  ))}
                </div>

                <Separator className="bg-slate-700" />

                <div>
                  <h4 className="text-white font-medium mb-3">
                    Example Payload
                  </h4>
                  <pre className="bg-slate-900 rounded-lg p-4 overflow-x-auto">
                    <code className="text-slate-300 text-sm">
                      {`{
  "event": "insight.analyzed",
  "timestamp": "2026-01-29T12:00:00Z",
  "data": {
    "insight_id": "uuid-here",
    "viability_score": 8.5,
    "status": "completed"
  }
}`}
                    </code>
                  </pre>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Pricing Tab */}
          <TabsContent value="pricing">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {pricingTiers.map((tier, index) => (
                <Card
                  key={index}
                  className={`bg-slate-800 border-slate-700 ${
                    tier.name === "Pro" ? "ring-2 ring-blue-500" : ""
                  }`}
                >
                  <CardHeader>
                    <CardTitle className="text-white">{tier.name}</CardTitle>
                    <div className="text-3xl font-bold text-white">
                      {tier.price}
                      {tier.price !== "Custom" && (
                        <span className="text-sm font-normal text-slate-400">
                          /month
                        </span>
                      )}
                    </div>
                    <CardDescription className="text-slate-400">
                      {tier.requests} requests
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {tier.features.map((feature, fIndex) => (
                        <li
                          key={fIndex}
                          className="flex items-start gap-2 text-sm text-slate-300"
                        >
                          <Check className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                    <Button
                      className={`w-full mt-6 ${
                        tier.name === "Pro"
                          ? "bg-blue-600 hover:bg-blue-700"
                          : "bg-slate-700 hover:bg-slate-600"
                      }`}
                    >
                      {tier.name === "Enterprise" ? "Contact Sales" : "Get Started"}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
