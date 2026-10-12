# DualMind

**Two AI perspectives. One shared space.**

[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md)

[![Offline checks](https://github.com/Xwc18779517894/DualMind/actions/workflows/tests.yml/badge.svg)](https://github.com/Xwc18779517894/DualMind/actions/workflows/tests.yml) ![Windows](https://img.shields.io/badge/platform-Windows-64748b) ![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab) [![MIT](https://img.shields.io/badge/license-MIT-c26943)](LICENSE)

Talking to one AI can help you think. Bringing a second perspective into the same conversation can reveal alternatives, missing assumptions and useful questions. **DualMind brings you, Codex and Gemini into a local workspace** for everyday conversation, shared work and deliberate discussion.

It does not make disagreement a sport or treat agreement as proof. You decide when the conversation continues.

![DualMind dark workspace](docs/images/workspace-dark.png)

*Real interface, isolated mock conversation. The UI currently uses Chinese labels.*

## What you can do

| | Behavior |
|---|---|
| Natural group chat | Two replies per send; the second AI can build on the first. No fixed argument template. |
| Independent perspectives | Switch to independent answers when you want separate first impressions. |
| Work together | Plan, write, review ideas and produce code; mention one AI to continue with it. |
| Deliberate discussion | Independent first round, limited follow-up rounds, then a five-part report. |
| Manage conversations | Full-text search, pin, rename, duplicate, soft-delete and restore. |
| Revise safely | Edit a message or regenerate one AI in a new branch; keep the original. |
| Change models | Fetch Gemini's model list, select or enter a model, and override Codex's CLI model. |
| Read comfortably | Warm light/dark/system themes, centered responsive composer, Markdown and code copying. |
| Keep useful work | Browser drafts, text-file context, copy and Markdown export. |

### What makes it small

The interface is plain HTML, CSS and JavaScript. A Python localhost server connects the existing Codex CLI and official Gemini SDK. No frontend build, Electron, cloud deployment or additional AI account is required. Local storage is not offline inference: selected providers receive the messages you send.

## Quick start · Windows

### 1. Install prerequisites

- [Python 3.11 or newer](https://www.python.org/downloads/windows/). Python 3.13.2 is the locally verified version.
- [Codex CLI](https://developers.openai.com/codex/cli/), installed and logged in with an eligible ChatGPT account. The npm route requires [Node.js LTS](https://nodejs.org/).
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

```powershell
npm install -g @openai/codex
codex login
```

Clone the source or download and extract the GitHub ZIP:

```powershell
git clone https://github.com/Xwc18779517894/DualMind.git
cd DualMind
```

### 2. Install the one Python dependency

Double-click `setup.cmd`. It creates `.venv` in the project and installs `requirements.txt`. Or use PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Open and configure

- Double-click **启动DualMind.cmd** for a standalone browser app window.
- Double-click **浏览器打开DualMind.cmd** for a normal browser tab.
- In **模型设置**, paste your Gemini key and save. A blank key field keeps the existing key.
- Select your Gemini model. The default is `gemini-3.5-flash-lite`, verified by one short request on the development account; availability and pricing depend on your own account.
- Keep Codex's model blank to use its CLI default, or enter an available model name. Locally cached model names are offered as suggestions, not an account-access guarantee.
- Start with one short message to **Gemini** only, then try both participants.

Manual startup:

```powershell
.\.venv\Scripts\python.exe dualmind_web.py --browser
```

The service prefers `http://127.0.0.1:8765/` and picks another port if busy. Settings show the actual address. A bookmarked URL requires the local service to be running. Closing a tab does not immediately stop the server; use **退出应用**, or let the idle server stop after about three minutes.

## Conversation controls

- **聊天:** natural conversation. **协作:** useful work. **深入讨论:** bounded discussion and a saved report.
- **一起聊:** the second AI sees the first AI's current answer. **各自回答:** the current answers stay independent. Neither setting starts an endless loop.
- `@Codex` or `@Gemini` at the start of a message selects one participant.
- Enter sends; Shift+Enter adds a line; Ctrl+Enter also sends. IME composition does not send.
- Ctrl+Shift+O starts a conversation; Ctrl+K searches history.
- Add or drag a UTF-8 text/code file into the composer: at most 64 KB per file and 12,000 characters total. Images/PDFs are not parsed in this release.
- Editing and regeneration create branches. Regeneration calls only the selected AI.

### Calls and limits

One participant: at most **1** generation call. Two participants: at most **2**. Discussion: **2 × rounds + 1**, with 1–3 rounds. No automatic retry or hidden model fallback. Listing Gemini models makes API metadata requests but does not generate text. No new paid subscription or billing configuration is enabled by DualMind; ChatGPT subscription limits and Gemini API pricing/quotas still apply.

A context window contains the latest 12 messages, approximately 16,000 characters. Important conclusions need evidence; the report is generated by Gemini and is not an independent fact-check. Codex runs read-only and produces text/code; this app does not provide general autonomous file editing. Responses appear after each model finishes, without token streaming.

## Proxy and troubleshooting

An optional **本地代理** field accepts a local HTTP/mixed proxy such as `http://127.0.0.1:7897`. It affects only Gemini and takes effect on save. Do not copy the example port blindly; use the port shown by your proxy software. An empty field uses the launch environment; `DUALMIND_GEMINI_PROXY` is supported. The bundled Clash launcher uses 7897 and must be adjusted if your port differs.

| Error | Next step |
|---|---|
| Key not configured | Save the key in the app, or set `GEMINI_API_KEY` before launching. Temporary shell variables are not inherited by Explorer. |
| 400 unsupported location | Check the actual network route and [supported regions](https://ai.google.dev/gemini-api/docs/available-regions). Changing a model does not guarantee a fix. |
| 404 model unavailable | Some listed models are retired or unavailable to your account. Choose another supported text model. |
| 429 quota/rate limit | Check API project usage and wait; do not repeatedly send to both AIs. |
| 503 high demand | The model is busy. Retry just Gemini later or explicitly choose another available model. |
| Disconnect or timeout | Check the proxy route and connectivity. The error alone does not prove the key is invalid. |
| Codex missing/auth error | Run `codex --version` and `codex login` in a terminal. Update the official CLI if `--ephemeral` is unsupported. |
| New backend does not appear | Finish the task, exit the app, and relaunch. A page refresh alone does not restart Python. |

## Local data and credentials

Fresh Windows installations store data in `%LOCALAPPDATA%\DualMind`. Existing prototype users retain the legacy data folder if it exists. Set `DUALMIND_DATA_DIR` to choose a different folder.

```text
DualMind data/
  history/          Conversations and reports (JSON)
  trash/            Recoverable deleted conversations
  settings.json     Models, interaction and timeout preferences
  gemini-key.dpapi   Windows-user-bound encrypted Gemini key
  server.json       Local server runtime, never share or commit
```

The UI never returns saved keys. History, trash and browser drafts are plaintext: do not paste secrets into chat. DPAPI keys cannot be moved directly to another Windows account. The app listens only on localhost and is not suitable for public hosting. See [security and privacy](SECURITY.md).

## Development and verification

```powershell
.\.venv\Scripts\python.exe -B -m unittest test_dualmind test_dualmind_web -v
node --check frontend/app.js
node --check frontend/theme.js
```

The automated suite uses mocked models and makes no real AI requests. `test_gemini.py` is an explicitly invoked live smoke test and has a main guard. CI runs offline checks on Windows. Browser validation covers light/dark themes, 1920×1080, 1366×768, narrow/short windows, model selection, drafts and session actions. Screenshot content is mocked; screenshots are not evidence of model quality or guaranteed account access.

Read the [architecture](docs/architecture.md), [changelog](CHANGELOG.md) and [contribution guide](CONTRIBUTING.md). The old CLI and Tkinter entry remain available; the web workspace is the maintained primary UI.

## Inspiration and credits

[LibreChat](https://github.com/LibreChat-AI/LibreChat) and [Open WebUI](https://github.com/open-webui/open-webui) informed the focus on conversation management, model controls and clear documentation. Codex and Claude informed the restrained workspace style. DualMind's two small characters and UI implementation are original; Claude is a visual reference, not an integrated provider.

Built with the official [Google Gen AI SDK](https://github.com/googleapis/python-genai) and [Codex CLI](https://developers.openai.com/codex/cli/reference/). Provider names remain their owners' trademarks. Source code is licensed under [MIT](LICENSE).
