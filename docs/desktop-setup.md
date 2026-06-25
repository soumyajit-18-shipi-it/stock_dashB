# Desktop Setup

The desktop wrapper uses Tauri configuration around the existing React/Vite frontend. Tauri keeps the desktop package small and lets the same frontend talk to either a local FastAPI backend or a deployed backend.

## Local Web Development

```bash
python run.py
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Tauri Desktop Development

Prerequisites:

- Node.js 18+
- Rust stable toolchain
- Tauri CLI, invoked through `npx @tauri-apps/cli@latest`
- Running backend: either `python run.py` locally or a deployed backend configured through `VITE_API_URL`

```bash
cd frontend
npm install
npm run desktop:dev
```

## Platform Build Notes

Linux:

- Install WebKitGTK and build tools required by Tauri for your distribution.
- Run `cd frontend && npm run desktop:build`.

macOS:

- Build on macOS.
- Install Xcode command line tools and Rust.
- Run `cd frontend && npm run desktop:build`.

Windows:

- Build on Windows.
- Ensure Microsoft Edge WebView2 Runtime and Rust are installed.
- For Windows PowerShell:
  ```powershell
  Set-Location frontend
  npm run desktop:build
  Set-Location ..
  ```
- For cmd.exe:
  ```cmd
  cmd /c "cd frontend && npm run desktop:build"
  ```

Native desktop packages are OS-specific; CI can validate configuration, but signed installers must be produced on the target OS with the appropriate signing credentials.

## Docker Runtime

```bash
docker compose up --build
```

The container exposes FastAPI on `http://localhost:8000`. The Docker image builds the frontend assets and includes them in the production image, while the API remains available under `/api/v1`.
