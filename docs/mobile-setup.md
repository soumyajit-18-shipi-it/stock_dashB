# Mobile Setup

The project supports mobile in two layers:

1. Responsive installable PWA for Android, iOS, and mobile browsers.
2. Capacitor configuration for native Android/iOS wrapper projects.

## PWA

PWA evidence:

- `frontend/public/manifest.webmanifest`
- `frontend/public/sw.js`
- `frontend/public/offline.html`
- mobile metadata in `frontend/index.html`

Build and preview:

```bash
cd frontend
npm install
npm run build:pwa
npm run preview
```

Install from Chrome/Edge on Android or desktop using the browser install prompt. On iOS, open the site in Safari and use Add to Home Screen.

## Offline Behavior

The service worker caches the app shell and static assets. API GET responses are cached after successful network responses and may be reused during network failures. Fresh market data, AI chat, report generation, and new predictions still require backend/network access.

## Android Wrapper

Prerequisites:

- Android Studio
- Android SDK and emulator/device
- Java toolchain compatible with the installed Android Gradle Plugin

Commands:

```bash
cd frontend
npm install
npm run build:pwa
npx @capacitor/cli@latest add android
npm run mobile:sync
npm run mobile:android
```

The `android/` folder is generated locally by Capacitor and is not committed until the team decides to maintain native project files in source control.

## iOS Wrapper

Prerequisites:

- macOS
- Xcode
- Apple developer account for signed device/App Store builds

Commands:

```bash
cd frontend
npm install
npm run build:pwa
npx @capacitor/cli@latest add ios
npm run mobile:sync
npm run mobile:ios
```

The `ios/` folder is generated locally by Capacitor and requires macOS/Xcode for builds.
