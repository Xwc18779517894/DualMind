"""本地 API 与凭据测试；--serve 提供隔离的浏览器模拟验证环境。"""
import argparse
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from credentials import Credentials
from dualmind import Message, ModelError, Session
from dualmind_web import Application, create_server, codex_model_options


class FakeCredentials:
    def get_key(self):
        return "not-a-real-key-for-local-tests"

    def status(self):
        return {"configured": True, "source": "离线验证用模拟配置", "error": ""}

    def save(self, value):
        pass


class FakeGateway:
    def __init__(self):
        self.calls, self.fail, self.slow = [], False, False

    def preflight(self, actors):
        pass

    def ask(self, actor, prompt, settings, cancel):
        self.calls.append((actor, prompt))
        cancel.wait(0.5 if self.slow else 0.03)
        if self.fail and actor == "Gemini":
            raise ModelError("模拟配额不足，已保留 Codex 内容。")
        if "五个标题" in prompt:
            return (
                "## 双方共识\n\n先明确目标与约束，再安排执行。\n\n"
                "## 核心分歧\n\nCodex 强调可交付成果，Gemini 强调留出调整空间。\n\n"
                "## 各方论据\n\n- **Codex**：小任务容易验证。\n- **Gemini**：反馈能帮助修正计划。\n\n"
                "## 证据不足\n\n尚未确认可用时间与现有基础。\n\n"
                "## 可执行建议\n\n1. 先给出本周时间预算。\n2. 用一个小任务验证，再调整。\n\n"
                "这是一份离线验证用模拟报告，没有调用任何真实模型。"
            )
        return (
            f"这是 **{actor} 的离线模拟回复**，用于检查界面和会话流程。\n\n"
            "### 可执行的下一步\n\n1. 明确你的目标和时间约束。\n2. 拆成可以验证的小任务。\n\n"
            + ("\u0060\u0060\u0060python\nprint('Hello, DualMind')\n\u0060\u0060\u0060\n\n"
               if actor == "Codex" else "可以接着点名我，检查 Codex 的方案并补充遗漏。\n\n")
            + "此环境没有发出任何真实 API 请求。"
        )


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.gateway = FakeGateway()
        self.app = Application(Path(self.temp.name), self.gateway, FakeCredentials(), test_mode=True)
        self.server = create_server(self.app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.app.stop()
        if self.app.worker:
            self.app.worker.join(3)
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.temp.cleanup()

    def request(self, path, body=None, authorized=True, origin=None, extra_headers=None):
        headers = {"Content-Type": "application/json"}
        if authorized:
            headers["X-DualMind-Token"] = self.app.token
        if origin:
            headers["Origin"] = origin
        headers.update(extra_headers or {})
        request = Request(self.base + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, response.read(), response.headers
        except HTTPError as exc:
            return exc.code, exc.read(), exc.headers

    def done(self):
        deadline = time.monotonic() + 3
        while self.app.snapshot()["running"] and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertFalse(self.app.snapshot()["running"])
        return self.app.snapshot()

    def test_static_frontend_and_missing_token(self):
        code, body, headers = self.request("/", authorized=False)
        self.assertEqual(code, 200)
        self.assertIn(b"app.js", body)
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertEqual(self.request("/api/config", authorized=False)[0], 403)
        self.assertEqual(self.request("/api/config", origin="https://example.invalid")[0], 403)
        self.assertEqual(self.request("/credentials.py")[0], 404)

    def test_config_never_returns_key(self):
        code, body, _ = self.request("/api/config")
        self.assertEqual(code, 200)
        self.assertNotIn(b"not-a-real-key-for-local-tests", body)
        self.assertTrue(json.loads(body)["gemini"]["configured"])
        self.assertEqual(self.gateway.calls, [])

    def test_bare_url_cookie_can_send_poll_and_export(self):
        _, _, headers = self.request("/", authorized=False)
        cookie = headers["Set-Cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)
        browser = {"Cookie": cookie.split(";")[0], "Sec-Fetch-Site": "same-origin"}
        code, body, _ = self.request("/api/config", authorized=False, extra_headers=browser)
        self.assertEqual(code, 200)
        self.assertNotIn(self.app.token.encode(), body)
        self.assertEqual(self.request("/api/send", {"text": "浏览器会话", "recipient": "gemini"},
                                      authorized=False, origin=self.base, extra_headers=browser)[0], 200)
        job = self.done()
        self.assertEqual(self.request("/api/job", authorized=False, extra_headers=browser)[0], 200)
        self.assertEqual(self.request("/api/export/" + job["session"]["id"],
                                      authorized=False, extra_headers=browser)[0], 200)
        self.assertEqual(len(self.gateway.calls), 1)

    def test_browser_cookie_rejects_external_origin_and_wrong_host(self):
        cookie = self.request("/", authorized=False)[2]["Set-Cookie"].split(";")[0]
        browser = {"Cookie": cookie}
        self.assertEqual(self.request("/api/config", authorized=False,
                                     origin="https://example.invalid", extra_headers=browser)[0], 403)
        self.assertEqual(self.request("/api/send", {"text": "外部请求"}, authorized=False,
                                     extra_headers={**browser, "Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(self.request("/api/config", authorized=False,
                                     extra_headers={**browser, "Host": "example.invalid"})[0], 403)
        self.assertEqual(self.gateway.calls, [])

    def test_root_never_grants_cookie_to_external_request(self):
        code, _, headers = self.request("/", authorized=False, extra_headers={"Sec-Fetch-Site": "cross-site"})
        self.assertEqual(code, 403)
        self.assertIsNone(headers.get("Set-Cookie"))
        invalid = {"Cookie": f"dualmind-{self.server.server_port}=wrong-session"}
        self.assertEqual(self.request("/api/config", authorized=False, extra_headers=invalid)[0], 403)

    def test_send_history_continue_rename_and_export(self):
        self.assertEqual(self.request("/api/send", {"text": "学习计划", "mode": "work"})[0], 200)
        job = self.done()
        session_id = job["session"]["id"]
        self.assertEqual(len(self.gateway.calls), 2)
        self.assertEqual(len(job["session"]["messages"]), 3)
        self.assertEqual(len(json.loads(self.request("/api/sessions")[1])["items"]), 1)
        self.assertEqual(self.request("/api/rename", {"id": session_id, "title": "本周计划"})[0], 200)
        self.assertEqual(self.request("/api/send", {"text": "接着检查", "session_id": session_id, "recipient": "gemini"})[0], 200)
        job = self.done()
        self.assertEqual(job["session"]["title"], "本周计划")
        self.assertIn("Codex 的离线模拟回复", self.gateway.calls[-1][1])
        code, body, headers = self.request("/api/export/" + session_id)
        self.assertEqual(code, 200)
        self.assertIn("本周计划", body.decode())
        self.assertIn("attachment", headers["Content-Disposition"])

    def test_debate_report_and_call_count(self):
        self.request("/api/send", {"text": "选择方案", "mode": "debate", "rounds": 2})
        job = self.done()
        self.assertEqual(len(self.gateway.calls), 5)
        self.assertEqual(job["session"]["messages"][-1]["kind"], "report")
        self.assertIn("证据不足", job["session"]["messages"][-1]["text"])

    def test_duplicate_and_stop_do_not_start_more_calls(self):
        self.gateway.slow = True
        self.assertEqual(self.request("/api/send", {"text": "任务"})[0], 200)
        self.assertEqual(self.request("/api/send", {"text": "重复任务"})[0], 409)
        self.assertEqual(self.request("/api/config", {"gemini_model": "other"})[0], 409)
        self.request("/api/stop", {})
        self.done()
        self.assertLessEqual(len(self.gateway.calls), 1)

    def test_failed_call_preserves_success(self):
        self.gateway.fail = True
        self.request("/api/send", {"text": "任务"})
        job = self.done()
        self.assertIn("部分调用失败", job["outcome"])
        self.assertEqual(job["session"]["messages"][1]["kind"], "reply")
        self.assertEqual(job["session"]["messages"][2]["kind"], "error")

    def test_missing_key_retains_no_session_and_no_calls(self):
        self.gateway.preflight = lambda actors: (_ for _ in ()).throw(ModelError("缺少 Key"))
        self.assertEqual(self.request("/api/send", {"text": "不要丢掉输入"})[0], 400)
        self.assertIsNone(self.app.snapshot())
        self.assertEqual(self.gateway.calls, [])

    def test_settings_persist_without_calls(self):
        self.assertEqual(self.request("/api/config", {"gemini_model": "custom-model", "rounds": 3, "timeout": 90})[0], 200)
        restarted = Application(Path(self.temp.name), self.gateway, FakeCredentials())
        self.assertEqual(restarted.settings.gemini_model, "custom-model")
        self.assertEqual(restarted.settings.rounds, 3)
        self.assertEqual(self.gateway.calls, [])

    def test_pin_fork_fulltext_search_delete_and_restore_without_model_calls(self):
        session = Session(title="管理测试", messages=[Message("Gemini", "正文里的独特关键词")])
        self.app.store.save(session)
        self.assertEqual(self.request("/api/pin", {"id": session.id})[0], 200)
        self.assertTrue(self.app.store.load(session.id).pinned)
        matches = json.loads(self.request("/api/search", {"query": "独特关键词"})[1])["items"]
        self.assertEqual(matches[0]["id"], session.id)
        forked = json.loads(self.request("/api/fork", {"id": session.id})[1])
        self.assertNotEqual(forked["id"], session.id)
        self.assertEqual(forked["messages"][0]["text"], "正文里的独特关键词")
        self.assertEqual(self.request("/api/delete", {"id": session.id})[0], 200)
        self.assertEqual(json.loads(self.request("/api/trash")[1])["items"][0]["id"], session.id)
        self.assertEqual(self.request("/api/restore", {"id": session.id})[0], 200)
        self.assertEqual(self.app.store.load(session.id).title, "管理测试")
        self.assertEqual(self.gateway.calls, [])

    def test_regenerate_branch_calls_only_selected_actor_and_keeps_original(self):
        self.request("/api/send", {"text": "原问题"})
        original = self.done()["session"]
        self.gateway.calls.clear()
        self.assertEqual(self.request("/api/send", {"text": "改后的问题", "recipient": "gemini",
                         "session_id": original["id"], "branch_index": 0})[0], 200)
        branch = self.done()["session"]
        self.assertNotEqual(branch["id"], original["id"])
        self.assertTrue(branch["title"].endswith(" · 分支"))
        self.assertEqual([a for a, _ in self.gateway.calls], ["Gemini"])
        self.assertEqual(self.app.store.load(original["id"]).messages[0].text, "原问题")
        self.assertEqual(branch["messages"][0]["text"], "改后的问题")
        self.assertEqual(self.request("/api/send", {"text": "测试", "session_id": original["id"],
                                                  "branch_index": 1})[0], 400)

    def test_active_session_cannot_be_deleted_or_forked(self):
        self.gateway.slow = True
        self.request("/api/send", {"text": "运行中"})
        session_id = self.app.snapshot()["session"]["id"]
        self.assertEqual(self.request("/api/delete", {"id": session_id})[0], 409)
        self.assertEqual(self.request("/api/fork", {"id": session_id})[0], 409)
        self.app.stop()
        self.done()

    def test_model_settings_persist_and_listing_is_not_generation(self):
        self.assertEqual(self.request("/api/config", {"codex_model": "test-model", "interaction": "independent",
                                                     "gemini_proxy": "http://127.0.0.1:7897"})[0], 200)
        settings = Application(Path(self.temp.name), self.gateway, FakeCredentials()).settings
        self.assertEqual(settings.codex_model, "test-model")
        self.assertEqual(settings.interaction, "independent")
        self.assertEqual(settings.gemini_proxy, "http://127.0.0.1:7897")
        self.assertIn("gemini-3.5-flash-lite", json.loads(self.request("/api/models", {})[1])["models"])
        self.assertEqual(self.gateway.calls, [])

    def test_management_rejects_invalid_ids_and_cross_origin(self):
        for endpoint in ("delete", "restore", "pin", "fork"):
            self.assertEqual(self.request("/api/" + endpoint, {"id": "../other"})[0], 400)
            self.assertEqual(self.request("/api/" + endpoint, {"id": "a" * 32}, origin="https://external.invalid")[0], 403)
        self.assertEqual(self.gateway.calls, [])


class CredentialTests(unittest.TestCase):
    def test_codex_options_exclude_hidden_cache_models(self):
        cached = {"models": [{"slug": "listed-model", "visibility": "list"},
                             {"slug": "internal-model", "visibility": "hide"},
                             {"slug": "invalid model", "visibility": "list"}]}
        with patch("dualmind_web.Path.read_text", return_value=json.dumps(cached)):
            self.assertEqual(codex_model_options(), ["listed-model"])

    @unittest.skipUnless(os.name == "nt", "DPAPI 是 Windows 功能")
    def test_dpapi_persistence_never_saves_plaintext(self):
        fake = "not-a-real-gemini-key-for-dpapi-tests-0000"
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            credentials = Credentials(Path(folder))
            credentials.save(fake)
            self.assertNotIn(fake.encode(), credentials.path.read_bytes())
            self.assertEqual(Credentials(Path(folder)).get_key(), fake)
            self.assertNotIn(fake, json.dumps(credentials.status()))
            self.assertTrue(credentials.status()["configured"])


def serve_fixture(root):
    app = Application(root, FakeGateway(), FakeCredentials(), test_mode=True)
    sample = Session(title="离线验证 · 学习计划评审", mode="debate", messages=[
        Message("你", "比较学习计划的可执行性", "user", "讨论"),
        Message("Gemini", FakeGateway().ask("Gemini", "五个标题", None, threading.Event()), "report", "综合报告"),
    ])
    app.store.save(sample)
    server = create_server(app)
    root.mkdir(parents=True, exist_ok=True)
    (root / "browser-test.json").write_text(
        json.dumps({"url": f"http://127.0.0.1:{server.server_port}/#token={app.token}", "port": server.server_port}),
        encoding="utf-8",
    )
    server.serve_forever()


if __name__ == "__main__":
    if "--serve" in os.sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument("--serve", action="store_true")
        parser.add_argument("--root", type=Path, required=True)
        args = parser.parse_args()
        serve_fixture(args.root)
    else:
        unittest.main()
