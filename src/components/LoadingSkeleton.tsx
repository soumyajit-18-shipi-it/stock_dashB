export function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-12 bg-slate-700 rounded-xl" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="h-96 bg-slate-700 rounded-xl" />
          <div className="h-48 bg-slate-700 rounded-xl" />
        </div>
        <div className="space-y-4">
          <div className="h-64 bg-slate-700 rounded-xl" />
          <div className="h-48 bg-slate-700 rounded-xl" />
        </div>
      </div>
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="h-96 bg-slate-800/50 rounded-xl border border-slate-700 flex items-center justify-center">
      <div className="animate-pulse flex flex-col items-center gap-4">
        <div className="h-8 w-48 bg-slate-700 rounded" />
        <div className="h-64 w-80 bg-slate-700 rounded" />
      </div>
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6 animate-pulse">
      <div className="h-6 w-32 bg-slate-700 rounded mb-4" />
      <div className="space-y-3">
        <div className="h-4 w-full bg-slate-700 rounded" />
        <div className="h-4 w-3/4 bg-slate-700 rounded" />
        <div className="h-4 w-1/2 bg-slate-700 rounded" />
      </div>
    </div>
  );
}
