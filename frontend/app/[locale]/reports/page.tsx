"use client";

import { useState, useEffect } from "react";
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
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  BarChart3,
  TrendingUp,
  Target,
  FileText,
  Download,
  RefreshCw,
  ChevronRight,
  Lightbulb,
  DollarSign,
  Users,
  Clock,
  AlertTriangle,
  CheckCircle2,
  ArrowUpRight,
  Zap,
} from "lucide-react";

// Types for market intelligence data
interface MarketSizing {
  tam: { value: string; description: string };
  sam: { value: string; description: string };
  som: { value: string; description: string };
  methodology: string;
  assumptions: string[];
  confidence_level: string;
}

interface IndustryBenchmark {
  metric_name: string;
  industry_average: string;
  top_performer: string;
  startup_target: string;
  source: string;
}

interface TrendOpportunity {
  trend_keyword: string;
  opportunity_score: number;
  business_implications: string;
  action_items: string[];
  time_sensitivity: string;
}

interface MarketReport {
  report_id: string;
  report_type: string;
  title: string;
  executive_summary: string;
  market_sizing?: MarketSizing;
  industry_benchmarks: IndustryBenchmark[];
  trend_opportunities: TrendOpportunity[];
  key_insights: string[];
  recommendations: string[];
  generated_at: string;
}

