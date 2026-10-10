# Security policy

## Reporting a vulnerability

Please do not report exploitable vulnerabilities in a public issue. Use GitHub's private vulnerability reporting for this repository if it is enabled. If private reporting is unavailable, contact the repository owner through their GitHub profile and include only the details needed to investigate.

## API credentials

The CLI reads provider credentials from environment variables. The web app accepts a key for the active request and sends it from the Streamlit server to the chosen model provider. Keep keys and tokens out of source files, shared public app configuration, issue reports, pull requests, screenshots, and commit history. If a credential is exposed, revoke it with its provider and create a replacement.
