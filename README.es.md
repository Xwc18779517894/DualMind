# DualMind

**Dos perspectivas de IA. Un espacio compartido.**

<p align="center">
  <a href="README.md#简体中文">简体中文</a> · <a href="README.md#english">English</a> · <a href="README.md#español">Español</a>
</p>

[![Pruebas sin conexión](https://github.com/Xwc18779517894/DualMind/actions/workflows/tests.yml/badge.svg)](https://github.com/Xwc18779517894/DualMind/actions/workflows/tests.yml) ![Windows](https://img.shields.io/badge/platform-Windows-64748b) [![MIT](https://img.shields.io/badge/license-MIT-c26943)](LICENSE)

Hablar con una IA ayuda a ordenar las ideas. Incorporar otra perspectiva puede revelar alternativas, supuestos y preguntas que faltaban. **DualMind reúne al usuario, Codex y Gemini en un espacio de trabajo local** para conversar, colaborar y analizar decisiones.

No obliga a los modelos a discrepar, ni considera que su acuerdo sea una prueba. Tú decides cuándo continúa la conversación.

![Interfaz oscura de DualMind](docs/images/workspace-dark.png)

*Captura de la interfaz real proporcionada por el autor. La interfaz de la aplicación está actualmente en chino; la documentación está disponible en tres idiomas.*

## Funciones

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

## Inicio rápido en Windows

### 1. Requisitos

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

### 2. Instalar dependencias

Haz doble clic en `setup.cmd`, que crea `.venv` e instala las dependencias. O ejecuta:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

El frontend usa HTML, CSS y JavaScript sin compilación. El servidor usa la biblioteca estándar de Python y el SDK oficial `google-genai`. No necesitas Electron ni desplegar servicios en la nube. Node no compila el frontend; se utiliza para la instalación de Codex mediante npm.

### 3. Abrir y configurar

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

## Cómo conversar

- **聊天:** conversación. **协作:** trabajo compartido. **深入讨论:** discusión e informe.
- **一起聊:** la segunda IA ve la respuesta actual de la primera. **各自回答:** respuestas independientes. Ninguna opción activa un bucle infinito.
- Empieza un mensaje con `@Codex` o `@Gemini` para dirigirte a una sola IA.
- Enter envía, Shift+Enter añade una línea y Ctrl+Enter también envía. La composición del teclado IME no envía mensajes.
- Ctrl+Shift+O crea una conversación; Ctrl+K abre la búsqueda.
- Puedes añadir o arrastrar archivos de texto/código UTF-8: hasta 64 KB por archivo y 12 000 caracteres por mensaje. Esta versión no interpreta imágenes ni PDF.
- La eliminación mueve las conversaciones a una papelera local recuperable. Editar o regenerar conserva el original en otra rama.

### Llamadas y límites

Una IA: como máximo **1** llamada de generación. Ambas: **2**. Discusión: **2 × rondas + 1**, con 1–3 rondas. Consultar modelos solicita metadatos, no genera texto. No hay reintentos automáticos ni cambios silenciosos a modelos de pago.

DualMind no activa nuevas suscripciones ni facturación, pero no garantiza que la API sea gratuita. Se aplican los límites de ChatGPT y las cuotas/precios de Gemini. El contexto incluye los últimos 12 mensajes y aproximadamente 16 000 caracteres.

El informe final lo genera Gemini y distingue acuerdos, desacuerdos, argumentos, evidencia insuficiente y recomendaciones prácticas. No sustituye la verificación de hechos. Codex trabaja en un entorno de solo lectura; esta versión no ofrece edición autónoma general de archivos. Las respuestas aparecen al terminar cada llamada, sin transmisión token a token.

## Proxy y errores frecuentes

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

## Datos y privacidad

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

## Desarrollo

```powershell
.\.venv\Scripts\python.exe -B -m unittest test_dualmind test_dualmind_web -v
node --check frontend/app.js
node --check frontend/theme.js
```

Las pruebas y CI simulan las llamadas a modelos. `test_gemini.py` realiza una prueba real solo si se ejecuta explícitamente. Las pruebas visuales usan contenido simulado; no garantizan calidad del modelo ni acceso para otras cuentas.

Consulta la [arquitectura](docs/architecture.md), el [registro de cambios](CHANGELOG.md) y la [guía de contribución](CONTRIBUTING.md). Se conservan las interfaces anteriores CLI/Tkinter; la interfaz principal es el espacio web.

## Créditos

[LibreChat](https://github.com/LibreChat-AI/LibreChat) y [Open WebUI](https://github.com/open-webui/open-webui) inspiraron la organización de conversaciones, controles de modelos y documentación. Codex/Claude sirvieron de referencia visual. Los dos personajes y la implementación son originales; Claude no es un proveedor integrado.

DualMind utiliza [Google Gen AI SDK](https://github.com/googleapis/python-genai) y [Codex CLI](https://developers.openai.com/codex/cli/reference/). Las marcas pertenecen a sus propietarios. Código bajo la [licencia MIT](LICENSE).