// Sample data for demonstration (will be replaced with API calls)
const sampleReport: MarketReport = {
  report_id: "MIR-20260129",
  report_type: "market_sizing",
  title: "SaaS Market Intelligence Report",
  executive_summary:
    "The SaaS market continues to show strong growth with AI-powered solutions leading the charge. Our analysis indicates significant opportunities in the API monitoring space, with TAM of $12B and achievable SOM of $120M in 3 years. Key differentiators include real-time anomaly detection and automated root cause analysis.",
  market_sizing: {
    tam: { value: "$12B", description: "Global API Monitoring Market" },
    sam: { value: "$3.2B", description: "SMB SaaS Companies" },
    som: { value: "$120M", description: "3-Year Achievable Market" },
    methodology: "Bottom-up analysis based on target customer segments",
    assumptions: [
      "15% annual market growth",
      "5% market penetration in year 1",
      "Average contract value of $2,400/year",
      "40% gross margin",
    ],
    confidence_level: "high",
  },
  industry_benchmarks: [
    {
      metric_name: "CAC (Customer Acquisition Cost)",
      industry_average: "$450",
      top_performer: "$180",
      startup_target: "$300",
      source: "SaaS Benchmarks 2026",
    },
    {
      metric_name: "LTV (Lifetime Value)",
      industry_average: "$2,400",
      top_performer: "$8,500",
      startup_target: "$3,600",
      source: "OpenView Partners",
    },
    {
      metric_name: "LTV:CAC Ratio",
      industry_average: "3:1",
      top_performer: "5:1",
      startup_target: "4:1",
      source: "SaaS Benchmarks 2026",
    },
    {
      metric_name: "Monthly Churn Rate",
      industry_average: "3.5%",
      top_performer: "1.2%",
      startup_target: "2.5%",
      source: "Baremetrics",
    },
    {
      metric_name: "Net Revenue Retention",
      industry_average: "105%",
      top_performer: "130%",
      startup_target: "115%",
      source: "KeyBanc Capital",
    },
  ],
  trend_opportunities: [
    {
      trend_keyword: "AI-powered observability",
      opportunity_score: 92,
      business_implications:
        "Growing demand for automated incident detection and root cause analysis. Organizations want to reduce MTTR and prevent outages proactively.",
      action_items: [
        "Develop ML-based anomaly detection",
        "Build automated RCA feature",
        "Create predictive alerting system",
      ],
      time_sensitivity: "urgent",
    },
    {
      trend_keyword: "DevOps automation",
      opportunity_score: 85,
      business_implications:
        "DevOps teams seeking tools that integrate into CI/CD pipelines and provide actionable insights without context switching.",
      action_items: [
        "Build GitHub/GitLab integrations",
        "Create Slack/Teams alerting",
        "Develop API for custom integrations",
      ],
      time_sensitivity: "near-term",
    },
    {
      trend_keyword: "Platform engineering",
      opportunity_score: 78,
      business_implications:
        "Internal developer platforms need standardized monitoring solutions that work across multiple services and teams.",
      action_items: [
        "Build multi-tenant architecture",
        "Create team-based dashboards",
        "Implement RBAC",
      ],
      time_sensitivity: "near-term",
    },
  ],
  key_insights: [
    "API monitoring market growing at 15% CAGR through 2028",
    "70% of enterprises plan to increase observability spending",
    "AI-powered solutions command 40% price premium",
    "SMB segment underserved by current market leaders",
    "Self-service onboarding critical for product-led growth",
  ],
  recommendations: [
    "Focus on SMB segment with self-service PLG motion",
    "Invest heavily in AI/ML capabilities for differentiation",
    "Build strong integrations ecosystem early",
    "Target 4:1 LTV:CAC ratio within 18 months",
    "Pursue SOC 2 compliance for enterprise readiness",
  ],
  generated_at: new Date().toISOString(),
};

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [isGenerating, setIsGenerating] = useState(false);
  const [report, setReport] = useState<MarketReport | null>(sampleReport);
  const [selectedReportType, setSelectedReportType] = useState("market_sizing");

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    // TODO: Replace with real API call when backend report generation endpoint exists.
    // Currently uses sampleReport placeholder data with a simulated delay.
    // Target endpoint: POST /api/reports/generate with { report_type: selectedReportType }
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setReport(sampleReport);
    setIsGenerating(false);
  };

  const getTimeSensitivityColor = (sensitivity: string) => {
    switch (sensitivity) {
      case "urgent":
        return "text-red-600 bg-red-50";
      case "near-term":
        return "text-yellow-600 bg-yellow-50";
      case "long-term":
        return "text-green-600 bg-green-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getConfidenceColor = (level: string) => {
    switch (level) {
      case "high":
        return "text-green-600";
      case "medium":
        return "text-yellow-600";
      case "low":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <div className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
                <Link href="/" className="hover:text-blue-600">
                  Home
                </Link>
                <ChevronRight className="w-4 h-4" />
                <span>Market Intelligence</span>
              </div>
              <h1 className="text-3xl font-bold text-slate-900">
                Market Intelligence Reports
              </h1>
              <p className="text-slate-600 mt-2">
                AI-powered market analysis, industry benchmarks, and strategic
                recommendations
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Select
                value={selectedReportType}
                onValueChange={setSelectedReportType}
              >
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Report Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="market_sizing">Market Sizing</SelectItem>
                  <SelectItem value="weekly_digest">Weekly Digest</SelectItem>
                  <SelectItem value="competitive_landscape">
                    Competitive Analysis
                  </SelectItem>
                </SelectContent>
              </Select>
              <Button onClick={handleGenerateReport} disabled={isGenerating}>
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-2" />
                    Generate Report
                  </>
                )}
              </Button>
              <Button variant="outline">
                <Download className="w-4 h-4 mr-2" />
                Export PDF
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {report ? (
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-8">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger
                value="market-sizing"
                className="flex items-center gap-2"
              >
                <Target className="w-4 h-4" />
                Market Sizing
              </TabsTrigger>
              <TabsTrigger
                value="benchmarks"
                className="flex items-center gap-2"
              >
                <TrendingUp className="w-4 h-4" />
                Benchmarks
              </TabsTrigger>
              <TabsTrigger
                value="opportunities"
                className="flex items-center gap-2"
              >
                <Lightbulb className="w-4 h-4" />
                Opportunities
              </TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {/* Executive Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    Executive Summary
                  </CardTitle>
                  <CardDescription>
                    Report ID: {report.report_id} | Generated:{" "}
                    {new Date(report.generated_at).toLocaleDateString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-slate-700 leading-relaxed">
                    {report.executive_summary}
                  </p>
                </CardContent>
              </Card>

              {/* Quick Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {report.market_sizing && (
                  <>
                    <Card className="bg-gradient-to-br from-blue-50 to-white border-blue-100">
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-xs font-medium text-blue-600 uppercase tracking-wider">
                            Total Addressable Market
                          </p>
                          <p className="text-4xl font-bold text-blue-700 mt-2">
                            {report.market_sizing.tam.value}
                          </p>
                          <p className="text-sm text-slate-500 mt-1">
                            {report.market_sizing.tam.description}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card className="bg-gradient-to-br from-green-50 to-white border-green-100">
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-xs font-medium text-green-600 uppercase tracking-wider">
                            Serviceable Market
                          </p>
                          <p className="text-4xl font-bold text-green-700 mt-2">
                            {report.market_sizing.sam.value}
                          </p>
                          <p className="text-sm text-slate-500 mt-1">
                            {report.market_sizing.sam.description}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card className="bg-gradient-to-br from-purple-50 to-white border-purple-100">
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-xs font-medium text-purple-600 uppercase tracking-wider">
                            Obtainable Market
                          </p>
                          <p className="text-4xl font-bold text-purple-700 mt-2">
                            {report.market_sizing.som.value}
                          </p>
                          <p className="text-sm text-slate-500 mt-1">
                            {report.market_sizing.som.description}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </>
                )}
              </div>

              {/* Key Insights & Recommendations */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Lightbulb className="w-5 h-5 text-yellow-500" />
                      Key Insights
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {report.key_insights.map((insight, index) => (
                        <li key={index} className="flex items-start gap-3">
                          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-medium">
                            {index + 1}
                          </span>
                          <span className="text-slate-700">{insight}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                      Strategic Recommendations
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {report.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start gap-3">
                          <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                          <span className="text-slate-700">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Market Sizing Tab */}
            <TabsContent value="market-sizing" className="space-y-6">
              {report.market_sizing && (
                <>
                  {/* TAM/SAM/SOM Visualization */}
                  <Card>
                    <CardHeader>
                      <CardTitle>TAM / SAM / SOM Analysis</CardTitle>
                      <CardDescription>
                        Market sizing methodology: {report.market_sizing.methodology}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-8">
                        {/* TAM */}
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium text-slate-700">
                              Total Addressable Market (TAM)
                            </span>
                            <span className="text-2xl font-bold text-blue-600">
                              {report.market_sizing.tam.value}
                            </span>
                          </div>
                          <Progress value={100} className="h-4 bg-blue-100" />
                          <p className="text-sm text-slate-500 mt-1">
                            {report.market_sizing.tam.description}
                          </p>
                        </div>

                        {/* SAM */}
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium text-slate-700">
                              Serviceable Addressable Market (SAM)
                            </span>
                            <span className="text-2xl font-bold text-green-600">
                              {report.market_sizing.sam.value}
                            </span>
                          </div>
                          <Progress value={27} className="h-4 bg-green-100" />
                          <p className="text-sm text-slate-500 mt-1">
                            {report.market_sizing.sam.description}
                          </p>
                        </div>

                        {/* SOM */}
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium text-slate-700">
                              Serviceable Obtainable Market (SOM)
                            </span>
                            <span className="text-2xl font-bold text-purple-600">
                              {report.market_sizing.som.value}
                            </span>
                          </div>
                          <Progress value={4} className="h-4 bg-purple-100" />
                          <p className="text-sm text-slate-500 mt-1">
                            {report.market_sizing.som.description}
                          </p>
                        </div>
                      </div>

                      <Separator className="my-6" />

                      {/* Assumptions */}
                      <div>
                        <h4 className="font-medium text-slate-900 mb-3">
                          Key Assumptions
                        </h4>
                        <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {report.market_sizing.assumptions.map((assumption, index) => (
                            <li
                              key={index}
                              className="flex items-center gap-2 text-slate-600"
                            >
                              <div className="w-2 h-2 rounded-full bg-blue-500" />
                              {assumption}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="mt-6 flex items-center gap-2">
                        <span className="text-sm text-slate-500">
                          Confidence Level:
                        </span>
                        <Badge
                          variant="outline"
                          className={getConfidenceColor(
                            report.market_sizing.confidence_level
                          )}
                        >
                          {report.market_sizing.confidence_level.toUpperCase()}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Benchmarks Tab */}
            <TabsContent value="benchmarks" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Industry Benchmarks</CardTitle>
                  <CardDescription>
                    Compare your targets against industry standards and top
                    performers
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Metric</TableHead>
                        <TableHead>Industry Average</TableHead>
                        <TableHead>Top Performer</TableHead>
                        <TableHead>Your Target</TableHead>
                        <TableHead>Source</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {report.industry_benchmarks.map((benchmark, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">
                            {benchmark.metric_name}
                          </TableCell>
                          <TableCell>{benchmark.industry_average}</TableCell>
                          <TableCell className="text-green-600">
                            {benchmark.top_performer}
                          </TableCell>
                          <TableCell className="font-semibold text-blue-600">
                            {benchmark.startup_target}
                          </TableCell>
                          <TableCell className="text-slate-500 text-sm">
                            {benchmark.source}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              {/* Benchmark Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {report.industry_benchmarks.slice(0, 3).map((benchmark, index) => (
                  <Card key={index}>
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <p className="text-sm font-medium text-slate-500">
                          {benchmark.metric_name}
                        </p>
                        <p className="text-3xl font-bold text-blue-600 mt-2">
                          {benchmark.startup_target}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">Your Target</p>
                        <Separator className="my-4" />
                        <div className="flex justify-between text-sm">
                          <div>
                            <p className="text-slate-500">Industry Avg</p>
                            <p className="font-medium">{benchmark.industry_average}</p>
                          </div>
                          <div>
                            <p className="text-slate-500">Top Performer</p>
                            <p className="font-medium text-green-600">
                              {benchmark.top_performer}
                            </p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* Opportunities Tab */}
            <TabsContent value="opportunities" className="space-y-6">
              <div className="grid gap-6">
                {report.trend_opportunities.map((opportunity, index) => (
                  <Card key={index} className="overflow-hidden">
                    <div className="flex">
                      {/* Score Indicator */}
                      <div
                        className={`w-2 ${
                          opportunity.opportunity_score >= 90
                            ? "bg-green-500"
                            : opportunity.opportunity_score >= 70
                            ? "bg-yellow-500"
                            : "bg-slate-300"
                        }`}
                      />
                      <div className="flex-1">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div>
                              <CardTitle className="flex items-center gap-2">
                                <TrendingUp className="w-5 h-5 text-blue-600" />
                                {opportunity.trend_keyword}
                              </CardTitle>
                              <CardDescription className="mt-1">
                                {opportunity.business_implications}
                              </CardDescription>
                            </div>
                            <div className="text-right">
                              <div className="text-3xl font-bold text-blue-600">
                                {opportunity.opportunity_score}
                              </div>
                              <div className="text-xs text-slate-500">
                                Opportunity Score
                              </div>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="flex items-center gap-2 mb-4">
                            <Clock className="w-4 h-4 text-slate-400" />
                            <Badge
                              variant="outline"
                              className={getTimeSensitivityColor(
                                opportunity.time_sensitivity
                              )}
                            >
                              {opportunity.time_sensitivity.toUpperCase()}
                            </Badge>
                          </div>

                          <h4 className="font-medium text-slate-900 mb-3">
                            Action Items
                          </h4>
                          <ul className="space-y-2">
                            {opportunity.action_items.map((action, actionIndex) => (
                              <li
                                key={actionIndex}
                                className="flex items-center gap-2 text-slate-600"
                              >
                                <ArrowUpRight className="w-4 h-4 text-blue-500" />
                                {action}
                              </li>
                            ))}
                          </ul>
                        </CardContent>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        ) : (
          /* Empty State */
          <Card className="text-center py-16">
            <CardContent>
              <BarChart3 className="w-16 h-16 mx-auto text-slate-300 mb-4" />
              <h3 className="text-xl font-semibold text-slate-700 mb-2">
                No Report Generated Yet
              </h3>
              <p className="text-slate-500 mb-6 max-w-md mx-auto">
                Generate a market intelligence report to see TAM/SAM/SOM analysis,
                industry benchmarks, and strategic recommendations.
              </p>
              <Button onClick={handleGenerateReport} size="lg">
                <Zap className="w-4 h-4 mr-2" />
                Generate Your First Report
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
