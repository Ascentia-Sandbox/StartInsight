'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Database, TrendingUp, Users, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { CommunitySignalsRow } from './community-signals-badge';
import { TrendIndicator, TrendStats } from './trend-indicator';
import { DataCitationLink } from './data-citation-link';
import { CommunitySignalsRadar } from './community-signals-radar';
import { ScoreBreakdown } from './score-breakdown';

interface EvidenceData {
  community_signals?: Record<string, {
    score?: number;
    members?: number;
    subreddits?: string[];
    groups?: number;
    channels?: number;
    views?: string;
    engagement?: number;
    top_post_url?: string;
  }>;
  community_signals_chart?: Array<{
    platform: 'Reddit' | 'Facebook' | 'YouTube' | 'Other';
    score: number;
    members: number;
    engagement_rate: number;
    top_url?: string | null;
  }>;
  enhanced_scores?: Array<{
    dimension: string;
    value: number;
    label: string;
  }>;
  trend_data?: {
    keyword?: string;
    volume?: string | number;
    growth?: string | number;
    current_interest?: number;
    avg_interest?: number;
    max_interest?: number;
    chart_data?: Array<{ date: string; volume: number }>;
  };
  sources?: Array<{ url: string; platform: string }>;
}

interface EvidencePanelProps {
  evidence: EvidenceData | Record<string, any> | null | undefined;
  primarySource?: { url: string; platform: string };
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function EvidencePanel({
  evidence,
  primarySource,
  collapsible = true,
  defaultExpanded = true,
}: EvidencePanelProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  // Early return if no evidence
  if (!evidence) return null;

  const communitySignals = evidence.community_signals;
  const communitySignalsChart = evidence.community_signals_chart;
  const enhancedScores = evidence.enhanced_scores;
  const trendData = evidence.trend_data;
  const hasCommunitySignals = communitySignals && Object.keys(communitySignals).length > 0;
  const hasCommunitySignalsChart = communitySignalsChart && communitySignalsChart.length > 0;
  const hasEnhancedScores = enhancedScores && enhancedScores.length > 0;
  const hasTrendData = trendData && (trendData.growth || trendData.current_interest);

  // Count total data sources
  const sourceCount = (hasCommunitySignals ? Object.keys(communitySignals!).length : 0) +
                      (hasCommunitySignalsChart ? communitySignalsChart!.length : 0) +
                      (hasEnhancedScores ? 1 : 0) +
                      (hasTrendData ? 1 : 0) +
                      (primarySource ? 1 : 0);

  if (sourceCount === 0) return null;

  const header = (
    <CardHeader className="pb-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-lg">Evidence Engine</CardTitle>
          <Badge variant="secondary" className="ml-2">
            {sourceCount} {sourceCount === 1 ? 'source' : 'sources'}
          </Badge>
        </div>
        {collapsible && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="gap-1"
          >
            {isExpanded ? (
              <>Hide <ChevronUp className="h-4 w-4" /></>
            ) : (
              <>Show <ChevronDown className="h-4 w-4" /></>
            )}
          </Button>
        )}
      </div>
      <p className="text-sm text-muted-foreground">
        Data-driven insights from {sourceCount} verified {sourceCount === 1 ? 'source' : 'sources'}
      </p>
    </CardHeader>
  );

  if (!isExpanded) {
    return <Card>{header}</Card>;
  }

  return (
    <Card>
      {header}
      <CardContent className="space-y-6">
        {/* Community Signals Section */}
        {hasCommunitySignals && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <h4 className="font-medium text-sm">Community Signals</h4>
            </div>
            <CommunitySignalsRow signals={communitySignals!} />

            {/* Show top posts/sources if available */}
            <div className="flex flex-wrap gap-2 mt-2">
              {Object.entries(communitySignals!).map(([platform, signal]) => {
                const signalData = signal as { top_post_url?: string };
                if (signalData.top_post_url) {
                  return (
                    <DataCitationLink
                      key={platform}
                      url={signalData.top_post_url}
                      platform={platform}
                      variant="badge"
                    />
                  );
                }
                return null;
              })}
            </div>
          </div>
        )}

        {hasCommunitySignals && (hasCommunitySignalsChart || hasEnhancedScores || hasTrendData) && <Separator />}

        {/* Community Signals Radar Chart */}
        {hasCommunitySignalsChart && (
          <div className="space-y-3">
            <CommunitySignalsRadar signals={communitySignalsChart!} />
          </div>
        )}

        {hasCommunitySignalsChart && (hasEnhancedScores || hasTrendData) && <Separator />}

        {/* Enhanced Scoring Breakdown */}
        {hasEnhancedScores && (
          <div className="space-y-3">
            <ScoreBreakdown scores={enhancedScores!} />
          </div>
        )}

        {hasEnhancedScores && hasTrendData && <Separator />}

        {/* Trend Data Section */}
        {hasTrendData && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
                <h4 className="font-medium text-sm">
                  Search Trends
                  {trendData.keyword && (
                    <span className="text-muted-foreground ml-1">
                      "{trendData.keyword}"
                    </span>
                  )}
                </h4>
              </div>
              {trendData.growth && (
                <TrendIndicator growth={trendData.growth} size="sm" />
              )}
            </div>

            <TrendStats
              currentInterest={trendData.current_interest}
              avgInterest={trendData.avg_interest}
              peakInterest={trendData.max_interest}
              growth={trendData.growth}
            />

            {trendData.volume && (
              <p className="text-sm text-muted-foreground">
                Search volume: <span className="font-medium">{trendData.volume}</span>
              </p>
            )}
          </div>
        )}

        {(hasCommunitySignals || hasTrendData) && primarySource && <Separator />}

        {/* Primary Source */}
        {primarySource && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <ExternalLink className="h-4 w-4 text-muted-foreground" />
              <h4 className="font-medium text-sm">Original Source</h4>
            </div>
            <DataCitationLink
              url={primarySource.url}
              platform={primarySource.platform}
              variant="button"
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Export index file for easier imports
export { CommunitySignalsRow, CommunitySignalsBadge } from './community-signals-badge';
export { DataCitationLink, MultiSourceCitations } from './data-citation-link';
export { TrendIndicator, TrendStats } from './trend-indicator';
