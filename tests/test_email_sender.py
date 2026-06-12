"""
测试：邮件发送 payload
"""

import base64
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.email_sender import EmailSender


def test_resend_payload_contains_markdown_attachment(monkeypatch):
    """Resend payload 应包含 HTML 正文、文本 fallback 和 Markdown 附件"""
    monkeypatch.setenv("SHIBAO_RESEND_KEY", "test-key")
    monkeypatch.setenv("SHIBAO_EMAIL_TO", "a@example.com;b@example.com")
    monkeypatch.setenv("SHIBAO_EMAIL_FROM", "bot@example.com")

    sender = EmailSender()
    payload = sender._build_resend_payload(
        html_body="<h1>日报</h1>",
        md_content="# 日报\n\n正文",
        subject="时报 | 2026-06-12",
        attachment_filename="shibao-2026-06-12.md",
    )

    assert payload["from"] == "bot@example.com"
    assert payload["to"] == ["a@example.com", "b@example.com"]
    assert payload["html"] == "<h1>日报</h1>"
    assert payload["text"] == "# 日报\n\n正文"
    assert payload["attachments"][0]["filename"] == "shibao-2026-06-12.md"
    assert base64.b64decode(payload["attachments"][0]["content"]).decode("utf-8") == "# 日报\n\n正文"


def test_default_attachment_filename_is_markdown(monkeypatch):
    """默认附件名应可作为 Markdown 文件名使用"""
    monkeypatch.setenv("SHIBAO_EMAIL_TO", "me@example.com")

    sender = EmailSender()

    assert sender._default_attachment_filename("时报 | 2026-06-12") == "时报 - 2026-06-12.md"
