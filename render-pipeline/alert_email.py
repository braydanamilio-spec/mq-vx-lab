"""
alert_email.py — Gửi email CẢNH BÁO (free, chống spam) qua Gmail SMTP.
Chống spam: run_render gọi 1 LẦN cuối mỗi lần chạy, CHỈ khi có lỗi (gộp tất cả vào 1 email).

Secrets cần (GitHub): SMTP_USER (gmail gửi), SMTP_PASS (App Password 16 ký tự), ALERT_EMAIL (nơi nhận).
Không đủ 3 biến -> bỏ qua (không gửi, không crash).
"""
from __future__ import annotations
import os
import smtplib
from email.message import EmailMessage


def send_alert(subject: str, body: str) -> bool:
    user = os.environ.get("SMTP_USER")
    pw = os.environ.get("SMTP_PASS")
    to = os.environ.get("ALERT_EMAIL")
    if not (user and pw and to):
        print("   (bỏ qua email: thiếu SMTP_USER/SMTP_PASS/ALERT_EMAIL)")
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to
        msg.set_content(body)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
            s.login(user, pw)
            s.send_message(msg)
        print(f"   📧 đã gửi cảnh báo -> {to}")
        return True
    except Exception as e:
        print(f"   ⚠️ gửi email lỗi: {e}")
        return False
