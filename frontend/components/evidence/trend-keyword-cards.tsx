'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Search, BarChart3 } from 'lucide-react';

interface TrendKeyword {
  keyword: string;
  volume: string; // e.g., '1.0K', '27.1K', '74.0K'
  growth: string; // e.g., '+1900%', '+86%', '+514%'
}

interface TrendKeywordCardsProps {
  keywords: TrendKeyword[];
}

// Helper function to parse growth percentage
function parseGrowth(growth: string): number {
  const match = growth.match(/([+-]?\d+(?:\.\d+)?)/);
  return match ? parseFloat(match[1]) : 0;
}

// Helper function to get growth color and variant
function getGrowthVariant(growth: string): {
  color: string;
  label: string;
} {
  const value = parseGrowth(growth);

  if (value >= 1000) return {
    color: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300',
    label: 'Explosive'
  };
  if (value >= 500) return {
    color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    label: 'Very High'
  };
  if (value >= 100) return {
    color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    label: 'High'
  };
  if (value >= 50) return {
    color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    label: 'Moderate'
  };
  if (value >= 0) return {
    color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
    label: 'Low'
  };
  return {
    color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
    label: 'Declining'
  };
}

// Helper function to parse volume (remove 'K', 'M' suffixes for comparison)
function parseVolume(volume: string): number {
  const match = volume.match(/(\d+(?:\.\d+)?)\s*([KM]?)/i);
  if (!match) return 0;

  const num = parseFloat(match[1]);
  const suffix = match[2]?.toUpperCase();

  if (suffix === 'M') return num * 1000000;
  if (suffix === 'K') return num * 1000;
  return num;
}

export function TrendKeywordCards({ keywords }: TrendKeywordCardsProps) {
  // Sort keywords by growth (descending)
  const sortedKeywords = [...keywords].sort((a, b) =>
    parseGrowth(b.growth) - parseGrowth(a.growth)
  );

  // Calculate total volume (for summary)
  const totalVolume = keywords.reduce((sum, k) => sum + parseVolume(k.volume), 0);
  const avgGrowth = keywords.length > 0
    ? keywords.reduce((sum, k) => sum + parseGrowth(k.growth), 0) / keywords.length
    : 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Search className="h-5 w-5 text-muted-foreground" />
          <CardTitle>Trending Keywords</CardTitle>
        </div>
        <CardDescription>
          {keywords.length} keyword{keywords.length !== 1 ? 's' : ''} tracked •{' '}
          {totalVolume >= 1000000
            ? `${(totalVolume / 1000000).toFixed(1)}M`
            : `${(totalVolume / 1000).toFixed(1)}K`} total volume •{' '}
          {avgGrowth >= 0 ? '+' : ''}{avgGrowth.toFixed(0)}% avg growth
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {sortedKeywords.map(({ keyword, volume, growth }, index) => {
            const { color, label } = getGrowthVariant(growth);
            const growthValue = parseGrowth(growth);
            const isTopKeyword = index === 0;

            return (
              <Card key={keyword} className={`relative overflow-hidden ${isTopKeyword ? 'border-2 border-primary' : ''}`}>
                <CardContent className="p-4">
                  {/* Top Keyword Badge */}
                  {isTopKeyword && (
                    <div className="absolute top-2 right-2">
                      <Badge variant="default" className="text-[10px] px-2 py-0">
                        Top Growth
                      </Badge>
                    </div>
                  )}

                  {/* Keyword Title */}
                  <div className="flex items-start gap-2 mb-3">
                    <TrendingUp className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                    <h4 className="font-semibold text-sm leading-tight line-clamp-2">
                      {keyword}
                    </h4>
                  </div>

                  {/* Volume */}
                  <div className="flex items-center gap-2 mb-2">
                    <BarChart3 className="h-3.5 w-3.5 text-muted-foreground" />
                    <div className="flex items-baseline gap-1">
                      <span className="text-2xl font-bold">{volume}</span>
                      <span className="text-xs text-muted-foreground">volume</span>
                    </div>
                  </div>

                  {/* Growth Badge */}
                  <div className="flex items-center gap-2">
                    <Badge className={`${color} flex-1 justify-center`}>
                      {growth} growth
                    </Badge>
                  </div>

                  {/* Growth Label */}
                  <div className="mt-2 text-center">
                    <span className="text-xs text-muted-foreground">{label} Growth</span>
                  </div>

                  {/* Visual Bar Indicator */}
                  <div className="mt-3">
                    <div className="h-1.5 w-full rounded-full bg-muted">
                      <div
                        className={`h-1.5 rounded-full transition-all ${
                          growthValue >= 1000 ? 'bg-emerald-500' :
                          growthValue >= 500 ? 'bg-green-500' :
                          growthValue >= 100 ? 'bg-blue-500' :
                          growthValue >= 50 ? 'bg-yellow-500' :
                          growthValue >= 0 ? 'bg-gray-400' :
                          'bg-red-500'
                        }`}
                        style={{
                          width: `${Math.min(100, Math.max(5, (growthValue / 2000) * 100))}%`
                        }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {keywords.length === 0 && (
          <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
            No trending keywords available
          </div>
        )}
      </CardContent>
    </Card>
  );
}
