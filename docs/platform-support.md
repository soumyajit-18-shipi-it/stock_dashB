# Platform Support

Stock Intelligence Dashboard is a React/Vite web app backed by FastAPI. The repository now contains support paths for web, PWA, Docker, desktop wrappers, and mobile wrappers.

## Desktop

| Platform | Support | Evidence |
| --- | --- | --- |
| GNU/Linux | Supported through browser, Docker, and Tauri desktop wrapper configuration. Native build must be run on a Linux machine with Tauri system dependencies installed. | `Dockerfile`, `docker-compose.yml`, `frontend/src-tauri/tauri.conf.json` |
| macOS | Supported through browser and Tauri desktop wrapper configuration. Native `.app`/`.dmg` builds must be run on macOS with Xcode command line tools and Tauri dependencies. | `frontend/src-tauri/tauri.conf.json` |
| Windows | Supported through browser and Tauri desktop wrapper configuration. Native installer builds must be run on Windows with WebView2 and Rust/Tauri prerequisites. | `frontend/src-tauri/tauri.conf.json` |
| Docker/container runtime | Supported. The Docker image builds the Vite frontend and serves the FastAPI backend. | `Dockerfile`, `docker-compose.yml` |

## Mobile

| Platform | Support | Evidence |
| --- | --- | --- |
| Android | Supported as responsive mobile web/PWA. Capacitor configuration is present; native Android project generation requires running `npx @capacitor/cli@latest add android` on a machine with Android Studio and SDK. | `frontend/public/manifest.webmanifest`, `frontend/public/sw.js`, `frontend/capacitor.config.json` |
| iOS | Supported as responsive mobile web/PWA. Capacitor configuration is present; native iOS project generation requires macOS with Xcode and `npx @capacitor/cli@latest add ios`. | `frontend/public/manifest.webmanifest`, `frontend/public/sw.js`, `frontend/capacitor.config.json` |
| Other mobile | Installable PWA and responsive mobile browser support. | `frontend/index.html`, `frontend/public/offline.html`, Tailwind responsive UI classes |

## Web Browsers

The app targets modern evergreen browsers supported by Vite and React 18: Chrome, Edge, Firefox, and Safari. Browser-specific certification is not stored in the repo; run the Playwright or manual QA checklist before claiming production certification for a browser/version.

## Backend Connectivity

The frontend reads `VITE_API_URL`. In local development it defaults to `http://localhost:8000/api/v1`; on Vercel it can use `/api/v1` with rewrites to the deployed backend. Desktop and mobile wrappers use the same frontend environment variable, so they can point to either a local backend or a deployed backend.
