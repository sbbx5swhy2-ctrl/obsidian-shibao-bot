"""
邮件发送模块 - Resend API + SMTP 双模发送
"""

import os
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request
from typing import Optional
from src.logger import get_logger

RESEND_API = "https://api.resend.com/emails"


class EmailSender:
    """Resend API + SMTP 双模邮件发送器"""

    def __init__(self):
        self.api_key = os.environ.get("SHIBAO_RESEND_KEY", "")
        self.to_addr = os.environ.get("SHIBAO_EMAIL_TO", "")
        self.from_addr = os.environ.get("SHIBAO_EMAIL_FROM", "onboarding@resend.dev")

    def is_configured(self) -> bool:
        """至少有一种发送方式已配置"""
        has_resend = bool(self.api_key and self.to_addr)
        has_smtp = bool(
            os.environ.get("SHIBAO_EMAIL_USER") and
            os.environ.get("SHIBAO_EMAIL_PASS") and
            self.to_addr
        )
        return has_resend or has_smtp

    def send_dual(self, html_body: str, md_content: str, subject: str) -> bool:
        logger = get_logger()
        if not self.is_configured():
            logger.error("邮件未配置：缺少必要环境变量")
            return False

        # 先试 Resend API
        logger.info("尝试通过 Resend API 发送...")
        ok1 = self._send_via_resend(html_body, subject, is_html=True)
        ok2 = self._send_via_resend(md_content, f"{subject} [Markdown]", is_html=False)

        if ok1 and ok2:
            logger.info("Resend 发送成功！")
            return True

        # Resend 失败，回退到 SMTP
        logger.info("Resend 失败，回退到 SMTP...")
        smtp_ok1 = self._send_via_smtp(html_body, subject, is_html=True)
        smtp_ok2 = self._send_via_smtp(md_content, f"{subject} [Markdown]", is_html=False)
        return smtp_ok1 and smtp_ok2

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
                logger.info(f"Resend 邮件已发送 → {self.to_addr} (id: {result.get('id', '?')})")
                return True

        except Exception as e:
            logger.error(f"Resend 发送失败: {e}")
            return False

    def _send_via_smtp(self, content: str, subject: str, is_html: bool) -> bool:
        logger = get_logger()
        smtp_user = os.environ.get("SHIBAO_EMAIL_USER", "")
        smtp_pass = os.environ.get("SHIBAO_EMAIL_PASS", "")

        if not smtp_user or not smtp_pass:
            logger.error("SMTP 未配置：缺少 SHIBAO_EMAIL_USER 或 SHIBAO_EMAIL_PASS")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = self.to_addr

            subtype = "html" if is_html else "plain"
            msg.attach(MIMEText(content, subtype, "utf-8"))

            ctx = ssl.create_default_context()
            with smtplib.SMTP("smtp-mail.outlook.com", 587, timeout=30) as server:
                server.starttls(context=ctx)
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [self.to_addr], msg.as_string())

            content_type = "HTML" if is_html else "Markdown"
            logger.info(f"SMTP 邮件已发送 ({content_type}) → {self.to_addr}")
            return True

        except Exception as e:
            logger.error(f"SMTP 发送失败: {e}")
            return False
