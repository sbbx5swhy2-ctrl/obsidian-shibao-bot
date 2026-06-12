"""
邮件发送模块 - 通过 Resend HTTP API 发送邮件
"""

import os
import json
import urllib.request
from typing import Optional
from src.logger import get_logger

RESEND_API = "https://api.resend.com/emails"


class EmailSender:
    """Resend API 邮件发送器"""

    def __init__(self):
        self.api_key = os.environ.get("SHIBAO_RESEND_KEY", "")
        self.to_addr = os.environ.get("SHIBAO_EMAIL_TO", "")
        self.from_addr = os.environ.get("SHIBAO_EMAIL_FROM", "onboarding@resend.dev")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.to_addr)

    def send_dual(self, html_body: str, md_content: str, subject: str) -> bool:
        logger = get_logger()
        if not self.is_configured():
            logger.error("邮件未配置：缺少 SHIBAO_RESEND_KEY 或 SHIBAO_EMAIL_TO")
            return False

        ok1 = self._send_via_resend(html_body, subject, is_html=True)
        ok2 = self._send_via_resend(md_content, f"{subject} [Markdown]", is_html=False)
        return ok1 and ok2

    def _send_via_resend(self, content: str, subject: str, is_html: bool) -> bool:
        logger = get_logger()
        try:
            payload = {
                "from": self.from_addr,
                "to": [self.to_addr],
                "subject": subject,
            }
            if is_html:
                payload["html"] = content
            else:
                payload["text"] = content

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                RESEND_API,
                data=data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                logger.info(f"邮件已发送 → {self.to_addr} (id: {result.get('id', '?')})")
                return True

        except Exception as e:
            logger.error(f"Resend 发送失败: {e}")
            return False
