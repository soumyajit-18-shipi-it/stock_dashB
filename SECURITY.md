# Security Policy

## Supported Versions

We currently support the following versions of Stock Intelligence Dashboard with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of our project seriously. If you believe you have found a security vulnerability, please report it to us responsibly.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please send an email to `security@example.com` (replace with actual contact) with a description of the vulnerability and steps to reproduce it.

### What to expect

*   We will acknowledge receipt of your report within 48 hours.
*   We will investigate and confirm the vulnerability.
*   We will provide an estimated timeline for a fix.
*   We will notify you once the vulnerability is patched.

## Responsible Disclosure

We ask that you follow responsible disclosure guidelines:

*   Give us a reasonable amount of time to fix the issue before making it public.
*   Do not exploit the vulnerability for any reason.
*   Provide enough information for us to reproduce the issue.

## Security Practices

*   **Secret Scanning:** We use Gitleaks to prevent secrets from being committed.
*   **Dependency Audits:** We regularly audit our dependencies for known vulnerabilities.
*   **Static Analysis:** We use Bandit and Semgrep to identify potential security issues in our code.
