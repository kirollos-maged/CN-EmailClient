"""

Put this file in the SAME folder as email_client.py and tcp_server.py, then run:
    python project_linked_email_gui.py

Install dependency first:
    pip install customtkinter
"""

from __future__ import annotations

import os
import re
import sys
import time
import queue
import signal
import subprocess
import threading
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk

BG = "#D4D0C8"
WHITE = "#FFFFFF"
FNT = ("Tahoma", 9)
FNT_B = ("Tahoma", 9, "bold")

class _W: pass
ctk = _W()

class _CTkRoot(tk.Tk):
    def __init__(self):
        super().__init__()
        self.configure(bg=BG)
        style = ttk.Style(self)
        if 'winnative' in style.theme_names():
            style.theme_use('winnative')
        elif 'classic' in style.theme_names():
            style.theme_use('classic')

class _CTkFrame(tk.Frame):
    def __init__(self, master=None, corner_radius=0, fg_color=None, **kw):
        kw.setdefault('bg', BG)
        super().__init__(master, **kw)
    def configure(self, **kw):
        kw.pop('corner_radius', None)
        kw.pop('fg_color', None)
        super().configure(**kw)

class _CTkLabel(tk.Label):
    def __init__(self, master=None, text='', font=None, text_color=None, justify='left', wraplength=0, **kw):
        kw.setdefault('bg', BG)
        kw.setdefault('fg', '#000000')
        fnt = FNT
        if font and hasattr(font, '_font'):
            fnt = font._font
        if wraplength:
            kw['wraplength'] = wraplength
        super().__init__(master, text=text, justify=justify or 'left', font=fnt, **kw)
    def configure(self, text=None, text_color=None, **kw):
        if text is not None: kw['text'] = text
        super().configure(**kw)

class _CTkButton(tk.Button):
    def __init__(self, master=None, text='', command=None, height=0, **kw):
        kw.pop('corner_radius', None)
        kw.pop('fg_color', None)
        super().__init__(master, text=text, command=command, bg=BG, fg='#000000', font=FNT, relief=tk.RAISED, bd=2, activebackground='#C0C0C0', **kw)
    def configure(self, text=None, **kw):
        if text is not None: kw['text'] = text
        super().configure(**kw)

class _CTkEntry(tk.Entry):
    def __init__(self, master=None, placeholder_text='', show='', **kw):
        kw.pop('corner_radius', None)
        kw.pop('fg_color', None)
        super().__init__(master, bg=WHITE, fg='#000000', font=FNT, relief=tk.SUNKEN, bd=2, show=show, **kw)
        self.insert(0, placeholder_text)
    def get(self):
        return super().get()

