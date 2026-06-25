import { lazy, Suspense } from 'react';

import type { PlotParams } from 'react-plotly.js';

const Plot = lazy(() => import('react-plotly.js'));

export function LazyPlot(props: PlotParams) {
  return (
    <Suspense
      fallback={
        <div className="flex h-full w-full items-center justify-center text-sm text-slate-400">
          Loading chart...
        </div>
      }
    >
      <Plot {...props} />
    </Suspense>
  );
}
