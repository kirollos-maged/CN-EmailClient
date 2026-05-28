
# 📬 CN-EmailClient — TCP-Linked Email Client with GUI
 
A Python desktop application that combines **SMTP/IMAP email operations** with a **real-time TCP notification system**, all wrapped in a clean GUI. Built as a Computer Networks (CN) project to demonstrate socket programming, multi-threading, and network protocol integration.
 
---
 
## ✨ Features
 
- **Send Emails** via SMTP (with TLS) using Ethereal Email (test server)
- **Receive Latest Email** via IMAP
- **Monitor Unread Emails** in the background using a subprocess thread
- **TCP Notification Server** — every email action triggers a real-time socket notification on `127.0.0.1:9999`
- **Notification Latency Tracking** — measures and displays round-trip time for each TCP notification
- **Desktop GUI** — built with Tkinter (with CustomTkinter fallback support), styled for Windows compatibility
- All output and TCP notifications are displayed live inside the GUI
---
 
## 🗂️ Project Structure
 
```
CN project/
└── project_linked_email_gui_ready/
    ├── project_linked_email_gui.py   # Main GUI application
    ├── email_client.py               # SMTP/IMAP email logic + TCP notification sender
    ├── tcp_server.py                 # TCP notification server (auto-started by GUI)
    ├── requirements_project_linked.txt
    └── run_project_linked_gui_windows.bat
```
 
---
 
## 🚀 Getting Started
 
### Prerequisites
 
- Python 3.8+
- pip
### Installation
 
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/netmail-cn-project.git
   cd netmail-cn-project
   ```
 
2. Install dependencies:
   ```bash
   pip install -r requirements_project_linked.txt
   ```
 
### Running
 
**On any OS:**
```bash
python project_linked_email_gui.py
```
 
**On Windows (double-click):**
```
run_project_linked_gui_windows.bat
```
 
> ⚠️ **Do not** manually run `tcp_server.py` — the GUI starts it automatically as a subprocess.
 
---
 
## ⚙️ How It Works
 
```
┌─────────────────────────────┐
│         GUI (Tkinter)       │
│  Send | Receive | Monitor   │
└────────────┬────────────────┘
             │ calls
┌────────────▼────────────────┐
│       email_client.py       │
│  SMTP send / IMAP receive   │
│  + TCP notification sender  │
└────────────┬────────────────┘
             │ socket to localhost:9999
┌────────────▼────────────────┐
│       tcp_server.py         │
│  Notification Server        │
│  (subprocess, multi-thread) │
└─────────────────────────────┘
```
 
1. The GUI launches `tcp_server.py` as a subprocess on startup.
2. Every email action (send/receive/monitor) calls `send_notification()` which connects to the TCP server via a socket, sends a message, and records the **latency**.
3. All results and notifications are streamed back into the GUI's output panel.
---
 
## 📦 Dependencies
 
| Package | Purpose |
|---|---|
| `customtkinter >= 5.2.2` | Modern GUI widgets (optional — falls back to Tkinter) |
| `smtplib` | Built-in — SMTP email sending |
| `imaplib` | Built-in — IMAP email retrieval |
| `socket` | Built-in — TCP notification system |
| `threading` | Built-in — Background monitoring & server handling |
 
---
 
## 🧪 Email Test Server
 
This project uses **[Ethereal Email](https://ethereal.email/)** — a fake SMTP/IMAP service for testing. No real emails are sent. You can create a free test account at ethereal.email and use those credentials in the GUI.
 
---
 
## 📡 TCP Notification Details
 
- **Host:** `127.0.0.1` (localhost)
- **Port:** `9999`
- **Protocol:** TCP (stream socket)
- **Threading:** Each client connection is handled in a separate thread
- **Latency:** Measured per notification and displayed in the GUI output
---
 
## 📄 License
 
This project was developed for educational purposes as part of a Computer Networks course.
 
---
 
## 🙌 Acknowledgements
 
- [Ethereal Email](https://ethereal.email/) for the test email infrastructure
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern UI components
 