class _CTkTextbox(tk.Text):
    def __init__(self, master=None, height=10, font=None, **kw):
        kw.pop('corner_radius', None)
        kw.pop('fg_color', None)
        h = max(1, height // 18)
        super().__init__(master, bg=WHITE, fg='#000000', font=("Courier New", 10), relief=tk.SUNKEN, bd=2, height=h, wrap='word', **kw)
    def configure(self, state=None, **kw):
        if state: super().configure(state=state)

class _CTkFont:
    def __init__(self, size=9, weight='normal'):
        self._font = ('Tahoma', size, 'bold' if weight=='bold' else 'normal')

ctk.CTk = _CTkRoot
ctk.CTkFrame = _CTkFrame
ctk.CTkLabel = _CTkLabel
ctk.CTkButton = _CTkButton
ctk.CTkEntry = _CTkEntry
ctk.CTkTextbox = _CTkTextbox
ctk.CTkFont = _CTkFont
ctk.set_appearance_mode = lambda x: None
ctk.set_default_color_theme = lambda x: None


APP_TITLE = "Network Email Client - Project Linked GUI"


class ProjectLinkedEmailGUI(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.base_dir = Path(__file__).resolve().parent
        self.email_client_path = self.base_dir / "email_client.py"
        self.tcp_server_path = self.base_dir / "tcp_server.py"

        self.server_process: Optional[subprocess.Popen[str]] = None
        self.monitor_process: Optional[subprocess.Popen[str]] = None
        self.output_queue: queue.Queue[tuple[str, str]] = queue.Queue()

        self.smtp_latency_value = "--"
        self.smtp_throughput_value = "--"
        self.imap_latency_value = "--"
        self.notification_latency_value = "--"
        self.last_event_value = "No events yet"

        self._configure_window()
        self._build_layout()
        self._poll_output_queue()
        self._validate_project_files()
        self.after(600, self.start_tcp_server)

    # ------------------------------------------------------------------
    # Window and layout
    # ------------------------------------------------------------------
    def _configure_window(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title(APP_TITLE)
        self.geometry("1180x720")
        self.minsize(1050, 650)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Menu Bar
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)
        
        # Sidebar
        self.sidebar = tk.Frame(self, bg=BG, relief=tk.SUNKEN, bd=2, width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False) # keep width
        
        # Blue Header in Sidebar
        header_bg = "#000080" # Classic Windows Dark Blue
        self.sidebar_header = tk.Label(self.sidebar, text=" CN Email", bg=header_bg, fg="white", font=("Tahoma", 10, "bold"), anchor="w")
        self.sidebar_header.pack(fill="x", padx=2, pady=2)
        
        # Navigation Buttons
        tk.Button(self.sidebar, text=" Dashboard", command=lambda: self.show_page("dashboard"), bg=BG, relief=tk.RAISED, bd=2, font=("Tahoma", 9), anchor="w").pack(fill="x", padx=6, pady=4)
        tk.Button(self.sidebar, text=" Compose Email", command=lambda: self.show_page("compose"), bg=BG, relief=tk.RAISED, bd=2, font=("Tahoma", 9), anchor="w").pack(fill="x", padx=6, pady=4)
        tk.Button(self.sidebar, text=" Inbox / IMAP", command=lambda: self.show_page("inbox"), bg=BG, relief=tk.RAISED, bd=2, font=("Tahoma", 9), anchor="w").pack(fill="x", padx=6, pady=4)
        tk.Button(self.sidebar, text=" TCP Server", command=lambda: self.show_page("server"), bg=BG, relief=tk.RAISED, bd=2, font=("Tahoma", 9), anchor="w").pack(fill="x", padx=6, pady=4)
        tk.Button(self.sidebar, text=" Metrics", command=lambda: self.show_page("metrics"), bg=BG, relief=tk.RAISED, bd=2, font=("Tahoma", 9), anchor="w").pack(fill="x", padx=6, pady=4)
        
        # Project Status Label
        self.project_status_label = tk.Label(self.sidebar, text="Checking...", bg=BG, fg="#333333", font=("Tahoma", 8), justify="left", wraplength=180)
        self.project_status_label.pack(side="bottom", anchor="sw", padx=6, pady=10)

        # Main Area
        self.main = tk.Frame(self, bg=BG, relief=tk.SUNKEN, bd=2)
        self.main.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(0, weight=1)
        
        self.pages: dict[str, tk.Frame] = {}
        self._build_dashboard_page()
        self._build_compose_page()
        self._build_inbox_page()
        self._build_server_page()
        self._build_metrics_page()
        self.show_page("dashboard")

    def _page(self, name: str) -> tk.Frame:
        frame = tk.Frame(self.main, bg=BG)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        self.pages[name] = frame
        return frame

    def show_page(self, name: str) -> None:
        for page in self.pages.values():
            page.grid_remove()
        self.pages[name].grid()

    def _build_dashboard_page(self) -> None:
        page = self._page("dashboard")
        
        tk.Label(page, text="Network Email Client Dashboard", bg=BG, font=("Tahoma", 14, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))
        tk.Label(page, text="This GUI runs your original email_client.py and tcp_server.py files.", bg=BG, font=("Tahoma", 9)).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))
        
        cards = tk.Frame(page, bg=BG)
        cards.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        for i in range(4):
            cards.grid_columnconfigure(i, weight=1)
            
        self.server_status_card = self._metric_card(cards, "TCP Server", "Starting...", 0, 0)
        self.smtp_status_card = self._metric_card(cards, "SMTP", "Ready", 0, 1)
        self.imap_status_card = self._metric_card(cards, "IMAP", "Ready", 0, 2)
        self.last_event_card = self._metric_card(cards, "Last Event", "No events yet", 0, 3)
        
        controls = tk.Frame(page, bg=BG)
        controls.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        
        tk.Button(controls, text="Start TCP Server", bg=BG, relief=tk.RAISED, font=("Tahoma", 9), command=self.start_tcp_server).pack(side="left", padx=5)
        tk.Button(controls, text="Stop TCP Server", bg=BG, relief=tk.RAISED, font=("Tahoma", 9), command=self.stop_tcp_server).pack(side="left", padx=5)
        tk.Button(controls, text="Load Account From Project", bg=BG, relief=tk.RAISED, font=("Tahoma", 9), command=self.load_account_from_project).pack(side="left", padx=5)
        tk.Button(controls, text="Clear Logs", bg=BG, relief=tk.RAISED, font=("Tahoma", 9), command=self.clear_all_logs).pack(side="left", padx=5)
        
        tk.Label(page, text="Live System Log:", bg=BG, font=("Tahoma", 9, "bold")).grid(row=4, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.dashboard_log = tk.Text(page, font=("Courier New", 9), relief=tk.SUNKEN, bd=2)
        self.dashboard_log.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
        page.grid_rowconfigure(5, weight=1)

    def _metric_card(self, parent: tk.Frame, title: str, value: str, row: int, col: int) -> tk.Label:
        card_bg = "#C4C4C4" # Highlighted gray
        frame = tk.Frame(parent, bg=card_bg, relief=tk.RAISED, bd=2)
        frame.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        tk.Label(frame, text=title, bg=card_bg, font=("Tahoma", 8), fg="#222222").pack(anchor="nw", padx=8, pady=(8, 0))
        lbl = tk.Label(frame, text=value, bg=card_bg, font=("Tahoma", 12, "bold"))
        lbl.pack(anchor="w", padx=8, pady=(4, 10))
        return lbl

    def _build_credentials_box(self, parent: tk.Frame, start_row: int = 0) -> int:
        box = tk.LabelFrame(parent, text="Credentials", bg=BG, font=("Tahoma", 8))
        box.grid(row=start_row, column=0, sticky="ew", padx=10, pady=5)
        box.grid_columnconfigure(1, weight=1)
        
        tk.Label(box, text="Ethereal Email:", bg=BG, font=("Tahoma", 9)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.email_entry = getattr(self, "email_entry", None) or tk.Entry(box, relief=tk.SUNKEN, bd=2)
        self.email_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        tk.Label(box, text="Password:", bg=BG, font=("Tahoma", 9)).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.password_entry = getattr(self, "password_entry", None) or tk.Entry(box, show="*", relief=tk.SUNKEN, bd=2)
        self.password_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        return start_row + 1

    def _build_compose_page(self) -> None:
        page = self._page("compose")
        tk.Label(page, text="Compose Email", bg=BG, font=("Tahoma", 14, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))
        tk.Label(page, text="Send emails using email_client.py", bg=BG, font=("Tahoma", 9)).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))
        
        self._build_credentials_box(page, 2)
        
        form = tk.LabelFrame(page, text="Message", bg=BG, font=("Tahoma", 8))
        form.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        form.grid_columnconfigure(1, weight=1)
        
        tk.Label(form, text="To:", bg=BG, font=("Tahoma", 9)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.to_entry = tk.Entry(form, relief=tk.SUNKEN, bd=2)
        self.to_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        tk.Label(form, text="Subject:", bg=BG, font=("Tahoma", 9)).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.subject_entry = tk.Entry(form, relief=tk.SUNKEN, bd=2)
        self.subject_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        tk.Label(form, text="Body:", bg=BG, font=("Tahoma", 9)).grid(row=2, column=0, sticky="nw", padx=5, pady=5)
        self.body_box = tk.Text(form, height=6, font=("Courier New", 9), relief=tk.SUNKEN, bd=2)
        self.body_box.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.body_box.insert("1.0", "Hello from Multi-Client Email System")
        
        tk.Button(form, text="Send Email", bg=BG, relief=tk.RAISED, font=("Tahoma", 9), command=self.send_email_using_project).grid(row=3, column=1, sticky="e", padx=5, pady=5)
        
        self.compose_output = tk.Text(page, font=("Courier New", 9), relief=tk.SUNKEN, bd=2)
        self.compose_output.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        page.grid_rowconfigure(4, weight=1)

    def _build_inbox_page(self) -> None:
        page = self._page("inbox")
        tk.Label(page, text="Inbox / IMAP", bg=BG, font=("Tahoma", 14, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))
        tk.Label(page, text="Receive and monitor emails.", bg=BG, font=("Tahoma", 9)).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))
        
        self._build_credentials_box(page, 2)
        
        controls = tk.Frame(page, bg=BG)
        controls.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        
        tk.Button(controls, text="Receive Latest Email", bg=BG, relief=tk.RAISED, font=("Tahoma", 9), command=self.receive_email_using_project).pack(side="left", padx=5)
        self.monitor_button = tk.Button(
            controls,
            text="Start Unread Monitor",
            bg=BG,
            relief=tk.RAISED,
            font=("Tahoma", 9),
            command=self.start_monitor_using_project
       )
        self.monitor_button.pack(side="left", padx=5)
        tk.Button(controls, text="Stop Monitor", bg=BG, relief=tk.RAISED, font=("Tahoma", 9), command=self.stop_monitor).pack(side="left", padx=5)
        
        self.inbox_output = tk.Text(page, font=("Courier New", 9), relief=tk.SUNKEN, bd=2)
        self.inbox_output.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        page.grid_rowconfigure(4, weight=1)

    def _build_server_page(self) -> None:
        page = self._page("server")
        tk.Label(page, text="TCP Notification Server", bg=BG, font=("Tahoma", 14, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))
        
        controls = tk.Frame(page, bg=BG)
        controls.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        tk.Button(controls, text="Start tcp_server.py", bg=BG, relief=tk.RAISED, font=("Tahoma", 9), command=self.start_tcp_server).pack(side="left", padx=5)
        tk.Button(controls, text="Stop tcp_server.py", bg=BG, relief=tk.RAISED, font=("Tahoma", 9), command=self.stop_tcp_server).pack(side="left", padx=5)
        tk.Button(controls, text="Clear Server Log", bg=BG, relief=tk.RAISED, font=("Tahoma", 9), command=lambda: self._clear_textbox(self.server_log)).pack(side="left", padx=5)
        
        self.server_log = tk.Text(page, font=("Courier New", 9), relief=tk.SUNKEN, bd=2)
        self.server_log.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        page.grid_rowconfigure(2, weight=1)

    def _build_metrics_page(self) -> None:
        page = self._page("metrics")
        tk.Label(page, text="Network Performance Metrics", bg=BG, font=("Tahoma", 14, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))
        
        cards = tk.Frame(page, bg=BG)
        cards.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        for i in range(4):
            cards.grid_columnconfigure(i, weight=1)
            
        self.smtp_latency_label = self._metric_card(cards, "SMTP Latency", "--", 0, 0)
        self.smtp_throughput_label = self._metric_card(cards, "SMTP Throughput", "--", 0, 1)
        self.imap_latency_label = self._metric_card(cards, "IMAP Latency", "--", 0, 2)
        self.notification_latency_label = self._metric_card(cards, "Notification Latency", "--", 0, 3)
        
        tk.Label(page, text="Client Output History:", bg=BG, font=("Tahoma", 9, "bold")).grid(row=2, column=0, sticky="w", padx=10, pady=(5, 0))
        self.metrics_log = tk.Text(page, font=("Courier New", 9), relief=tk.SUNKEN, bd=2)
        self.metrics_log.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        page.grid_rowconfigure(3, weight=1)

    # ------------------------------------------------------------------
    # Project integration
    # ------------------------------------------------------------------
    def _validate_project_files(self) -> None:
        missing = []
        if not self.email_client_path.exists():
            missing.append("email_client.py")
        if not self.tcp_server_path.exists():
            missing.append("tcp_server.py")

        if missing:
            self.project_status_label.configure(text="Missing: " + ", ".join(missing))
            self._log("system", "Missing project files: " + ", ".join(missing))
        else:
            self.project_status_label.configure(text="Linked to:\nemail_client.py\ntcp_server.py")
            self._log("system", f"Linked folder: {self.base_dir}")
            self._log("system", "Found email_client.py and tcp_server.py")

    def _project_python_command(self, code: str, args: list[str]) -> list[str]:
        return [sys.executable, "-u", "-c", code, *args]

    def _run_project_command(self, title: str, code: str, args: list[str], target: str) -> None:
        if not self.email_client_path.exists():
            self._log("error", "email_client.py not found. Put the GUI in the same folder as your project files.")
            return

        def worker() -> None:
            self.output_queue.put((target, f"\n--- {title} started ---\n"))
            try:
                process = subprocess.Popen(
                    self._project_python_command(code, args),
                    cwd=str(self.base_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                output_lines: list[str] = []
                assert process.stdout is not None
                for line in process.stdout:
                    output_lines.append(line)
                    self.output_queue.put((target, line))
                    self.output_queue.put(("dashboard", line))
                    self.output_queue.put(("metrics", line))
                process.wait()
                full_output = "".join(output_lines)
                self._parse_metrics(full_output)
                self.output_queue.put((target, f"--- {title} finished with code {process.returncode} ---\n"))
            except Exception as exc:
                self.output_queue.put((target, f"[Error] {exc}\n"))

        threading.Thread(target=worker, daemon=True).start()

    def send_email_using_project(self) -> None:
        sender = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        recipient = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip() or "CN Project Test"
        body = self.body_box.get("1.0", "end-1c")

        if not sender or not password or not recipient:
            self._log("compose", "Please enter sender email, password, and recipient email.\n")
            return

        self.smtp_status_card.configure(text="Sending...")
        code = "import email_client, sys; email_client.send_email(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])"
        self._run_project_command("email_client.send_email", code, [sender, password, recipient, subject, body], "compose")

    def receive_email_using_project(self) -> None:
        email_address = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email_address or not password:
            self._log("inbox", "Please enter email and password first.\n")
            return

        self.imap_status_card.configure(text="Receiving...")
        code = "import email_client, sys; email_client.receive_latest_email(sys.argv[1], sys.argv[2])"
        self._run_project_command("email_client.receive_latest_email", code, [email_address, password], "inbox")

    def start_monitor_using_project(self) -> None:
        email_address = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email_address or not password:
            self._log("inbox", "Please enter email and password first.\n")
            return
        if self.monitor_process and self.monitor_process.poll() is None:
            self._log("inbox", "Monitor is already running.\n")
            return

        code = "import email_client, sys; email_client.monitor_unread_emails(sys.argv[1], sys.argv[2])"
        try:
            self.monitor_process = subprocess.Popen(
                self._project_python_command(code, [email_address, password]),
                cwd=str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self.monitor_button.configure(text="Monitor Running")
            self._log("inbox", "Started monitor using email_client.monitor_unread_emails(...).\n")
            threading.Thread(target=self._read_process_output, args=(self.monitor_process, "monitor"), daemon=True).start()
        except Exception as exc:
            self._log("inbox", f"[Monitor Error] {exc}\n")

    def stop_monitor(self) -> None:
        if self.monitor_process and self.monitor_process.poll() is None:
            self._terminate_process(self.monitor_process)
            self._log("inbox", "Monitor stopped.\n")
        self.monitor_process = None
        self.monitor_button.configure(text="Start Unread Monitor")

    def start_tcp_server(self) -> None:
        if not self.tcp_server_path.exists():
            self._log("server", "tcp_server.py not found. Put the GUI in the same folder as your project files.\n")
            self.server_status_card.configure(text="Missing")
            return
        if self.server_process and self.server_process.poll() is None:
            self._log("server", "tcp_server.py is already running.\n")
            self.server_status_card.configure(text="Running")
            return

        try:
            self.server_process = subprocess.Popen(
                [sys.executable, "-u", str(self.tcp_server_path)],
                cwd=str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self.server_status_card.configure(text="Running")
            self._log("server", "Started original tcp_server.py process.\n")
            threading.Thread(target=self._read_process_output, args=(self.server_process, "server"), daemon=True).start()
        except Exception as exc:
            self.server_status_card.configure(text="Failed")
            self._log("server", f"[TCP Server Error] {exc}\n")

    def stop_tcp_server(self) -> None:
        if self.server_process and self.server_process.poll() is None:
            self._terminate_process(self.server_process)
            self._log("server", "tcp_server.py stopped.\n")
        self.server_process = None
        self.server_status_card.configure(text="Stopped")

    def _read_process_output(self, process: subprocess.Popen[str], target: str) -> None:
        try:
            assert process.stdout is not None
            for line in process.stdout:
                self.output_queue.put((target, line))
                if target == "server":
                    self.output_queue.put(("dashboard", line))
                elif target == "monitor":
                    self.output_queue.put(("inbox", line))
                    self.output_queue.put(("dashboard", line))
                    self.output_queue.put(("metrics", line))
                    self._parse_metrics(line)
        except Exception as exc:
            self.output_queue.put((target, f"[Read Error] {exc}\n"))

    def _terminate_process(self, process: subprocess.Popen[str]) -> None:
        try:
            if process.poll() is None:
                if os.name == "nt":
                    process.terminate()
                else:
                    process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
        except Exception as exc:
            self._log("system", f"[Terminate Error] {exc}")

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def load_account_from_project(self) -> None:
        """Find the first Ethereal account tuple in email_client.py and load it into the entries."""
        if not self.email_client_path.exists():
            self._log("system", "email_client.py not found.\n")
            return

        text = self.email_client_path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r'\(\s*["\']([^"\']+@ethereal\.email)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', text)
        if not match:
            self._log("system", "No Ethereal account tuple found in email_client.py.\n")
            return

        email_address, password = match.group(1), match.group(2)
        self.email_entry.delete(0, "end")
        self.email_entry.insert(0, email_address)
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, password)
        self._log("system", "Loaded first Ethereal account from email_client.py.\n")

    def _parse_metrics(self, text: str) -> None:
        smtp_latency = re.search(r"SMTP Latency:\s*([0-9.]+)\s*seconds", text)
        smtp_throughput = re.search(r"SMTP Throughput:\s*([0-9.]+)\s*Bytes/sec", text)
        imap_latency = re.search(r"IMAP Latency:\s*([0-9.]+)\s*seconds", text)
        notification_latency = re.search(r"Notification Latency:\s*([0-9.]+)\s*seconds", text)

        if smtp_latency:
            self.smtp_latency_value = smtp_latency.group(1) + " s"
            self.output_queue.put(("metric_update", "smtp_latency"))
        if smtp_throughput:
            self.smtp_throughput_value = smtp_throughput.group(1) + " B/s"
            self.output_queue.put(("metric_update", "smtp_throughput"))
        if imap_latency:
            self.imap_latency_value = imap_latency.group(1) + " s"
            self.output_queue.put(("metric_update", "imap_latency"))
        if notification_latency:
            self.notification_latency_value = notification_latency.group(1) + " s"
            self.output_queue.put(("metric_update", "notification_latency"))

        if "Email Sent Successfully" in text:
            self.last_event_value = "Email Sent Successfully"
            self.output_queue.put(("metric_update", "last_event"))
        elif "Email Sending Failed" in text:
            self.last_event_value = "Email Sending Failed"
            self.output_queue.put(("metric_update", "last_event"))
        elif "Email Received Successfully" in text:
            self.last_event_value = "Email Received Successfully"
            self.output_queue.put(("metric_update", "last_event"))
        elif "Email Receiving Failed" in text:
            self.last_event_value = "Email Receiving Failed"
            self.output_queue.put(("metric_update", "last_event"))

    def _apply_metric_update(self) -> None:
        self.smtp_latency_label.configure(text=self.smtp_latency_value)
        self.smtp_throughput_label.configure(text=self.smtp_throughput_value)
        self.imap_latency_label.configure(text=self.imap_latency_value)
        self.notification_latency_label.configure(text=self.notification_latency_value)
        self.last_event_card.configure(text=self.last_event_value)

        if self.smtp_latency_value != "--":
            self.smtp_status_card.configure(text="Done")
        if self.imap_latency_value != "--":
            self.imap_status_card.configure(text="Done")

    def _poll_output_queue(self) -> None:
        while True:
            try:
                target, text = self.output_queue.get_nowait()
            except queue.Empty:
                break

            if target == "metric_update":
                self._apply_metric_update()
                continue

            self._write_target(target, text)

        self.after(100, self._poll_output_queue)

    def _write_target(self, target: str, text: str) -> None:
        if target == "dashboard":
            self._write_textbox(self.dashboard_log, text)
        elif target == "compose":
            self._write_textbox(self.compose_output, text)
        elif target == "inbox":
            self._write_textbox(self.inbox_output, text)
        elif target == "server":
            self._write_textbox(self.server_log, text)
        elif target == "monitor":
            self._write_textbox(self.inbox_output, text)
        elif target == "metrics":
            self._write_textbox(self.metrics_log, text)
        elif target in {"system", "error"}:
            self._write_textbox(self.dashboard_log, text + ("" if text.endswith("\n") else "\n"))

    def _log(self, target: str, text: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.output_queue.put((target, f"[{timestamp}] {text}" if not text.startswith("\n") else text))

    @staticmethod
    def _write_textbox(textbox: ctk.CTkTextbox, text: str) -> None:
        textbox.configure(state="normal")
        textbox.insert("end", text)
        textbox.see("end")
        textbox.configure(state="normal")

    @staticmethod
    def _clear_textbox(textbox: ctk.CTkTextbox) -> None:
        textbox.delete("1.0", "end")

    def clear_all_logs(self) -> None:
        for box in [self.dashboard_log, self.compose_output, self.inbox_output, self.server_log, self.metrics_log]:
            self._clear_textbox(box)

    def on_close(self) -> None:
        self.stop_monitor()
        self.stop_tcp_server()
        self.destroy()


if __name__ == "__main__":
    app = ProjectLinkedEmailGUI()
    app.mainloop()
