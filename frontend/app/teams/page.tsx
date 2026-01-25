'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Users, Share2, MessageSquare, Shield } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchTeams, createTeam } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { Team } from '@/lib/types';

export default function TeamsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [teamName, setTeamName] = useState('');
  const [teamDescription, setTeamDescription] = useState('');

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/auth/login?redirectTo=/teams');
        return;
      }

      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, [router]);

  // Fetch teams
  const { data: teams, isLoading } = useQuery({
    queryKey: ['teams', accessToken],
    queryFn: () => fetchTeams(accessToken!),
    enabled: !!accessToken,
  });

  // Create team mutation
  const createTeamMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      createTeam(accessToken!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      setShowCreateModal(false);
      setTeamName('');
      setTeamDescription('');
    },
  });

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-8 w-8 text-primary mx-auto" />
          <p className="mt-2 text-muted-foreground">Loading teams...</p>
        </div>
      </div>
    );
  }

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    createTeamMutation.mutate({
      name: teamName,
      description: teamDescription || undefined,
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Teams</h1>
            <p className="text-muted-foreground mt-2">
              Collaborate with your team on market research
            </p>
          </div>
          <Button onClick={() => setShowCreateModal(true)}>Create Team</Button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="animate-spin h-8 w-8 text-primary" />
          </div>
        ) : !teams || teams.length === 0 ? (
          // Empty State
          <Card>
            <CardContent className="p-12">
              <div className="text-center">
                <Users className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No teams yet</h3>
                <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
                  Create a team to collaborate with colleagues on market research and share
                  insights.
                </p>
                <Button onClick={() => setShowCreateModal(true)}>Create Your First Team</Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          // Teams List
          <div className="space-y-4">
            {teams.map((team: Team) => (
              <Card key={team.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                  <div>
                    <CardTitle>{team.name}</CardTitle>
                    <CardDescription>
                      {team.member_count} member{team.member_count !== 1 ? 's' : ''}
                      {team.description && ` - ${team.description}`}
                    </CardDescription>
                  </div>
                  <Button variant="outline">Manage</Button>
                </CardHeader>
              </Card>
            ))}
          </div>
        )}

        {/* Features Info */}
        <div className="mt-12 grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Share2 className="h-5 w-5 text-primary" />
                Share Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Share valuable insights with team members for collaborative analysis
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-primary" />
                Discuss & Comment
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Add notes and comments to shared insights for team discussion
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary" />
                Role-Based Access
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Control who can view, edit, and manage team resources
              </CardDescription>
            </CardContent>
          </Card>
        </div>

        {/* Create Team Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div
              className="absolute inset-0 bg-black/50"
              onClick={() => setShowCreateModal(false)}
            />
            <Card className="relative z-10 w-full max-w-md">
              <CardHeader>
                <CardTitle>Create New Team</CardTitle>
                <CardDescription>
                  Start collaborating with your colleagues
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreateTeam} className="space-y-4">
                  <div className="space-y-2">
                    <label htmlFor="teamName" className="text-sm font-medium">
                      Team Name
                    </label>
                    <Input
                      id="teamName"
                      value={teamName}
                      onChange={(e) => setTeamName(e.target.value)}
                      placeholder="e.g., Marketing Team"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <label htmlFor="teamDescription" className="text-sm font-medium">
                      Description (optional)
                    </label>
                    <Input
                      id="teamDescription"
                      value={teamDescription}
                      onChange={(e) => setTeamDescription(e.target.value)}
                      placeholder="What is this team for?"
                    />
                  </div>
                  <div className="flex gap-2 justify-end">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setShowCreateModal(false)}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" disabled={createTeamMutation.isPending}>
                      {createTeamMutation.isPending && (
                        <Loader2 className="animate-spin h-4 w-4 mr-2" />
                      )}
                      Create Team
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
