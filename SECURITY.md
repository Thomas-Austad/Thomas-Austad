# Security Policy

## Scope

The Talent Advisor Platform processes resumes, employment histories, contact information, compensation preferences, job listings, generated application documents, and application approvals. Treat this information as confidential.

## Reporting a vulnerability

Do not open a public issue containing vulnerability details, credentials, candidate data, or proof-of-concept data from a real user.

For a personal repository, enable GitHub private vulnerability reporting and use it for reports. If private reporting is unavailable, create a private communication channel before sharing details.

Include:

- affected version or commit;
- component and configuration;
- reproduction steps using synthetic data;
- expected and observed behavior;
- impact assessment;
- suggested remediation, when known.

## Response priorities

Immediately rotate exposed credentials and suspend affected write integrations. Preserve minimal audit evidence without copying sensitive records into tickets or chat.

Highest-priority issues include:

- authentication or object-level authorization bypass;
- cross-user data exposure;
- secret or token disclosure;
- unauthorized job submission or messaging;
- prompt injection that causes tool use or data exfiltration;
- SSRF, SQL injection, command injection, path traversal, XSS, or unsafe file processing;
- fabricated or altered candidate claims presented as factual;
- sensitive information appearing in logs, analytics, fixtures, or model traces.

## Secure repository settings

Enable where available:

- secret scanning and push protection;
- Dependabot alerts, security updates, and version updates;
- dependency review on pull requests;
- CodeQL/default code scanning;
- branch protection with required reviews and passing checks;
- protected deployment environments;
- private vulnerability reporting.

Never store real candidate data, production secrets, database dumps, or generated application documents in the repository.
