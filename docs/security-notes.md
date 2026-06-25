# Security Audit Notes

This document captures the security state of the frontend Node.js packages and dependency vulnerabilities.

## Scan and Audit Summary

A dependency audit scan was run on the React frontend project.

- **Vulnerabilities Before Audit Fix:** 6 vulnerabilities (4 moderate, 2 high)
- **Vulnerabilities Remaining (Post Safe Fixes):** 4 vulnerabilities (3 moderate, 1 high)

## Applied Fixes

Run command:
```powershell
Set-Location frontend
npm audit fix
Set-Location ..
```

This updated 29 packages and successfully resolved the production runtime vulnerabilities in:
- `undici` (high severity TLS certificate validation bypass, HTTP header injection, WebSocket client denial of service, and cross-origin request routing).
- `dompurify` (moderate severity ALLOWED_ATTR pollution bypass).

## Remaining Vulnerabilities

| Dependency | Severity | Vulnerability Details | Risk | Reason for Not Force-Fixing |
| :--- | :--- | :--- | :--- | :--- |
| `esbuild` / `vite` | Moderate / High | Dev server request access / arbitrary file read on Windows (GHSA-67mh-4wv8-2f99, GHSA-g7r4-m6w7-qqqr) | Low. Only active when running the development server locally. | Requires `npm audit fix --force`, which upgrades Vite to version 8.1.0, representing a major breaking change. |
| `js-yaml` / `depcheck` | Moderate | Quadratic-complexity DoS in YAML merge key handling (GHSA-h67p-54hq-rp68) | Low. Only used during static dead dependency check tasks. | Requires `npm audit fix --force`, which upgrades `depcheck` to version 0.4.7, representing a major breaking change. |
