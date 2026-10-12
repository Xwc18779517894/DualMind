# Security and privacy

DualMind is a **single-user localhost application**, not an Internet-facing service. Keep it bound to `127.0.0.1`; do not port-forward it or deploy this server as a shared website.

- Gemini credentials entered in the app are protected with Windows DPAPI and are not returned to the frontend.
- Local session cookies are HttpOnly and SameSite=Strict. Requests validate Host and Origin.
- Model content is escaped before rendering. Links are restricted to HTTP(S); code is displayed, never executed by the frontend.
- Conversation history, trash and browser drafts are stored locally as plaintext. Messages you send are transmitted to the selected model providers. Local storage does not mean offline inference.
- Codex runs with a read-only sandbox and receives no Gemini API key. DualMind does not promise a tool-free Codex runtime: CLI configuration and installed extensions still matter.
- No telemetry is built into DualMind. Provider-side logging and retention follow their respective terms.

Never paste secrets into chat. Before sharing logs or screenshots, remove credentials and personal conversation content. Do not put a secret in a public issue; use the repository's private vulnerability reporting feature if available, or open a minimal issue requesting a private contact channel without exploit details.
