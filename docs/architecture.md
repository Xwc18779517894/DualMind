# How DualMind works

```text
Browser or app window
  HTML / CSS / JavaScript (no build step)
          ↓ authenticated localhost requests
dualmind_web.py — settings, background job, session actions
          ↓
dualmind.py — bounded conversation engine
   ├─ Codex CLI → existing ChatGPT login, read-only, low reasoning
   └─ google-genai → Gemini API, key supplied by local backend
          ↓
Local JSON history + Windows DPAPI credential storage
```

`credentials.py` handles credentials only. The frontend never receives the saved Gemini key. The server binds to `127.0.0.1` and rejects unexpected Host/Origin values. Static pages set an HttpOnly session cookie; the old token header remains supported for local clients.

The engine has three paths:

- **Chat/work, together:** Codex responds first; Gemini receives that answer as peer content and can build on it. This trades independent first impressions for natural interaction. It is always at most two calls.
- **Chat/work, independent:** Both receive the same history snapshot. Neither sees the other's current answer.
- **Discussion:** Both independently respond in round one. Later rounds receive both previous answers. A final Gemini report preserves disagreements and distinguishes missing evidence. Calls are capped at `2 × rounds + 1`.

The latest 12 messages and approximately 16,000 characters are included as context. DualMind does not make extra summarization calls. Provider errors never trigger automatic retries or a paid fallback. A failure preserves earlier replies. The UI polls job status; responses appear when each call finishes, not token by token.

Session management is deliberately small: JSON files are saved atomically, deletion moves them to a local trash directory, and restore refuses to overwrite an existing conversation. Editing or regeneration builds a branch rather than rewriting the original. A running session cannot be deleted, renamed or forked.

Windows is the supported desktop platform. The web server and engine use the standard library; the only required Python dependency is `google-genai`. Node is needed for the standard npm installation of Codex CLI, but not for building the frontend.

Legacy data is retained if the old `E:\CodexWork\2026-10-11\DualMind` directory exists. Fresh Windows installations use `%LOCALAPPDATA%\DualMind`. `DUALMIND_DATA_DIR` overrides either choice. No local data is included in the source repository.
