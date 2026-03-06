export default function HomeLoading() {
  return (
    <div className="min-h-screen">
      {/* Hero skeleton */}
      <section className="hero-gradient py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="h-16 bg-muted/40 rounded-xl w-3/4 mx-auto mb-6 animate-pulse" />
          <div className="h-6 bg-muted/40 rounded w-1/2 mx-auto mb-8 animate-pulse" />
          <div className="flex justify-center gap-4">
            <div className="h-12 w-36 bg-muted/40 rounded-lg animate-pulse" />
            <div className="h-12 w-36 bg-muted/30 rounded-lg animate-pulse" />
          </div>
        </div>
      </section>

      {/* Insights skeleton */}
      <section className="py-16 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="h-8 bg-muted rounded w-40 mb-2 animate-pulse" />
          <div className="h-4 bg-muted rounded w-64 mb-8 animate-pulse" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-xl border bg-card p-5 h-56 animate-pulse">
                <div className="h-4 bg-muted rounded w-3/4 mb-3" />
                <div className="h-3 bg-muted rounded w-full mb-2" />
                <div className="h-3 bg-muted rounded w-5/6 mb-4" />
                <div className="h-2 bg-muted rounded-full w-full" />
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
