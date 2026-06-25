# Accessibility and Performance

## Low-Bandwidth Strategy

- The PWA service worker caches the app shell, static assets, and successful GET API responses.
- React Query keeps API data fresh for five minutes and in memory for thirty minutes to avoid repeated network calls.
- The UI includes a Low data toggle in the navigation bar. It records the preference in `localStorage` and surfaces a status banner.
- Plotly chart rendering is lazy-loaded through `frontend/src/components/LazyPlot.tsx` so the largest chart dependency is not part of the first dashboard shell.
- Backend market data uses TTL caching in `backend/data/provider.py`: shorter during market hours and longer after close.
- The app exposes a plain offline fallback page at `frontend/public/offline.html`.

## Offline Behavior

Offline support is partial by design. Cached screens and static UI can load offline. Fresh stock prices, predictions, AI chat, and report generation need a working backend and external market/AI providers.

## Static Assets and Compression

Vite production builds produce minified static assets. Compression should be enabled by the hosting platform or reverse proxy:

- Vercel enables compression for static assets.
- Nginx/Apache deployments should enable gzip or Brotli.
- Docker deployments should run behind a reverse proxy when public-facing compression and TLS termination are required.

## Device Compatibility

The frontend uses responsive Tailwind layouts and a mobile viewport meta tag. The minimum supported width in CSS is 320px. Low-end device certification requires running Lighthouse and manual checks on representative devices.

## Performance Commands

```bash
cd frontend
npm run build:pwa
npm run preview
npm run lighthouse:local
```

The Lighthouse command requires network access for `npx lighthouse` if Lighthouse is not already installed. Save generated reports under `reports/lighthouse/`.

## Bundle Inspection

```bash
cd frontend
npm run build
```

Use the generated `dist/assets` sizes as the baseline. If chart bundles become too large, split Plotly charts behind dynamic imports and keep non-chart screens lightweight.

Latest local PWA build evidence:

- Before chart code-splitting, the main JavaScript chunk was about 5.85 MB minified.
- After `LazyPlot`, the initial app chunk is about 936 KB minified and Plotly is deferred into a separate async chunk of about 4.87 MB.
- The build still warns about large chunks because Plotly itself is large; the important change is that the chart bundle is no longer part of the first app shell.
