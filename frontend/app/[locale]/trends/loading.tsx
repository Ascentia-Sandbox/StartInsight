export default function TrendsLoading() {
  return (
    <div className="min-h-screen py-8 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="h-8 bg-muted rounded w-40 mb-2 animate-pulse" />
        <div className="h-4 bg-muted rounded w-64 mb-8 animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="rounded-xl border bg-card p-4 h-32 animate-pulse">
              <div className="h-4 bg-muted rounded w-3/4 mb-2" />
              <div className="h-3 bg-muted rounded w-1/2 mb-4" />
              <div className="h-8 bg-muted rounded w-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
