# DualMind

<p align="center">
  <strong>多一种思路，多一点可能。</strong><br>
  Two AI perspectives. One shared space.<br>
  Dos perspectivas de IA. Un espacio compartido.
</p>

<p align="center">
  <a href="#简体中文">简体中文</a> · <a href="#english">English</a> · <a href="#español">Español</a>
</p>

[![Offline checks](https://github.com/Xwc18779517894/DualMind/actions/workflows/tests.yml/badge.svg)](https://github.com/Xwc18779517894/DualMind/actions/workflows/tests.yml) ![Windows](https://img.shields.io/badge/platform-Windows-64748b) ![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab) [![MIT](https://img.shields.io/badge/license-MIT-c26943)](LICENSE)

![DualMind · 共同工作空间 / Shared workspace](docs/images/workspace-dark.png)

<p align="center"><sub>作者提供的实际界面截图 · Author-provided interface screenshot · Captura de la interfaz proporcionada por el autor</sub></p>

## 简体中文

<p align="center">
  <a href="#简体中文">简体中文</a> · <a href="#english">English</a> · <a href="#español">Español</a>
</p>

和一个 AI 聊天，能帮助我们整理想法；把另一个 AI 放进同一段对话，可能发现遗漏的前提、不同的路线和更值得问的问题。**DualMind 是你、Codex 和 Gemini 的本地共同工作空间**，可以聊日常、一起做事，也可以在重要问题上认真交换看法。

它不会为了辩论而强行反对，也不把两个模型的一致意见当成事实。对话由你的消息推进。

### 已有功能

| 功能 | 使用方式 |
|---|---|
| 自然群聊 | 默认两位 AI 回答，第二位可以接着第一位补充，不套“立场、论据、假设”模板。 |
| 各自思考 | 切换“各自回答”，同轮互不影响；两种方式都最多两次调用。 |
| 共同工作 | 计划、写作、方案评审、产出代码；点名一位继续做。 |
| 深入讨论 | 第一轮独立思考，随后交换具体看法，最后生成五部分报告。 |
| 会话管理 | 全文搜索、置顶、改名、复制会话、删除到回收站、恢复。 |
| 修改与重试 | 编辑消息或重新生成会创建分支，保留原会话；重试只调用选中的 AI。 |
| 模型切换 | 获取 Gemini 模型列表，选择或手填；Codex 保留 CLI 默认，也支持指定模型。 |
| 舒适阅读 | 暖白、墨灰与跟随系统主题；橙紫高亮；正文和输入框共用居中宽度。 |
| 日常细节 | 草稿自动保存、@点名、快捷键、文本文件上下文、代码复制和 Markdown 导出。 |

### Windows 快速开始

#### 1. 准备环境

- 安装 [Python 3.11 或更新版本](https://www.python.org/downloads/windows/)，本机验证版本为 3.13.2。
- 安装官方 [Codex CLI](https://developers.openai.com/codex/cli/) 并登录有使用资格的 ChatGPT 账号。npm 安装方式需要 [Node.js LTS](https://nodejs.org/)。
- 从 [Google AI Studio](https://aistudio.google.com/apikey) 获取 Gemini API Key。

```powershell
npm install -g @openai/codex
codex login
git clone https://github.com/Xwc18779517894/DualMind.git
cd DualMind
```

也可以在 GitHub 点击 Code → Download ZIP，解压后打开项目文件夹。

#### 2. 安装 Python 依赖

双击 `setup.cmd`，会创建项目内的 `.venv` 并安装依赖。也可以手动执行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

前端是原生 HTML/CSS/JavaScript，没有构建步骤、Electron 或云服务。Python 必需依赖只有 `google-genai`；前端不需要 Node，但 npm 安装 Codex CLI 需要。

#### 3. 启动并配置模型

1. 双击 **启动DualMind.cmd**：独立应用窗口；或 **浏览器打开DualMind.cmd**：普通浏览器标签页。
2. 在“模型设置”粘贴 Gemini Key 并保存。输入框留空表示保留已有 Key，保存不会生成回答。
3. 选择 Gemini 模型；默认 `gemini-3.5-flash-lite` 曾在开发账号的一次短请求中成功，其他账号的可用性、配额和费用需自行确认。
4. Codex 模型留空使用 CLI 当前默认；可手填模型名或参考本机 CLI 缓存候选。候选不保证当前账号有权限。
5. 第一次先只选 Gemini 发送一句短消息，确认连接，再让两位一起参与。

命令行启动方式：

```powershell
.\.venv\Scripts\python.exe dualmind_web.py --browser
```

服务优先使用 `http://127.0.0.1:8765/`，端口被占用时会换一个可用端口；实际地址在设置页显示。收藏的网址需要本地服务先运行。关网页不等于立即关服务，可点“退出应用”，或等待约三分钟空闲退出。

### 聊天方式与快捷操作

- **聊天**自然接话；**协作**一起产出有用结果；**深入讨论**才会多轮交流并生成报告。
- **一起聊**：第二位能看到第一位本轮回复；**各自回答**：双方基于同一历史独立回答。两者都不会无限自动聊天。
- 消息开头输入 `@Codex` 或 `@Gemini`，可以单独点名；也可以用输入框旁的选择器。
- Enter 发送，Shift+Enter 换行，Ctrl+Enter 也能发送；输入法选词时不会发送。
- Ctrl+Shift+O 新会话，Ctrl+K 打开历史搜索。
- 可添加或拖入 UTF-8 文本/代码文件，单文件最多 64 KB，整条消息最多 12000 字。本版不解析图片或 PDF。
- 会话编辑和重新生成会创建新分支，不覆盖原会话。删除可在回收站恢复。

#### 调用次数与边界

单独点名最多 **1 次**生成；两位最多 **2 次**；深入讨论为 **2 × 轮数 + 1 次**，支持 1～3 轮。获取模型列表会请求 API 元数据，不生成文本。没有自动重试、无限循环或隐藏的付费模型回退。

应用不额外开通收费账号或计费，但不保证 API 免费：Codex 消耗已有账号额度，Gemini 受实际项目配额和计费规则约束。上下文携带最近 12 条、约 16000 字；长任务请重申重要背景。

最后的报告由 Gemini 汇总，区分双方共识、核心分歧、各方论据、证据不足和可执行建议；它不是独立事实核查。当前协作能产出文本、方案和代码，不提供通用的自主文件修改。回复在各模型完成后显示，尚无逐 token 流式输出。

### 代理与常见错误

“模型设置 → 本地代理”可填写本机 HTTP/混合代理，如 `http://127.0.0.1:7897`，只影响 Gemini，保存立即生效。不修改系统代理、Codex 网络或证书验证。

请以代理软件实际端口为准；留空使用启动环境，也支持 `DUALMIND_GEMINI_PROXY`。备用 Clash 启动器使用 7897，如果端口不同需修改。首次网络配置、地区条件和路由仍须符合服务支持要求。

| 错误 | 处理方法 |
|---|---|
| Key 未配置 | 在应用里保存 Key，或启动前设置 `GEMINI_API_KEY`。PowerShell 临时变量不会被 Explorer 双击继承。 |
| 400 地区不支持 | 检查实际出口和 [Gemini 支持地区](https://ai.google.dev/gemini-api/docs/available-regions)；换模型不能保证解决。 |
| 404 模型不可用 | 部分模型虽然列出，但已退役或未向账号开放；选择其他支持文本生成的模型。 |
| 429 配额/频率限制 | 查看 API 项目用量，稍后再试，避免反复同时调用两位。 |
| 503 high demand | 当前模型繁忙，稍后只重新生成 Gemini，或明确选择另一可用模型。 |
| 断连/超时 | 检查网络、代理分流和超时；不能仅凭网络错误判断 Key 无效。 |
| Codex 不可用 | 在终端检查 `codex --version` 和 `codex login`；旧 CLI 不支持临时会话参数时更新官方 CLI。 |
| 后端更新未生效 | 任务完成后退出应用再启动；只刷新网页不会重新加载 Python。 |

### 本地数据与密钥

新安装默认存放于 `%LOCALAPPDATA%\DualMind`；原型用户的旧目录存在时继续使用，避免历史丢失。可用 `DUALMIND_DATA_DIR` 覆盖位置。

```text
数据目录/
  history/          会话与报告 JSON
  trash/            可恢复的已删除会话
  settings.json     模型、互动方式与超时
  gemini-key.dpapi   Windows 用户绑定的加密 Key
  server.json       本地运行信息，不能公开分享或提交
```

页面不回显已保存的密钥；Key 不写源码、普通设置或模型日志。DPAPI 密文不能直接搬到另一个 Windows 用户。历史、回收站和浏览器草稿是本地明文，聊天中不要粘贴秘密。

本地保存不意味着离线推理：发送的消息会交给所选模型提供方。服务只绑定 localhost，不应暴露到公网。详见 [安全与隐私说明](SECURITY.md)。

### 开发与验证

```powershell
.\.venv\Scripts\python.exe -B -m unittest test_dualmind test_dualmind_web -v
node --check frontend/app.js
node --check frontend/theme.js
```

自动测试模拟所有模型，不消耗真实 AI 额度。`test_gemini.py` 是手动运行才发请求的真实短测脚本；导入不会调用模型。CI 在 Windows 运行离线测试。浏览器验证覆盖深浅主题、全屏、窄窗、短窗、草稿、模型选择与会话管理；模拟界面不代表真实模型质量。

阅读 [架构说明](docs/architecture.md)、[变更日志](CHANGELOG.md)、[贡献指南](CONTRIBUTING.md)。旧 CLI/Tkinter 入口保留，主要维护界面为 Web 工作空间。

### 参考与致谢

参考 [LibreChat](https://github.com/LibreChat-AI/LibreChat) 和 [Open WebUI](https://github.com/open-webui/open-webui) 的会话管理、模型控制和文档组织；视觉上参考 Codex/Claude 的克制工作台。两位小角色和界面实现为原创，Claude 仅是视觉参考，当前实际接入为 Codex + Gemini。

使用官方 [Google Gen AI SDK](https://github.com/googleapis/python-genai) 与 [Codex CLI](https://developers.openai.com/codex/cli/reference/)。各模型品牌归对应所有者。源码采用 [MIT 许可](LICENSE)。

---

## English

<p align="center">
  <a href="#简体中文">简体中文</a> · <a href="#english">English</a> · <a href="#español">Español</a>
</p>

Talking to one AI can help you think. Bringing a second perspective into the same conversation can reveal alternatives, missing assumptions and useful questions. **DualMind brings you, Codex and Gemini into a local workspace** for everyday conversation, shared work and deliberate discussion.

It does not make disagreement a sport or treat agreement as proof. You decide when the conversation continues.

### What you can do

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

#### What makes it small

The interface is plain HTML, CSS and JavaScript. A Python localhost server connects the existing Codex CLI and official Gemini SDK. No frontend build, Electron, cloud deployment or additional AI account is required. Local storage is not offline inference: selected providers receive the messages you send.

### Quick start · Windows

#### 1. Install prerequisites

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

#### 2. Install the one Python dependency

Double-click `setup.cmd`. It creates `.venv` in the project and installs `requirements.txt`. Or use PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

#### 3. Open and configure

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

### Conversation controls

- **聊天:** natural conversation. **协作:** useful work. **深入讨论:** bounded discussion and a saved report.
- **一起聊:** the second AI sees the first AI's current answer. **各自回答:** the current answers stay independent. Neither setting starts an endless loop.
- `@Codex` or `@Gemini` at the start of a message selects one participant.
- Enter sends; Shift+Enter adds a line; Ctrl+Enter also sends. IME composition does not send.
- Ctrl+Shift+O starts a conversation; Ctrl+K searches history.
- Add or drag a UTF-8 text/code file into the composer: at most 64 KB per file and 12,000 characters total. Images/PDFs are not parsed in this release.
- Editing and regeneration create branches. Regeneration calls only the selected AI.

#### Calls and limits

One participant: at most **1** generation call. Two participants: at most **2**. Discussion: **2 × rounds + 1**, with 1–3 rounds. No automatic retry or hidden model fallback. Listing Gemini models makes API metadata requests but does not generate text. No new paid subscription or billing configuration is enabled by DualMind; ChatGPT subscription limits and Gemini API pricing/quotas still apply.

A context window contains the latest 12 messages, approximately 16,000 characters. Important conclusions need evidence; the report is generated by Gemini and is not an independent fact-check. Codex runs read-only and produces text/code; this app does not provide general autonomous file editing. Responses appear after each model finishes, without token streaming.

### Proxy and troubleshooting

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

### Local data and credentials

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

### Development and verification

```powershell
.\.venv\Scripts\python.exe -B -m unittest test_dualmind test_dualmind_web -v
node --check frontend/app.js
node --check frontend/theme.js
```

The automated suite uses mocked models and makes no real AI requests. `test_gemini.py` is an explicitly invoked live smoke test and has a main guard. CI runs offline checks on Windows. Browser validation covers light/dark themes, 1920×1080, 1366×768, narrow/short windows, model selection, drafts and session actions. Browser verification used mock conversations. The featured screenshot was supplied by the author and shows the empty workspace; it is not evidence of model quality or guaranteed account access.

Read the [architecture](docs/architecture.md), [changelog](CHANGELOG.md) and [contribution guide](CONTRIBUTING.md). The old CLI and Tkinter entry remain available; the web workspace is the maintained primary UI.

### Inspiration and credits

[LibreChat](https://github.com/LibreChat-AI/LibreChat) and [Open WebUI](https://github.com/open-webui/open-webui) informed the focus on conversation management, model controls and clear documentation. Codex and Claude informed the restrained workspace style. DualMind's two small characters and UI implementation are original; Claude is a visual reference, not an integrated provider.

Built with the official [Google Gen AI SDK](https://github.com/googleapis/python-genai) and [Codex CLI](https://developers.openai.com/codex/cli/reference/). Provider names remain their owners' trademarks. Source code is licensed under [MIT](LICENSE).

---

## Español

<p align="center">
  <a href="#简体中文">简体中文</a> · <a href="#english">English</a> · <a href="#español">Español</a>
</p>

Hablar con una IA ayuda a ordenar las ideas. Incorporar otra perspectiva puede revelar alternativas, supuestos y preguntas que faltaban. **DualMind reúne al usuario, Codex y Gemini en un espacio de trabajo local** para conversar, colaborar y analizar decisiones.

No obliga a los modelos a discrepar, ni considera que su acuerdo sea una prueba. Tú decides cuándo continúa la conversación.

### Funciones

| Función | Comportamiento |
|---|---|
| Conversación natural | Dos respuestas por mensaje; la segunda IA puede complementar la primera, sin plantilla de debate. |
| Respuestas independientes | Ambos modelos reciben el mismo contexto sin ver la respuesta actual del otro. |
| Colaboración | Planificación, escritura, revisión de ideas y generación de código. |
| Discusión limitada | Primera ronda independiente, rondas adicionales acotadas e informe final de cinco secciones. |
| Gestión de conversaciones | Búsqueda en todo el texto, fijar, renombrar, duplicar, eliminar y restaurar. |
| Revisión sin perder el original | Editar o regenerar crea una rama; regenerar llama únicamente a la IA seleccionada. |
| Selección de modelos | Lista de Gemini, nombres manuales y elección del modelo de Codex CLI. |
| Lectura cómoda | Temas claro, oscuro y del sistema; columna centrada, Markdown y copia de código. |
| Trabajo guardado | Borradores, archivos de texto como contexto y exportación Markdown. |

### Inicio rápido en Windows

#### 1. Requisitos

- [Python 3.11 o posterior](https://www.python.org/downloads/windows/); la versión verificada localmente es 3.13.2.
- [Codex CLI](https://developers.openai.com/codex/cli/), con una cuenta de ChatGPT que tenga acceso. La instalación mediante npm requiere [Node.js LTS](https://nodejs.org/).
- Una clave de Gemini obtenida en [Google AI Studio](https://aistudio.google.com/apikey).

```powershell
npm install -g @openai/codex
codex login
git clone https://github.com/Xwc18779517894/DualMind.git
cd DualMind
```

También puedes descargar el ZIP desde GitHub y extraerlo.

#### 2. Instalar dependencias

Haz doble clic en `setup.cmd`, que crea `.venv` e instala las dependencias. O ejecuta:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

El frontend usa HTML, CSS y JavaScript sin compilación. El servidor usa la biblioteca estándar de Python y el SDK oficial `google-genai`. No necesitas Electron ni desplegar servicios en la nube. Node no compila el frontend; se utiliza para la instalación de Codex mediante npm.

#### 3. Abrir y configurar

1. **启动DualMind.cmd** abre una ventana independiente; **浏览器打开DualMind.cmd** abre una pestaña normal.
2. En **模型设置** (configuración de modelos), pega la clave de Gemini y guarda. Dejar el campo vacío conserva la clave existente.
3. Elige el modelo de Gemini. El predeterminado es `gemini-3.5-flash-lite`, que respondió a una prueba breve con la cuenta de desarrollo. El acceso, los límites y los precios dependen de tu cuenta.
4. Deja vacío el modelo de Codex para usar el predeterminado de CLI, o escribe un nombre disponible. Las sugerencias proceden de la caché local y no garantizan acceso.
5. Prueba primero un mensaje corto dirigido solo a **Gemini**; después utiliza ambos participantes.

Inicio manual:

```powershell
.\.venv\Scripts\python.exe dualmind_web.py --browser
```

El servidor intenta usar `http://127.0.0.1:8765/` y elige otro puerto si está ocupado. La configuración muestra la dirección real. El servidor debe estar activo antes de abrir un marcador. Usa **退出应用** para salir; cerrar una pestaña no detiene inmediatamente el servidor, que puede cerrarse tras unos tres minutos de inactividad.

### Cómo conversar

- **聊天:** conversación. **协作:** trabajo compartido. **深入讨论:** discusión e informe.
- **一起聊:** la segunda IA ve la respuesta actual de la primera. **各自回答:** respuestas independientes. Ninguna opción activa un bucle infinito.
- Empieza un mensaje con `@Codex` o `@Gemini` para dirigirte a una sola IA.
- Enter envía, Shift+Enter añade una línea y Ctrl+Enter también envía. La composición del teclado IME no envía mensajes.
- Ctrl+Shift+O crea una conversación; Ctrl+K abre la búsqueda.
- Puedes añadir o arrastrar archivos de texto/código UTF-8: hasta 64 KB por archivo y 12 000 caracteres por mensaje. Esta versión no interpreta imágenes ni PDF.
- La eliminación mueve las conversaciones a una papelera local recuperable. Editar o regenerar conserva el original en otra rama.

#### Llamadas y límites

Una IA: como máximo **1** llamada de generación. Ambas: **2**. Discusión: **2 × rondas + 1**, con 1–3 rondas. Consultar modelos solicita metadatos, no genera texto. No hay reintentos automáticos ni cambios silenciosos a modelos de pago.

DualMind no activa nuevas suscripciones ni facturación, pero no garantiza que la API sea gratuita. Se aplican los límites de ChatGPT y las cuotas/precios de Gemini. El contexto incluye los últimos 12 mensajes y aproximadamente 16 000 caracteres.

El informe final lo genera Gemini y distingue acuerdos, desacuerdos, argumentos, evidencia insuficiente y recomendaciones prácticas. No sustituye la verificación de hechos. Codex trabaja en un entorno de solo lectura; esta versión no ofrece edición autónoma general de archivos. Las respuestas aparecen al terminar cada llamada, sin transmisión token a token.

### Proxy y errores frecuentes

El campo **本地代理** acepta un proxy HTTP local, por ejemplo `http://127.0.0.1:7897`. Solo afecta a Gemini y se aplica al guardar. Usa el puerto real de tu software; dejarlo vacío utiliza el entorno de inicio. También se admite `DUALMIND_GEMINI_PROXY`. El lanzador de Clash incluye 7897, que debes ajustar si tu puerto es distinto.

| Error | Qué hacer |
|---|---|
| Clave no configurada | Guarda la clave o establece `GEMINI_API_KEY` antes de iniciar. Las variables temporales de PowerShell no se heredan al abrir desde Explorer. |
| 400, ubicación no admitida | Comprueba la ruta de red y las [regiones admitidas](https://ai.google.dev/gemini-api/docs/available-regions). Cambiar de modelo no garantiza resolverlo. |
| 404, modelo no disponible | Algunos modelos listados están retirados o no disponibles para tu cuenta; elige otro modelo de texto. |
| 429, cuota o frecuencia | Consulta el uso del proyecto y espera; evita repetir llamadas a ambas IA. |
| 503, alta demanda | Espera o elige explícitamente otro modelo disponible. Regenera solo Gemini para no repetir Codex. |
| Desconexión o tiempo agotado | Comprueba la conexión y el proxy. El error no demuestra por sí solo que la clave sea inválida. |
| Codex no funciona | Comprueba `codex --version` y `codex login`; actualiza el CLI oficial si no admite `--ephemeral`. |
| Cambios del backend no visibles | Termina la tarea, sal de la aplicación y vuelve a abrirla. Recargar la página no reinicia Python. |

### Datos y privacidad

Las instalaciones nuevas guardan los datos en `%LOCALAPPDATA%\DualMind`. Los usuarios del prototipo conservan su directorio anterior si existe. `DUALMIND_DATA_DIR` permite elegir otro directorio.

```text
Directorio de datos/
  history/          Conversaciones e informes JSON
  trash/            Conversaciones eliminadas recuperables
  settings.json     Modelos, interacción y tiempo de espera
  gemini-key.dpapi   Clave cifrada vinculada al usuario de Windows
  server.json       Estado local del servidor: no compartir ni publicar
```

La clave guardada no vuelve al frontend. DPAPI vincula el cifrado a tu usuario de Windows. El historial, la papelera y los borradores se guardan como texto sin cifrar: no pegues secretos en el chat. Almacenamiento local no significa inferencia sin conexión; los mensajes enviados llegan a los proveedores seleccionados. El servidor solo escucha en localhost y no debe exponerse a Internet. Consulta [seguridad y privacidad](SECURITY.md).

### Desarrollo

```powershell
.\.venv\Scripts\python.exe -B -m unittest test_dualmind test_dualmind_web -v
node --check frontend/app.js
node --check frontend/theme.js
```

Las pruebas y CI simulan las llamadas a modelos. `test_gemini.py` realiza una prueba real solo si se ejecuta explícitamente. Las pruebas visuales usan contenido simulado. La captura principal fue proporcionada por el autor y muestra el espacio vacío; no garantiza calidad del modelo ni acceso para otras cuentas.

Consulta la [arquitectura](docs/architecture.md), el [registro de cambios](CHANGELOG.md) y la [guía de contribución](CONTRIBUTING.md). Se conservan las interfaces anteriores CLI/Tkinter; la interfaz principal es el espacio web.

### Créditos

[LibreChat](https://github.com/LibreChat-AI/LibreChat) y [Open WebUI](https://github.com/open-webui/open-webui) inspiraron la organización de conversaciones, controles de modelos y documentación. Codex/Claude sirvieron de referencia visual. Los dos personajes y la implementación son originales; Claude no es un proveedor integrado.

DualMind utiliza [Google Gen AI SDK](https://github.com/googleapis/python-genai) y [Codex CLI](https://developers.openai.com/codex/cli/reference/). Las marcas pertenecen a sus propietarios. Código bajo la [licencia MIT](LICENSE).
