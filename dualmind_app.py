"""Tkinter 桌面界面：后台调用模型，主线程只处理界面和事件队列。"""
from __future__ import annotations

from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from dualmind import (
    ACTORS, DATA_DIR, MODES, Cancelled, Engine, Session, SessionStore, Settings, safe_error,
)

BG = "#f7f4ed"
PANEL = "#eee9df"
INK = "#292d2a"
MUTED = "#77776f"
COLORS = {"你": "#685749", "Codex": "#3b5e78", "Gemini": "#63714c"}
MODE_KEYS = {label: key for key, label in MODES.items()}
RECIPIENTS = {"两个都回答": ACTORS, "只叫 Codex": ("Codex",), "只叫 Gemini": ("Gemini",)}


class App:
    def __init__(self, root: tk.Tk, engine: Engine | None = None, store: SessionStore | None = None):
        self.root = root
        self.engine, self.store = engine or Engine(), store or SessionStore()
        self.session = Session()
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.busy = False
        self.close_pending = False
        self.history_ids = []
        self.pending_text = ""
        self.start_count = 0
        root.title("DualMind · 共同工作空间")
        root.geometry("1120x780")
        root.minsize(850, 620)
        root.configure(bg=BG)
        self.mode = tk.StringVar(value="聊天")
        self.recipient = tk.StringVar(value="两个都回答")
        self.model = tk.StringVar(value=Settings().gemini_model)
        self.rounds = tk.StringVar(value="2")
        self.status = tk.StringVar(value="准备好了")
        self.cost = tk.StringVar()
        self._build()
        self.refresh_history()
        self._options_changed()
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.poll_id = root.after(100, self._poll)

    def _build(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", font=("Microsoft YaHei UI", 10), background=BG, foreground=INK)
        style.configure("TButton", padding=(12, 7), background=PANEL)
        style.configure("Accent.TButton", background="#586b56", foreground="white")
        style.map("Accent.TButton", background=[("active", "#475b45"), ("disabled", PANEL)])
        style.configure("TCombobox", padding=5)
        style.configure("TEntry", padding=5)
        style.configure("TLabel", background=BG)
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 21, "bold"))
        outer = ttk.Frame(self.root, padding=20)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(0, weight=1)

        sidebar = tk.Frame(outer, bg=PANEL, padx=14, pady=14, width=220)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        sidebar.grid_propagate(False)
        tk.Label(sidebar, text="会话", bg=PANEL, fg=INK, font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w")
        self.new_button = ttk.Button(sidebar, text="＋ 新会话", command=self.new_session)
        self.new_button.pack(fill="x", pady=(15, 12))
        self.history = tk.Listbox(
            sidebar, bg=PANEL, fg=INK, selectbackground="#d9dece", selectforeground=INK,
            relief="flat", borderwidth=0, highlightthickness=0,
            font=("Microsoft YaHei UI", 10), activestyle="none", exportselection=False,
        )
        self.history.pack(fill="both", expand=True)
        self.history.bind("<<ListboxSelect>>", self.open_history)
        tk.Label(
            sidebar, text="历史保存在本机\n密钥仅从环境变量读取",
            bg=PANEL, fg=MUTED, justify="left", font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w", pady=(12, 0))

        main = ttk.Frame(outer)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)
        ttk.Label(main, text="DualMind", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(main, text="你和两个 AI，一起聊，也一起做事。", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(4, 15),
        )

        options = ttk.Frame(main)
        options.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.mode_box = ttk.Combobox(options, textvariable=self.mode, values=list(MODE_KEYS), width=7, state="readonly")
        self.mode_box.pack(side="left")
        self.recipient_box = ttk.Combobox(options, textvariable=self.recipient, values=list(RECIPIENTS), width=14, state="readonly")
        self.recipient_box.pack(side="left", padx=7)
        ttk.Label(options, text="Gemini").pack(side="left", padx=(5, 4))
        self.model_entry = ttk.Entry(options, textvariable=self.model, width=23)
        self.model_entry.pack(side="left")
        self.rounds_label = ttk.Label(options, text="轮数")
        self.rounds_box = ttk.Combobox(options, textvariable=self.rounds, values=("1", "2", "3"), width=3, state="readonly")
        self.mode_box.bind("<<ComboboxSelected>>", self._options_changed)
        self.recipient_box.bind("<<ComboboxSelected>>", self._options_changed)
        self.rounds_box.bind("<<ComboboxSelected>>", self._options_changed)

        transcript_frame = ttk.Frame(main)
        transcript_frame.grid(row=3, column=0, sticky="nsew")
        transcript_frame.columnconfigure(0, weight=1)
        transcript_frame.rowconfigure(0, weight=1)
        self.transcript = tk.Text(
            transcript_frame, bg="#fffcf6", fg=INK, relief="flat", wrap="word",
            font=("Microsoft YaHei UI", 11), padx=20, pady=18, spacing3=8,
            borderwidth=0, highlightthickness=1, highlightbackground="#e2ddd2",
            state="disabled",
        )
        self.transcript.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(transcript_frame, command=self.transcript.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.transcript.configure(yscrollcommand=scroll.set)
        for actor, color in COLORS.items():
            self.transcript.tag_configure(actor, foreground=color, font=("Microsoft YaHei UI", 11, "bold"))
        self.transcript.tag_configure("error", foreground="#a34c3c")
        self.transcript.tag_configure("intro", foreground=MUTED)
        self.render_session()

        actions = ttk.Frame(main)
        actions.grid(row=4, column=0, sticky="ew", pady=(10, 8))
        self.copy_button = ttk.Button(actions, text="复制最新结果", command=self.copy_result)
        self.copy_button.pack(side="left")
        self.export_button = ttk.Button(actions, text="导出会话", command=self.export_session)
        self.export_button.pack(side="left", padx=7)
        ttk.Label(actions, textvariable=self.status, style="Muted.TLabel", wraplength=380).pack(side="right")
        self.input = tk.Text(
            main, height=4, wrap="word", bg="#fffcf6", fg=INK,
            font=("Microsoft YaHei UI", 11), relief="flat", padx=12, pady=10,
            highlightthickness=1, highlightbackground="#ded8cc",
        )
        self.input.grid(row=5, column=0, sticky="ew")
        self.input.bind("<Control-Return>", lambda event: self.send() or "break")
        footer = ttk.Frame(main)
        footer.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(footer, textvariable=self.cost, style="Muted.TLabel", wraplength=500).pack(side="left")
        self.stop_button = ttk.Button(footer, text="停止", command=self.stop, state="disabled")
        self.stop_button.pack(side="right", padx=(8, 0))
        self.send_button = ttk.Button(footer, text="发送  Ctrl+Enter", style="Accent.TButton", command=self.send)
        self.send_button.pack(side="right")
        self.input.focus_set()

    def _options_changed(self, event=None):
        debate = self.mode.get() == "讨论"
        if debate:
            self.recipient.set("两个都回答")
            self.rounds_label.pack(side="left", padx=(8, 4))
            self.rounds_box.pack(side="left")
        else:
            self.rounds_label.pack_forget()
            self.rounds_box.pack_forget()
        self.recipient_box.configure(state="disabled" if debate or self.busy else "readonly")
        count = 2 * int(self.rounds.get()) + 1 if debate else len(RECIPIENTS[self.recipient.get()])
        hint = "手动发送推进，不自动互聊" if not debate else "有限轮次，最后由 Gemini 汇总"
        self.cost.set(f"本次最多 {count} 次模型调用 · {hint}")

    def _set_busy(self, busy: bool):
        self.busy = busy
        for widget in (self.new_button, self.send_button, self.copy_button, self.export_button, self.model_entry):
            widget.configure(state="disabled" if busy else "normal")
        for widget in (self.mode_box, self.rounds_box):
            widget.configure(state="disabled" if busy else "readonly")
        self.history.configure(state="disabled" if busy else "normal")
        self.input.configure(state="disabled" if busy else "normal")
        self.stop_button.configure(state="normal" if busy else "disabled")
        self._options_changed()

    def append_message(self, message):
        self.transcript.configure(state="normal")
        self.transcript.insert("end", f"{message.speaker} · {message.stage}\n", message.speaker)
        self.transcript.insert("end", message.text + "\n\n", "error" if message.kind == "error" else ())
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def render_session(self):
        self.transcript.configure(state="normal")
        self.transcript.delete("1.0", "end")
        if not self.session.messages:
            self.transcript.insert(
                "end",
                "从一句话开始。\n\n聊天：两个 AI 分别回应，你可以随时点名其中一个。\n"
                "协作：一起规划、写作、分析或编写代码。\n"
                "想让一个 AI 接着另一个的答案做事，下一条消息直接点名即可。\n"
                "讨论：独立分析、相互审查，再汇总建议。\n\n"
                "会话使用最近的有限历史；聊天与协作不会自动循环。\n",
                "intro",
            )
        self.transcript.configure(state="disabled")
        for message in self.session.messages:
            self.append_message(message)

    def refresh_history(self):
        try:
            sessions, skipped = self.store.list_sessions()
        except OSError as exc:
            self.status.set(f"读取历史失败：{safe_error(exc)}")
            return
        self.history.configure(state="normal")
        self.history.delete(0, "end")
        self.history_ids = [s.id for s in sessions]
        for session in sessions:
            self.history.insert("end", f"{session.created[5:10]}  {session.title[:18]}")
        if skipped:
            self.status.set(f"跳过 {skipped} 个无法读取的历史文件，原文件保留。")
        self.history.configure(state="disabled" if self.busy else "normal")

    def new_session(self):
        if self.busy:
            return
        self.session = Session()
        self.history.selection_clear(0, "end")
        self.render_session()
        self.status.set("新会话")
        self.input.focus_set()

    def open_history(self, event=None):
        selected = self.history.curselection()
        if self.busy or not selected:
            return
        try:
            self.session = self.store.load(self.history_ids[selected[0]])
            self.mode.set(MODES[self.session.mode])
            self._options_changed()
            self.render_session()
            self.status.set("历史已打开，可以接着聊")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            messagebox.showerror("无法打开历史", safe_error(exc), parent=self.root)

    def send(self):
        if self.busy:
            return
        text = self.input.get("1.0", "end").strip()
        if not text:
            self.status.set("先写一条消息")
            return
        try:
            settings = Settings(self.model.get().strip(), rounds=int(self.rounds.get()))
            settings.validate()
            if len(text) > 12000:
                raise ValueError("消息最多 12000 字，请拆分发送。")
        except ValueError as exc:
            messagebox.showinfo("检查输入", str(exc), parent=self.root)
            return
        mode, recipients = MODE_KEYS[self.mode.get()], RECIPIENTS[self.recipient.get()]
        self.pending_text, self.start_count = text, len(self.session.messages)
        self.input.delete("1.0", "end")
        self.cancel = threading.Event()
        if not self.session.messages:
            self.transcript.configure(state="normal")
            self.transcript.delete("1.0", "end")
            self.transcript.configure(state="disabled")
        self._set_busy(True)
        self.status.set("检查模型配置…")

        def emit(kind, value):
            # 先展示产出，即使磁盘保存失败也能看到并复制本次结果。
            self.events.put((kind, value))
            if kind == "message":
                self.store.save(self.session)

        def worker():
            try:
                success = self.engine.run(self.session, text, mode, recipients, settings, self.cancel, emit)
                result = "完成" if success else "部分调用失败，已保留完成的内容"
                if self.cancel.is_set():
                    result = "已停止，已完成内容已保留"
                self.events.put(("done", result))
            except Cancelled as exc:
                self.events.put(("done", str(exc)))
            except Exception as exc:
                self.events.put(("done", f"未完成：{safe_error(exc)}"))

        self.worker = threading.Thread(target=worker, daemon=True, name="dualmind-models")
        self.worker.start()

    def _poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "message":
                    self.append_message(value)
                elif kind == "status":
                    if not self.cancel.is_set():
                        self.status.set(str(value))
                elif kind == "done":
                    self._set_busy(False)
                    self.status.set(str(value))
                    if len(self.session.messages) == self.start_count:
                        self.input.insert("1.0", self.pending_text)
                    self.refresh_history()
                    if self.close_pending:
                        self.root.destroy()
                        return
        except queue.Empty:
            pass
        self.poll_id = self.root.after(100, self._poll)

    def stop(self):
        if self.busy:
            self.cancel.set()
            self.stop_button.configure(state="disabled")
            self.status.set("正在停止；Gemini 当前请求可能需等到返回或超时。")

    def copy_result(self):
        result = self.session.latest_result()
        if not result:
            self.status.set("还没有可复制的结果")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(result)
        self.status.set("最新结果已复制")

    def export_session(self):
        if not self.session.messages:
            self.status.set("还没有可导出的消息")
            return
        path = filedialog.asksaveasfilename(
            parent=self.root, title="导出会话", defaultextension=".md",
            initialfile=f"DualMind-{self.session.id[:8]}.md",
            filetypes=[("Markdown", "*.md"), ("文本", "*.txt")],
            initialdir=str(self.store.root) if self.store.root.exists() else str(DATA_DIR.parent),
        )
        if path:
            try:
                Path(path).write_text(self.session.markdown(), encoding="utf-8")
                self.status.set("会话已导出")
            except OSError as exc:
                messagebox.showerror("导出失败", safe_error(exc), parent=self.root)

    def close(self):
        if self.busy:
            self.close_pending = True
            self.stop()
            self.status.set("正在停止并关闭；等待当前请求结束，保留已完成内容。")
        else:
            self.root.after_cancel(self.poll_id)
            self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
