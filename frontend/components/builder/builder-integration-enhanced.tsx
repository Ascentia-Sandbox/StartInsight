'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, Loader2, Code, Rocket, Sparkles, Check, X } from 'lucide-react';
import Link from 'next/link';
import { config } from '@/lib/env';

// ============================================================================
// TYPES
// ============================================================================

interface BuilderPlatform {
  id: string;
  name: string;
  description: string;
  oauth_configured: boolean;
  features: string[];
}

interface BuilderProject {
  platform: string;
  project_id: string | null;
  project_url: string;
  status: 'success' | 'pending' | 'failed';
  error: string | null;
  created_at: string;
}

interface BuilderIntegrationProps {
  insightId: string;
  problemStatement: string;
  proposedSolution: string;
}

// ============================================================================
// PLATFORM ICONS
// ============================================================================

const PlatformIcon = ({ platform }: { platform: string }) => {
  switch (platform) {
    case 'lovable':
      return <Rocket className="h-5 w-5 text-purple-500" />;
    case 'replit':
      return <Code className="h-5 w-5 text-orange-500" />;
    case 'v0':
      return <Sparkles className="h-5 w-5 text-blue-500" />;
    default:
      return <Code className="h-5 w-5" />;
  }
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function BuilderIntegrationEnhanced({
  insightId,
  problemStatement,
  proposedSolution,
}: BuilderIntegrationProps) {
  const apiUrl = config.apiUrl;

  const [platforms, setPlatforms] = useState<BuilderPlatform[]>([]);
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState<string | null>(null); // Platform ID being built
  const [projects, setProjects] = useState<Record<string, BuilderProject>>({}); // Platform ID -> Project

  // Fetch available platforms
  useEffect(() => {
    fetchPlatforms();
  }, []);

  const fetchPlatforms = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/build/platforms`);
      if (response.ok) {
        const data = await response.json();
        setPlatforms(data.platforms);
      }
    } catch (error) {
      console.error('Error fetching platforms:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBuildProject = async (platformId: string) => {
    setBuilding(platformId);

    try {
      // Get OAuth URL and redirect
      const redirectUri = `${window.location.origin}/api/build/${platformId}/callback`;
      const response = await fetch(
        `${apiUrl}/api/build/${platformId}/auth?insight_id=${insightId}&redirect_uri=${encodeURIComponent(redirectUri)}`
      );

      if (response.ok) {
        const data = await response.json();
        // For OAuth flow, redirect to authorization URL
        // window.location.href = data.auth_url;

        // For now, show message about OAuth setup needed
        alert(`OAuth setup required for ${platformId}. Please configure ${platformId.toUpperCase()}_CLIENT_ID and ${platformId.toUpperCase()}_CLIENT_SECRET environment variables.`);
      } else {
        const error = await response.json();
        alert(`Failed to start ${platformId} OAuth: ${error.detail}`);
      }
    } catch (error) {
      console.error(`Error building with ${platformId}:`, error);
      alert(`Failed to build with ${platformId}. Please try again.`);
    } finally {
      setBuilding(null);
    }
  };

  const handleBuildV0 = async () => {
    setBuilding('v0');

    try {
      const response = await fetch(`${apiUrl}/api/build/v0?insight_id=${insightId}`, {
        method: 'POST',
      });

      if (response.ok) {
        const project: BuilderProject = await response.json();
        setProjects((prev) => ({ ...prev, v0: project }));

        if (project.status === 'success') {
          // Open v0.dev in new tab
          window.open(project.project_url, '_blank');
        } else {
          alert(project.error || 'v0 generation is experimental and not yet fully implemented.');
        }
      } else {
        const error = await response.json();
        alert(`v0 generation failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error generating v0 design:', error);
      alert('Failed to generate v0 design. Please try again.');
    } finally {
      setBuilding(null);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Rocket className="h-5 w-5" />
            Build This Idea
          </CardTitle>
          <CardDescription>
            Create a prototype with AI-powered builder platforms
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {platforms.map((platform) => (
              <Card key={platform.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <PlatformIcon platform={platform.id} />
                    {platform.oauth_configured ? (
                      <Badge variant="default" className="text-xs">
                        <Check className="h-3 w-3 mr-1" />
                        Configured
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="text-xs">
                        <X className="h-3 w-3 mr-1" />
                        Setup Required
                      </Badge>
                    )}
                  </div>
                  <CardTitle className="text-lg mt-2">{platform.name}</CardTitle>
                  <CardDescription className="text-sm">
                    {platform.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex flex-wrap gap-1">
                    {platform.features.slice(0, 3).map((feature, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                  </div>

                  {projects[platform.id] ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        {projects[platform.id].status === 'success' ? (
                          <Badge variant="default">
                            <Check className="h-3 w-3 mr-1" />
                            Created
                          </Badge>
                        ) : projects[platform.id].status === 'failed' ? (
                          <Badge variant="destructive">
                            <X className="h-3 w-3 mr-1" />
                            Failed
                          </Badge>
                        ) : (
                          <Badge variant="secondary">
                            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                            Pending
                          </Badge>
                        )}
                      </div>
                      {projects[platform.id].status === 'success' && (
                        <Link href={projects[platform.id].project_url} target="_blank">
                          <Button variant="outline" size="sm" className="w-full">
                            <ExternalLink className="h-4 w-4 mr-2" />
                            Open Project
                          </Button>
                        </Link>
                      )}
                      {projects[platform.id].error && (
                        <p className="text-xs text-red-500">{projects[platform.id].error}</p>
                      )}
                    </div>
                  ) : (
                    <Button
                      onClick={() =>
                        platform.id === 'v0' ? handleBuildV0() : handleBuildProject(platform.id)
                      }
                      disabled={building !== null || !platform.oauth_configured}
                      className="w-full"
                      size="sm"
                    >
                      {building === platform.id && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      {platform.oauth_configured ? 'Build Prototype' : 'OAuth Setup Required'}
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Setup Instructions */}
      {platforms.some((p) => !p.oauth_configured) && (
        <Card className="border-yellow-500/50">
          <CardHeader>
            <CardTitle className="text-sm">Setup Required</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>
              To use builder integrations, configure OAuth credentials in your environment:
            </p>
            <ul className="list-disc list-inside space-y-1">
              {!platforms.find((p) => p.id === 'lovable')?.oauth_configured && (
                <li>
                  <strong>Lovable:</strong> Set <code>LOVABLE_CLIENT_ID</code> and{' '}
                  <code>LOVABLE_CLIENT_SECRET</code>
                </li>
              )}
              {!platforms.find((p) => p.id === 'replit')?.oauth_configured && (
                <li>
                  <strong>Replit:</strong> Set <code>REPLIT_CLIENT_ID</code> and{' '}
                  <code>REPLIT_CLIENT_SECRET</code>
                </li>
              )}
            </ul>
            <p className="text-xs pt-2">
              ℹ️ v0.dev doesn't require OAuth (uses browser automation)
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
