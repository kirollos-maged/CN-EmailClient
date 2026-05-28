import smtplib
import imaplib
import email
import socket
import threading
import time

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ==========================================
# Send Notification to TCP Server
# ==========================================
def send_notification(message):

    host = '127.0.0.1'
    port = 9999

    try:

        start_time = time.time()

        client_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        client_socket.connect((host, port))

        client_socket.sendall(
            message.encode('utf-8')
        )

        end_time = time.time()

        notification_latency = end_time - start_time

        print(
            f"Notification Latency: "
            f"{notification_latency:.6f} seconds"
        )

        client_socket.close()

    except Exception as e:
        print(f"[Warning] Notification Error: {e}")


# ==========================================
# SMTP Send Email
# ==========================================
def send_email(sender_email, password,
               recipient_email, subject, body):

    try:

        msg = MIMEMultipart()

        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        smtp_server = 'smtp.ethereal.email'
        smtp_port = 587

        # ===== Start Time =====
        start_time = time.time()

        server = smtplib.SMTP(
            smtp_server,
            smtp_port
        )

        server.starttls()

        server.login(
            sender_email,
            password
        )

        server.send_message(msg)

        server.quit()

        # ===== End Time =====
        end_time = time.time()

        smtp_latency = end_time - start_time

        print(
            f"SMTP Latency: "
            f"{smtp_latency:.4f} seconds"
        )

        # ===== Throughput =====
        total_bytes = len(
            msg.as_string().encode('utf-8')
        )

        throughput = total_bytes / smtp_latency

        print(
            f"SMTP Throughput: "
            f"{throughput:.2f} Bytes/sec"
        )

        print(
            f"[{sender_email}] "
            f"Email Sent Successfully"
        )

        send_notification(
            f"{sender_email}: "
            f"Email Sent Successfully"
        )

    except Exception as e:

        print(
            f"[{sender_email}] "
            f"Email Sending Failed: {e}"
        )

        send_notification(
            f"{sender_email}: "
            f"Email Sending Failed"
        )


# ==========================================
# Receive Latest Email
# ==========================================
def receive_latest_email(email_address, password):

    try:

        imap_server = 'imap.ethereal.email'
        imap_port = 993

        # ===== Start Time =====
        start_time = time.time()

        mail = imaplib.IMAP4_SSL(
            imap_server,
            imap_port
        )

        mail.login(
            email_address,
            password
        )

        mail.select('inbox')

        status, response = mail.search(
            None,
            'ALL'
        )

        email_ids = response[0].split()

        if not email_ids:

            print(
                f"[{email_address}] "
                f"Inbox is empty"
            )

            mail.logout()

            return

        latest_email_id = email_ids[-1]

        status, msg_data = mail.fetch(
            latest_email_id,
            '(RFC822)'
        )

        for response_part in msg_data:

            if isinstance(response_part, tuple):

                msg = email.message_from_bytes(
                    response_part[1]
                )

                print(f"\n[{email_address}]")

                print(
                    "Subject:",
                    msg['subject']
                )

                if msg.is_multipart():

                    for part in msg.walk():

                        if (
                            part.get_content_type()
                            == "text/plain"
                        ):

                            body = part.get_payload(
                                decode=True
                            ).decode('utf-8')

                            print("Body:")
                            print(body)

                            break

                else:

                    body = msg.get_payload(
                        decode=True
                    ).decode('utf-8')

                    print("Body:")
                    print(body)

        mail.logout()

        # ===== End Time =====
        end_time = time.time()

        imap_latency = end_time - start_time

        print(
            f"IMAP Latency: "
            f"{imap_latency:.4f} seconds"
        )

        send_notification(
            f"{email_address}: "
            f"Email Received Successfully"
        )

    except Exception as e:

        print(
            f"[{email_address}] "
            f"Receive Error: {e}"
        )

        send_notification(
            f"{email_address}: "
            f"Email Receiving Failed"
        )


# ==========================================
# Monitor Unread Emails
# ==========================================
def monitor_unread_emails(
        email_address,
        password
):

    previous_count = -1

    while True:

        try:

            imap_server = 'imap.ethereal.email'
            imap_port = 993

            mail = imaplib.IMAP4_SSL(
                imap_server,
                imap_port
            )

            mail.login(
                email_address,
                password
            )

            mail.select('inbox')

            status, response = mail.search(
                None,
                'UNSEEN'
            )

            unread_ids = response[0].split()

            unread_count = len(unread_ids)

            if unread_count != previous_count:

                if unread_count > 0:

                    message = (
                        f"{email_address}: "
                        f"You have "
                        f"{unread_count} "
                        f"unread emails"
                    )

                else:

                    message = (
                        f"{email_address}: "
                        f"All emails "
                        f"have been read"
                    )

                print(message)

                send_notification(message)

                previous_count = unread_count

            mail.logout()

        except Exception as e:

            print(
                f"[{email_address}] "
                f"Monitoring Error: {e}"
            )

        time.sleep(10)


# ==========================================
# Main
# ==========================================
if __name__ == "__main__":

    clients = [


        (
            "ralph10@ethereal.email",
            "PwGa8JdhGGVptSCM7F"
        )
    ]

    # Start monitoring thread
    for email_address, password in clients:

        monitor_thread = threading.Thread(
            target=monitor_unread_emails,
            args=(email_address, password)
        )

        monitor_thread.daemon = True

        monitor_thread.start()

    # Test send + receive
    for email_address, password in clients:

        print(f"\n--- Testing {email_address} ---")

        send_email(
            email_address,
            password,
            "delpha.gislason97@ethereal.email",
            "CN Project Test",
            "Hello from Multi-Client Email System"
        )

        receive_latest_email(
            email_address,
            password
        )

    while True:
        time.sleep(1)