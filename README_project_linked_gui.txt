Project Linked GUI
==================

This GUI is linked to your original project files:
- email_client.py
- tcp_server.py

How it works:
1. The GUI starts your original tcp_server.py as a subprocess.
2. Send Email runs email_client.send_email(...).
3. Receive Latest Email runs email_client.receive_latest_email(...).
4. Start Unread Monitor runs email_client.monitor_unread_emails(...) in a subprocess.
5. All output and TCP notifications are shown inside the GUI.

How to run:
1. Put these files in the same folder:
   - project_linked_email_gui.py
   - email_client.py
   - tcp_server.py
   - requirements_project_linked.txt
2. Install dependency:
   pip install -r requirements_project_linked.txt
3. Run:
   python project_linked_email_gui.py

Windows:
Double click run_project_linked_gui_windows.bat

Important:
Do not manually run tcp_server.py at the same time. The GUI starts it for you.
