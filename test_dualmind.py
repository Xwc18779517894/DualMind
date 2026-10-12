"""仅使用模拟响应，不运行 test_gemini.py，不调用任何真实模型。"""
import os
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from dualmind import (
    ACTORS, Cancelled, Engine, Message, ModelError, ModelGateway, Session,
    SessionStore, Settings, ask_codex, ask_gemini, safe_error,
)


class FakeGateway:
    def __init__(self, fail_at=0, cancel_after_first=None):
        self.calls = []
        self.fail_at = fail_at
        self.cancel_after_first = cancel_after_first

    def preflight(self, actors):
        pass

    def ask(self, actor, prompt, settings, cancel):
        self.calls.append((actor, prompt))
        if len(self.calls) == self.fail_at:
            raise ModelError("模拟配额不足")
        if len(self.calls) == 1 and self.cancel_after_first:
            self.cancel_after_first.set()
        return f"{actor}-回答-{len(self.calls)}"


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeGateway()
        self.engine = Engine(self.fake)
        self.session = Session()

    def test_chat_two_independent_replies_without_report(self):
        self.assertTrue(self.engine.run(self.session, "一起聊聊", settings=Settings(interaction="independent")))
        self.assertEqual([a for a, _ in self.fake.calls], list(ACTORS))
        self.assertNotIn("Codex-回答-1", self.fake.calls[1][1])
        self.assertEqual([m.kind for m in self.session.messages], ["user", "reply", "reply"])

    def test_single_recipient(self):
        self.engine.run(self.session, "给我建议", recipients=("Gemini",))
        self.assertEqual(len(self.fake.calls), 1)
        self.assertEqual(self.fake.calls[0][0], "Gemini")

    def test_together_chat_has_same_turn_peer_without_debate_template(self):
        self.engine.run(self.session, "今天有点累")
        self.assertIn("Codex-回答-1", self.fake.calls[1][1])
        self.assertIn("不必逐条审查", self.fake.calls[1][1])
        self.assertNotIn("给出立场、论据、假设和局限", self.fake.calls[0][1])
        self.assertEqual(len(self.fake.calls), 2)
        self.assertEqual(self.session.messages[-1].model, "gemini-3.5-flash-lite")

    def test_together_chat_after_failed_peer_still_answers_independently(self):
        fake = FakeGateway(fail_at=1)
        self.assertFalse(Engine(fake).run(self.session, "聊聊"))
        self.assertEqual(len(fake.calls), 2)
        self.assertNotIn("同伴 Codex 刚才的回复", fake.calls[1][1])

    def test_invalid_proxy_and_model_never_call(self):
        for settings in (Settings(gemini_proxy="http://remote.invalid:8080"),
                         Settings(gemini_proxy="http://name:secret@localhost:7897"),
                         Settings(gemini_proxy="http://localhost:not-a-port"),
                         Settings(codex_model="--dangerously-bypass"),
                         Settings(interaction="infinite")):
            with self.subTest(settings=settings):
                with self.assertRaises(ValueError):
                    self.engine.run(self.session, "测试", settings=settings)
        self.assertEqual(self.fake.calls, [])

    def test_followup_sees_previous_both_answers(self):
        self.engine.run(self.session, "先写方案")
        self.engine.run(self.session, "审阅刚才的方案", mode="work", recipients=("Gemini",))
        prompt = self.fake.calls[-1][1]
        self.assertIn("Codex-回答-1", prompt)
        self.assertIn("Gemini-回答-2", prompt)
        self.assertIn("审阅刚才的方案", prompt)

    def test_debate_round_counts_and_review_context(self):
        for rounds in (1, 2, 3):
            with self.subTest(rounds=rounds):
                fake, session = FakeGateway(), Session()
                Engine(fake).run(session, "问题", mode="debate", settings=Settings(rounds=rounds))
                self.assertEqual(len(fake.calls), 2 * rounds + 1)
                self.assertEqual(session.messages[-1].kind, "report")
                if rounds >= 2:
                    for _, prompt in fake.calls[2:4]:
                        self.assertIn("Codex-回答-1", prompt)
                        self.assertIn("Gemini-回答-2", prompt)
                        self.assertIn("你自己的上一轮观点", prompt)
                    self.assertNotIn("Codex-回答-3", fake.calls[3][1])
                self.assertIn("证据不足", fake.calls[-1][1])
                self.assertIn("双方一致不代表事实", fake.calls[-1][1])

    def test_failed_chat_preserves_success_and_error(self):
        fake = FakeGateway(fail_at=2)
        success = Engine(fake).run(self.session, "任务")
        self.assertFalse(success)
        self.assertEqual([m.kind for m in self.session.messages], ["user", "reply", "error"])

    def test_failed_debate_does_not_continue_or_summarize(self):
        fake = FakeGateway(fail_at=1)
        self.assertFalse(Engine(fake).run(self.session, "问题", mode="debate"))
        self.assertEqual(len(fake.calls), 2)
        self.assertFalse(any(m.kind == "report" for m in self.session.messages))

    def test_cancel_between_calls_preserves_first_answer(self):
        cancel = threading.Event()
        fake = FakeGateway(cancel_after_first=cancel)
        with self.assertRaises(Cancelled):
            Engine(fake).run(self.session, "任务", cancel=cancel)
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(self.session.messages[-1].text, "Codex-回答-1")

    def test_invalid_options_never_call_model_or_append(self):
        for kwargs in (
            {"settings": Settings(rounds=4)},
            {"mode": "debate", "recipients": ("Codex",)},
            {"recipients": ("Codex", "Codex")},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.engine.run(self.session, "任务", **kwargs)
        self.assertEqual(self.fake.calls, [])
        self.assertEqual(self.session.messages, [])

    def test_copy_latest_result_does_not_return_old_report(self):
        self.session.messages = [
            Message("你", "旧问题", "user"), Message("Gemini", "旧报告", "report"),
            Message("你", "新问题", "user"), Message("Codex", "新回复"),
        ]
        self.assertEqual(self.session.latest_result(), "Codex\n新回复")


class StorageTests(unittest.TestCase):
    def test_round_trip_and_corrupt_file_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            store = SessionStore(Path(folder))
            session = Session(title="中文标题", messages=[Message("你", "测试", "user")])
            store.save(session)
            session.messages.append(Message("Gemini", "回答"))
            store.save(session)
            self.assertEqual(store.load(session.id).messages[-1].text, "回答")
            corrupt = Path(folder) / "history" / ("a" * 32 + ".json")
            corrupt.write_text("{", encoding="utf-8")
            sessions, skipped = store.list_sessions()
            self.assertEqual(len(sessions), 1)
            self.assertEqual(skipped, 1)
            self.assertTrue(corrupt.exists())
            self.assertIn("中文标题", sessions[0].markdown())
            self.assertFalse(list((Path(folder) / "history").glob("*.tmp")))

    def test_reject_path_traversal(self):
        with self.assertRaises(ValueError):
            SessionStore().load("../other")

    def test_trash_restore_and_old_history_compatibility(self):
        with tempfile.TemporaryDirectory() as folder:
            store = SessionStore(Path(folder))
            session = Session(title="保留这段", messages=[Message("Gemini", "内容")], pinned=True)
            store.save(session)
            data = json.loads(store._path(session.id).read_text(encoding="utf-8"))
            data.pop("pinned")
            data["messages"][0].pop("model")
            store._path(session.id).write_text(json.dumps(data), encoding="utf-8")
            self.assertFalse(store.load(session.id).pinned)
            store.trash(session.id)
            self.assertEqual(store.list_sessions()[0], [])
            self.assertEqual(store.list_trash()[0]["title"], "保留这段")
            store.restore(session.id)
            self.assertEqual(store.load(session.id).messages[0].text, "内容")
            self.assertEqual(store.list_trash(), [])

    def test_restore_does_not_overwrite_existing_history(self):
        with tempfile.TemporaryDirectory() as folder:
            store = SessionStore(Path(folder))
            session = Session(title="原会话")
            store.save(session)
            store.trash(session.id)
            session.title = "同名新会话"
            store.save(session)
            with self.assertRaises(ValueError):
                store.restore(session.id)
            self.assertEqual(store.load(session.id).title, "同名新会话")


class AdapterTests(unittest.TestCase):
    def test_preflight_missing_key_no_codex_request(self):
        with patch.dict(os.environ, {}, clear=True), patch("dualmind.codex_command") as command:
            with self.assertRaises(ModelError):
                ModelGateway().preflight(ACTORS)
            command.assert_not_called()

    def test_secret_redaction(self):
        secret = "fake-only-for-unit-test"
        with patch.dict(os.environ, {"GEMINI_API_KEY": secret}):
            self.assertNotIn(secret, safe_error(f"error {secret}"))
        self.assertNotIn("fake-key", safe_error("https://example.invalid?key=fake-key&x=1"))

    def test_codex_stdin_polling_and_no_gemini_key_in_child(self):
        process = MagicMock()
        process.communicate.side_effect = [
            subprocess.TimeoutExpired("fake", 0.2), ("回答", ""),
        ]
        process.returncode = 0
        process.poll.return_value = 0
        with patch("dualmind.codex_command", return_value="codex.cmd"), \
             patch("dualmind.subprocess.Popen", return_value=process) as popen, \
             patch.dict(os.environ, {"GEMINI_API_KEY": "fake-only"}):
            self.assertEqual(ask_codex('中文 & "引号"'), "回答")
        self.assertEqual(process.communicate.call_args_list[0].kwargs["input"], '中文 & "引号"')
        self.assertIsNone(process.communicate.call_args_list[1].kwargs["input"])
        self.assertNotIn("GEMINI_API_KEY", popen.call_args.kwargs["env"])
        self.assertIn("read-only", popen.call_args.args[0])

    def test_codex_timeout_cleans_process(self):
        process = MagicMock()
        process.poll.return_value = 0
        with patch("dualmind.codex_command", return_value="codex.cmd"), \
             patch("dualmind.subprocess.Popen", return_value=process), \
             patch("dualmind.time.monotonic", side_effect=[0, 181]), \
             patch("dualmind._stop_process") as stop:
            with self.assertRaisesRegex(ModelError, "超时"):
                ask_codex("问题")
            stop.assert_called_once_with(process)

    def test_codex_selected_model_uses_cli_flag_and_ephemeral_session(self):
        process = MagicMock()
        process.communicate.return_value = ("模拟回复", "")
        process.returncode = 0
        process.poll.return_value = 0
        with patch("dualmind.codex_command", return_value="codex.cmd"), \
             patch("dualmind.subprocess.Popen", return_value=process) as popen:
            ask_codex("聊天", Settings(codex_model="test-model"))
        command = popen.call_args.args[0]
        self.assertIn("--ephemeral", command)
        self.assertEqual(command[command.index("--model") + 1], "test-model")
        self.assertIn("read-only", command)

    def test_gemini_model_list_filters_modalities_without_generation(self):
        from google import genai
        client = MagicMock()
        client.__enter__.return_value = client
        def model(name, actions):
            return type("Model", (), {"name": "models/" + name, "supported_actions": actions})()
        client.models.list.return_value = [
            model("gemini-test-flash", ["generateContent"]),
            model("gemini-test-flash-image", ["generateContent"]),
            model("gemini-test-tts", ["generateContent"]),
            model("gemini-embedding", ["embedContent"]),
        ]
        with patch.object(genai, "Client", return_value=client) as factory:
            result = ModelGateway(lambda: "fake-only").list_gemini_models(
                Settings(gemini_proxy="http://127.0.0.1:7897"))
        self.assertEqual(result, ["gemini-test-flash"])
        self.assertEqual(factory.call_args.kwargs["http_options"].retry_options.attempts, 1)
        self.assertEqual(factory.call_args.kwargs["http_options"].client_args["proxy"], "http://127.0.0.1:7897")
        client.models.generate_content.assert_not_called()

    def test_gemini_config_error_and_empty_response_without_network(self):
        from google import genai
        client = MagicMock()
        client.__enter__.return_value = client
        client.models.generate_content.return_value.text = "本地模拟回答"
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-only"}), \
             patch.object(genai, "Client", return_value=client) as factory:
            self.assertEqual(ask_gemini("问题"), "本地模拟回答")
            config = factory.call_args.kwargs["http_options"]
            self.assertEqual(config.timeout, 180000)
            self.assertEqual(config.retry_options.attempts, 1)
            self.assertEqual(client.models.generate_content.call_args.kwargs["model"], "gemini-3.5-flash-lite")
            client.models.generate_content.return_value.candidates = [
                type("Candidate", (), {"finish_reason": "MAX_TOKENS"})()
            ]
            self.assertIn("可能不完整", ask_gemini("问题"))
            client.models.generate_content.return_value.text = ""
            with self.assertRaisesRegex(ModelError, "没有返回文本"):
                ask_gemini("问题")
            error = RuntimeError("模拟 fake-only")
            error.code = 429
            client.models.generate_content.side_effect = error
            with self.assertRaisesRegex(ModelError, "配额") as raised:
                ask_gemini("问题")
            self.assertNotIn("fake-only", str(raised.exception))


    def test_gemini_explicit_proxy_is_scoped_to_sdk(self):
        from google import genai
        client = MagicMock()
        client.__enter__.return_value = client
        client.models.generate_content.return_value.text = "代理配置模拟回复"
        client.models.generate_content.return_value.candidates = []
        with patch.dict(os.environ, {"DUALMIND_GEMINI_PROXY": "http://127.0.0.1:7897"}), \
             patch.object(genai, "Client", return_value=client) as factory:
            self.assertEqual(ask_gemini("问题", api_key="fake-only"), "代理配置模拟回复")
            args = factory.call_args.kwargs["http_options"].client_args
            self.assertEqual(args, {"proxy": "http://127.0.0.1:7897", "trust_env": False})
            self.assertNotIn("verify", args)
            client.models.generate_content.assert_called_once()
        with patch.dict(os.environ, {"DUALMIND_GEMINI_PROXY": ""}), \
             patch.object(genai, "Client", return_value=client) as factory:
            ask_gemini("问题", api_key="fake-only")
            self.assertFalse(factory.call_args.kwargs["http_options"].client_args)

    def test_gemini_location_error_is_distinguished_from_other_400_errors(self):
        from google import genai
        from google.genai.errors import ClientError
        client = MagicMock()
        client.__enter__.return_value = client
        for message, expected in (
            ("User location is not supported for the API use.", "当前访问地区不受 API 支持"),
            ("Other failed precondition.", "请求参数或模型配置不正确"),
        ):
            with self.subTest(message=message), patch.object(genai, "Client", return_value=client):
                client.models.generate_content.reset_mock()
                client.models.generate_content.side_effect = ClientError(400, {
                    "error": {"code": 400, "message": message, "status": "FAILED_PRECONDITION"},
                })
                with self.assertRaises(ModelError) as raised:
                    ask_gemini("问题", api_key="fake-only")
                self.assertIn(expected, str(raised.exception))
                self.assertIn(message, str(raised.exception))
                client.models.generate_content.assert_called_once()

    def test_gemini_busy_model_is_distinguished_from_other_503_errors(self):
        from google import genai
        from google.genai.errors import ServerError
        client = MagicMock()
        client.__enter__.return_value = client
        for message, expected in (
            ("This model is currently experiencing high demand. fake-only", "模型当前繁忙"),
            ("Service temporarily unavailable. fake-only", "服务暂时不可用"),
        ):
            with self.subTest(message=message), patch.object(genai, "Client", return_value=client):
                client.models.generate_content.reset_mock()
                client.models.generate_content.side_effect = ServerError(503, {
                    "error": {"code": 503, "message": message, "status": "UNAVAILABLE"},
                })
                with self.assertRaises(ModelError) as raised:
                    ask_gemini("问题", api_key="fake-only")
                self.assertIn(expected, str(raised.exception))
                self.assertIn("只选择 Gemini", str(raised.exception))
                self.assertNotIn("fake-only", str(raised.exception))
                client.models.generate_content.assert_called_once()

    def test_gemini_network_errors_are_actionable_without_retry(self):
        import httpx
        from google import genai
        client = MagicMock()
        client.__enter__.return_value = client
        for error, expected in (
            (httpx.RemoteProtocolError("Server disconnected without sending a response."), "网络连接失败"),
            (httpx.ConnectError("connection failed fake-only"), "网络连接失败"),
            (httpx.ReadTimeout("read timed out"), "等待网络响应超时"),
        ):
            with self.subTest(error=type(error).__name__), \
                 patch.object(genai, "Client", return_value=client):
                client.models.generate_content.reset_mock()
                client.models.generate_content.side_effect = error
                with self.assertRaises(ModelError) as raised:
                    ask_gemini("问题", api_key="fake-only")
                self.assertIn(expected, str(raised.exception))
                self.assertIn("请检查网络", str(raised.exception))
                self.assertNotIn("fake-only", str(raised.exception))
                client.models.generate_content.assert_called_once()


class DesktopTests(unittest.TestCase):
    """隐藏 Tk 窗口验证实际控件及线程消息流，模型始终为 FakeGateway。"""

    def setUp(self):
        import tkinter as tk
        from dualmind_app import App
        self.temp = tempfile.TemporaryDirectory()
        self.root = tk.Tk()
        self.root.withdraw()
        self.fake = FakeGateway()
        self.app = App(self.root, Engine(self.fake), SessionStore(Path(self.temp.name)))

    def tearDown(self):
        self.app.close()
        self.temp.cleanup()

    def wait_done(self):
        deadline = time.monotonic() + 5
        while self.app.busy and time.monotonic() < deadline:
            self.root.update()
            time.sleep(0.01)
        self.assertFalse(self.app.busy, "后台任务未结束")

    def test_send_history_copy_and_followup(self):
        self.app.input.insert("1.0", "一起做学习计划")
        self.app.send()
        self.wait_done()
        transcript = self.app.transcript.get("1.0", "end")
        self.assertIn("Codex-回答-1", transcript)
        self.assertIn("Gemini-回答-2", transcript)
        self.assertEqual(len(self.app.store.list_sessions()[0]), 1)
        with patch.object(self.root, "clipboard_clear"), patch.object(self.root, "clipboard_append") as copied:
            self.app.copy_result()
            self.assertIn("Gemini-回答-2", copied.call_args.args[0])
        self.app.recipient.set("只叫 Gemini")
        self.app.input.insert("1.0", "审阅上面的计划")
        self.app.send()
        self.wait_done()
        self.assertEqual(len(self.fake.calls), 3)
        self.assertIn("Codex-回答-1", self.fake.calls[-1][1])
        self.app.new_session()
        self.assertEqual(self.app.session.messages, [])
        self.app.history.selection_set(0)
        self.app.open_history()
        self.assertEqual(len(self.app.session.messages), 5)

    def test_preflight_failure_restores_input(self):
        self.app.engine.gateway.preflight = lambda actors: (_ for _ in ()).throw(ModelError("缺少配置"))
        self.app.input.insert("1.0", "不要丢掉这句话")
        self.app.send()
        self.wait_done()
        self.assertEqual(self.fake.calls, [])
        self.assertEqual(self.app.input.get("1.0", "end").strip(), "不要丢掉这句话")
        self.assertIn("缺少配置", self.app.status.get())

    def test_discussion_controls_and_call_estimate(self):
        self.app.mode.set("讨论")
        self.app._options_changed()
        self.assertEqual(str(self.app.recipient_box["state"]), "disabled")
        self.assertIn("5 次", self.app.cost.get())
        self.app.mode.set("聊天")
        self.app.recipient.set("只叫 Codex")
        self.app._options_changed()
        self.assertIn("1 次", self.app.cost.get())


if __name__ == "__main__":
    unittest.main()
