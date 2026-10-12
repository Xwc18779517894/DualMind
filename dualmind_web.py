"""DualMind 本地 Web 应用。只监听 127.0.0.1，无云服务、无前端构建依赖。"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie, CookieError
import json
import os
import re
from pathlib import Path
import secrets
import subprocess
import threading
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import webbrowser

from credentials import Credentials
from dualmind import (
    ACTORS, DATA_DIR, MODES, Cancelled, Engine, ModelError, ModelGateway,
    Message, Session, SessionStore, Settings, codex_command, safe_error,
)

FRONTEND = Path(__file__).parent / "frontend"
VERSION = "0.4.0"


class Conflict(ValueError):
    pass


def codex_model_options():
    """只读取 CLI 缓存中的公开模型名称，不读 auth.json 或访问账号接口。"""
    cache = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "models_cache.json"
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
        return sorted({m["slug"] for m in data.get("models", [])
                       if isinstance(m, dict) and isinstance(m.get("slug"), str)
                       and m.get("visibility", "list") == "list"
                       and re.fullmatch(r"[A-Za-z0-9._-]{1,100}", m["slug"])})[:100]
    except (OSError, ValueError, TypeError, KeyError):
        return []


class Application:
    def __init__(self, root: Path = DATA_DIR, gateway=None, credentials=None, test_mode=False):
        self.store = SessionStore(root)
        self.credentials = credentials or Credentials(root)
        self.engine = Engine(gateway or ModelGateway(self.credentials.get_key))
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.job = None
        self.worker = None
        self.cancel = threading.Event()
        self.last_seen = time.monotonic()
        self.test_mode = test_mode
        self.settings = Settings()
        self.config_error = ""
        config = self.store.root / "settings.json"
        if config.exists():
            try:
                self.settings = Settings(**json.loads(config.read_text(encoding="utf-8")))
                self.settings.validate()
            except (OSError, ValueError, TypeError) as exc:
                self.settings = Settings()
                self.config_error = "设置文件无法读取，已使用默认参数；原文件保留。"

    def config(self):
        try:
            codex_command()
            codex = {"configured": True, "source": "ChatGPT 登录 · Codex CLI", "error": ""}
        except ModelError as exc:
            codex = {"configured": False, "source": "未找到 CLI", "error": str(exc)}
        return {
            "version": VERSION, "settings": asdict(self.settings), "gemini": self.credentials.status(),
            "codex": codex, "data_dir": str(self.store.root), "warning": self.config_error,
            "test_mode": self.test_mode,
            "codex_models": codex_model_options(),
        }

    def save_config(self, data):
        with self.lock:
            if self.job and self.job["running"]:
                raise Conflict("当前模型调用尚未结束，请完成或停止后再修改配置。")
            settings = Settings(
                str(data.get("gemini_model", self.settings.gemini_model)).strip(),
                int(data.get("timeout", self.settings.timeout)),
                int(data.get("rounds", self.settings.rounds)),
                str(data.get("codex_model", self.settings.codex_model)).strip(),
                str(data.get("interaction", self.settings.interaction)),
                str(data.get("gemini_proxy", self.settings.gemini_proxy)).strip(),
            )
            settings.validate()
            key = data.get("api_key", "")
            if not isinstance(key, str):
                raise ValueError("Key 格式不正确。")
            if key.strip():
                self.credentials.save(key)
            path = self.store.root / "settings.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(path)
            self.settings, self.config_error = settings, ""
            return self.config()

    def sessions(self, query=""):
        sessions, skipped = self.store.list_sessions()
        if query:
            query = query.casefold()
            sessions = [s for s in sessions if query in (s.title + "\n" + "\n".join(m.text for m in s.messages)).casefold()]
        return {
            "items": [
                {
                    "id": s.id, "title": s.title, "created": s.created, "mode": s.mode,
                    "pinned": s.pinned,
                    "message_count": len(s.messages),
                    "reply_count": sum(m.kind in ("reply", "report") for m in s.messages),
                    "report_count": sum(m.kind == "report" for m in s.messages),
                    "preview": next((m.text[:110] for m in reversed(s.messages) if m.speaker == "你"), ""),
                } for s in sessions
            ], "skipped": skipped,
        }

    def snapshot(self):
        with self.lock:
            if not self.job:
                return None
            return {**{k: v for k, v in self.job.items() if k != "session"},
                    "session": asdict(self.job["session"])}

    def start(self, data):
        with self.lock:
            if self.job and self.job["running"]:
                raise Conflict("已有任务在运行，不会重复发出请求。")
            text = data.get("text", "")
            if not isinstance(text, str) or not text.strip() or len(text) > 12000:
                raise ValueError("请输入 1～12000 字的消息。")
            mode = data.get("mode", "chat")
            recipient = data.get("recipient", "both")
            if mode not in MODES or recipient not in ("both", "codex", "gemini"):
                raise ValueError("会话模式或接收模型不正确。")
            actors = ACTORS if recipient == "both" else (recipient.capitalize(),)
            if mode == "debate" and actors != ACTORS:
                raise ValueError("讨论需要两个模型参与。")
            settings = Settings(**{**asdict(self.settings), "rounds": int(data.get("rounds", self.settings.rounds))})
            settings.validate()
            self.engine.gateway.preflight(actors)
            session_id = data.get("session_id")
            session = self.store.load(session_id) if session_id else Session()
            # 编辑和重新生成都创建分支，原会话与已成功回复保留。
            if "branch_index" in data:
                index = data["branch_index"]
                if (not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(session.messages)
                        or session.messages[index].speaker != "你" or mode == "debate"):
                    raise ValueError("只能从聊天或协作的用户消息创建分支。")
                session = Session(title=session.title + " · 分支", mode=mode,
                                  messages=[Message(**asdict(m)) for m in session.messages[:index]])
            self.cancel = threading.Event()
            self.job = {"id": secrets.token_hex(12), "session": session, "running": True,
                        "status": "准备开始", "outcome": "", "mode": mode}
            job, cancel = self.job, self.cancel

        def emit(kind, value):
            with self.lock:
                if kind == "status" and not cancel.is_set():
                    job["status"] = str(value)
                if kind == "message":
                    self.store.save(session)

        def worker():
            try:
                success = self.engine.run(session, text, mode, actors, settings, cancel, emit)
                outcome = "完成" if success else "部分调用失败，已保留完成的内容"
                if cancel.is_set():
                    outcome = "已停止，已保留完成的内容"
            except Cancelled:
                outcome = "已停止，已保留完成的内容"
            except Exception as exc:
                outcome = "未完成：" + safe_error(exc)
            with self.lock:
                job["running"], job["status"], job["outcome"] = False, outcome, outcome

        self.worker = threading.Thread(target=worker, name="dualmind-models", daemon=True)
        self.worker.start()
        return self.snapshot()

    def stop(self):
        with self.lock:
            if self.job and self.job["running"]:
                self.cancel.set()
                self.job["status"] = "正在停止；Gemini 当前请求可能需要等待返回或超时"
        return self.snapshot()

    def rename(self, data):
        with self.lock:
            if self.job and self.job["running"] and self.job["session"].id == data.get("id"):
                raise Conflict("请等当前会话完成后再改名。")
            title = data.get("title", "")
            if not isinstance(title, str) or not title.strip() or len(title) > 80:
                raise ValueError("标题应为 1～80 字。")
            session = self.store.load(data.get("id", ""))
            session.title = title.strip()
            self.store.save(session)
            return asdict(session)

    def manage_session(self, data, action):
        with self.lock:
            session_id = data.get("id", "")
            if self.job and self.job["running"] and self.job["session"].id == session_id:
                raise Conflict("请等当前会话完成或停止后再操作。")
            if action == "restore":
                self.store.restore(session_id)
            elif action == "delete":
                self.store.trash(session_id)
                if self.job and self.job["session"].id == session_id:
                    self.job = None
            else:
                session = self.store.load(session_id)
                if action == "pin":
                    session.pinned = not session.pinned
                elif action == "fork":
                    session = Session(title=session.title + " · 副本", mode=session.mode,
                                      messages=[Message(**asdict(m)) for m in session.messages])
                else:
                    raise ValueError("操作不正确。")
                self.store.save(session)
                return asdict(session)
            return {"ok": True}

    def models(self):
        with self.lock:
            if self.job and self.job["running"]:
                raise Conflict("请等当前回复完成后再获取模型列表。")
            settings = Settings(**asdict(self.settings))
        if self.test_mode:
            return {"models": ["gemini-3.5-flash-lite", "gemini-3.8-flash"], "cached": False}
        return {"models": self.engine.gateway.list_gemini_models(settings), "cached": False}


class Handler(BaseHTTPRequestHandler):
    server_version = "DualMind"
    sys_version = ""

    def log_message(self, format, *args):
        # 不记录请求 URL、正文、密钥或模型内容。
        pass

    @property
    def app(self):
        return self.server.app

    def reply(self, code, body, content_type="application/json; charset=utf-8", attachment="", cookie=False):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if cookie:
            # 按端口区分本机多个实例；只在合法首页访问时建立浏览器会话。
            self.send_header("Set-Cookie", f"dualmind-{self.server.server_port}={self.app.token}; Path=/; HttpOnly; SameSite=Strict")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'self'; style-src 'self'; "
                         "img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
        if attachment:
            self.send_header("Content-Disposition", f'attachment; filename="{attachment}"')
        self.end_headers()
        self.wfile.write(body)

    def local_request(self):
        origin = f"http://127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            return False
        if self.headers.get("Origin", origin) != origin:
            return False
        return self.headers.get("Sec-Fetch-Site", "none") in ("none", "same-origin", "same-site")

    def authorized(self):
        if not self.local_request():
            return False
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
        except CookieError:
            return False
        entry = cookies.get(f"dualmind-{self.server.server_port}")
        header_token = self.headers.get("X-DualMind-Token", "")
        cookie_token = entry.value if entry else ""
        if not any(hmac.compare_digest(value.encode(), self.app.token.encode()) for value in (header_token, cookie_token)):
            return False
        self.app.last_seen = time.monotonic()
        return True

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/health":
            self.reply(200, {"app": "DualMind", "version": VERSION})
            return
        if path.startswith("/api/"):
            if not self.authorized():
                self.reply(403, {"error": "本地会话授权失效，请从启动器重新打开应用。"})
                return
            try:
                if path == "/api/config":
                    self.reply(200, self.app.config())
                elif path == "/api/sessions":
                    self.reply(200, self.app.sessions())
                elif path == "/api/trash":
                    self.reply(200, {"items": self.app.store.list_trash()})
                elif path == "/api/job":
                    self.reply(200, {"job": self.app.snapshot()})
                elif path == "/api/ping":
                    self.reply(200, {"ok": True})
                elif path.startswith("/api/session/"):
                    session = self.app.store.load(path.rsplit("/", 1)[-1])
                    self.reply(200, asdict(session))
                elif path.startswith("/api/export/"):
                    session = self.app.store.load(path.rsplit("/", 1)[-1])
                    self.reply(200, session.markdown().encode("utf-8"), "text/markdown; charset=utf-8",
                               f"DualMind-{session.id[:8]}.md")
                else:
                    self.reply(404, {"error": "没有这个接口。"})
            except (OSError, ValueError, TypeError, KeyError) as exc:
                self.reply(400, {"error": safe_error(exc)})
            return
        files = {"/": ("index.html", "text/html; charset=utf-8"),
                 "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                 "/theme.js": ("theme.js", "text/javascript; charset=utf-8"),
                 "/style.css": ("style.css", "text/css; charset=utf-8")}
        if path not in files:
            self.reply(404, {"error": "文件不存在。"})
            return
        name, mime = files[path]
        if not self.local_request():
            self.reply(403, {"error": "请在本机地址栏打开 DualMind。"})
            return
        try:
            self.reply(200, (FRONTEND / name).read_bytes(), mime, cookie=path == "/")
        except OSError:
            self.reply(500, {"error": "前端文件缺失，请检查 frontend 目录。"})

    def do_POST(self):
        if not self.authorized():
            self.reply(403, {"error": "请求没有获得本地授权。"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 100000:
                raise ValueError("请求过大或格式不正确。")
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("请求格式应为 JSON。")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("请求格式不正确。")
            path = urlsplit(self.path).path
            if path == "/api/send":
                self.reply(200, {"job": self.app.start(data)})
            elif path == "/api/stop":
                self.reply(200, {"job": self.app.stop()})
            elif path == "/api/config":
                self.reply(200, self.app.save_config(data))
            elif path == "/api/rename":
                self.reply(200, self.app.rename(data))
            elif path == "/api/search":
                query = data.get("query", "")
                if not isinstance(query, str) or len(query) > 200:
                    raise ValueError("搜索关键词应在 200 字以内。")
                self.reply(200, self.app.sessions(query))
            elif path == "/api/models":
                self.reply(200, self.app.models())
            elif path in ("/api/delete", "/api/restore", "/api/pin", "/api/fork"):
                self.reply(200, self.app.manage_session(data, path.rsplit("/", 1)[-1]))
            elif path == "/api/shutdown":
                self.app.stop()
                self.reply(200, {"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                self.reply(404, {"error": "没有这个接口。"})
        except Conflict as exc:
            self.reply(409, {"error": str(exc)})
        except (ModelError, ValueError, TypeError, OSError, KeyError) as exc:
            self.reply(400, {"error": safe_error(exc)})
        except Exception:
            self.reply(500, {"error": "本地服务处理失败，请重试；没有自动重复调用模型。"})


def create_server(app: Application, port=0):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.app = app
    return server


def open_window(url):
    candidates = [
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    for executable in candidates:
        if executable.is_file():
            subprocess.Popen([str(executable), f"--app={url}", "--window-size=1320,900"],
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            return
    webbrowser.open(url)


def main():
    parser = argparse.ArgumentParser(description="DualMind 本地前端应用")
    parser.add_argument("--launch", action="store_true", help="打开独立应用窗口")
    parser.add_argument("--browser", action="store_true", help="用默认浏览器打开本地网址")
    parser.add_argument("--port", type=int, default=8765, help="优先使用的本机端口，默认 8765")
    args = parser.parse_args()
    opener = webbrowser.open if args.browser else open_window
    runtime = DATA_DIR / "server.json"
    if (args.launch or args.browser) and runtime.exists():
        try:
            previous = json.loads(runtime.read_text(encoding="utf-8"))
            port, token = int(previous["port"]), previous["token"]
            request = Request(f"http://127.0.0.1:{port}/api/config", headers={"X-DualMind-Token": token})
            with urlopen(request, timeout=2) as response:
                if json.load(response).get("version") == VERSION:
                    opener(f"http://127.0.0.1:{port}/")
                    return
        except (OSError, ValueError, KeyError):
            pass
    app = Application()
    try:
        server = create_server(app, args.port)
    except OSError as exc:
        if getattr(exc, "winerror", None) != 10048 and exc.errno != 98:
            raise
        server = create_server(app)  # 端口被其他程序占用时仍可启动。
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = runtime.with_suffix(".tmp")
    temporary.write_text(json.dumps({"port": server.server_port, "token": app.token}), encoding="utf-8")
    temporary.replace(runtime)
    url = f"http://127.0.0.1:{server.server_port}/"
    if args.launch or args.browser:
        opener(url)

    def idle_watch():
        while not getattr(server, "closing", False):
            time.sleep(10)
            job = app.snapshot()
            if not (job and job["running"]) and time.monotonic() - app.last_seen > 180:
                server.shutdown()
                return

    threading.Thread(target=idle_watch, daemon=True).start()
    try:
        server.serve_forever()
    finally:
        server.closing = True
        app.stop()
        if app.worker:
            app.worker.join(app.settings.timeout + 20)
        server.server_close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # pythonw 启动时也留下可读原因；不记录密钥和异常链。
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / "startup-error.log").write_text(safe_error(exc), encoding="utf-8")
