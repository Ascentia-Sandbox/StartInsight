import { redirect } from 'next/navigation';
import Link from 'next/link';
import { createClient } from '@/lib/supabase/server';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default async function WorkspacePage() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect('/auth/login');
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">My Workspace</h1>
            <p className="text-muted-foreground mt-2">
              Your saved insights and research analyses
            </p>
          </div>
          <Link href="/insights">
            <Button>Browse Insights</Button>
          </Link>
        </div>

        {/* Tabs - Saved Insights / Ratings / Research */}
        <div className="flex gap-4 border-b mb-8">
          <button className="pb-2 px-1 border-b-2 border-primary text-primary font-medium">
            Saved Insights
          </button>
          <button className="pb-2 px-1 text-muted-foreground hover:text-foreground">
            My Ratings
          </button>
          <button className="pb-2 px-1 text-muted-foreground hover:text-foreground">
            Research History
          </button>
        </div>

        {/* Empty State */}
        <Card>
          <CardContent className="p-12">
            <div className="text-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-16 w-16 mx-auto text-muted-foreground mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"
                />
              </svg>
              <h3 className="text-lg font-semibold mb-2">No saved insights yet</h3>
              <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
                Start building your workspace by saving insights that interest you.
                Click the bookmark icon on any insight to save it here.
              </p>
              <Link href="/insights">
                <Button>Browse Insights</Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Instructions */}
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <span className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-sm">1</span>
                Browse Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Explore AI-analyzed market opportunities from Reddit, Product Hunt, and Google Trends.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <span className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-sm">2</span>
                Save &amp; Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Save insights that interest you and rate them to help improve recommendations.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <span className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-sm">3</span>
                Research &amp; Build
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Run AI research on your ideas and use build tools to create brand assets.
              </CardDescription>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
