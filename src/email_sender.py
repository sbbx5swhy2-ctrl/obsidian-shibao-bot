"""
邮件发送模块 - Resend API + SMTP 双模发送
"""

import base64
import json
import os
import smtplib
import ssl
import urllib.request
from email.message import EmailMessage
from typing import List, Optional

from src.logger import get_logger

RESEND_API = "https://api.resend.com/emails"


class EmailSender:
    """Resend API + SMTP 双模邮件发送器"""

    def __init__(self):
        self.api_key = os.environ.get("SHIBAO_RESEND_KEY", "")
        self.to_addr = os.environ.get("SHIBAO_EMAIL_TO", "")
        self.from_addr = os.environ.get("SHIBAO_EMAIL_FROM") or "onboarding@resend.dev"
        self.smtp_host = os.environ.get("SHIBAO_SMTP_HOST") or "smtp-mail.outlook.com"
        self.smtp_port = int(os.environ.get("SHIBAO_SMTP_PORT") or "587")

    def is_configured(self) -> bool:
        """至少有一种发送方式已配置"""
        has_resend = bool(self.api_key and self.to_addr)
        has_smtp = bool(
            os.environ.get("SHIBAO_EMAIL_USER")
            and os.environ.get("SHIBAO_EMAIL_PASS")
            and self.to_addr
        )
        return has_resend or has_smtp

    def send_report(
        self,
        html_body: str,
        md_content: str,
        subject: str,
        attachment_filename: Optional[str] = None,
    ) -> bool:
        """发送一封日报邮件：HTML 正文 + Markdown 附件。"""
        logger = get_logger()
        if not self.is_configured():
            logger.error("邮件未配置：缺少必要环境变量")
            return False

        if attachment_filename is None:
            attachment_filename = self._default_attachment_filename(subject)

        if self.api_key:
            logger.info("尝试通过 Resend API 发送...")
            ok = self._send_via_resend(html_body, md_content, subject, attachment_filename)
            if ok:
                logger.info("Resend 发送成功！")
                return True

        logger.info("Resend 未配置或发送失败，回退到 SMTP...")
        return self._send_via_smtp(html_body, md_content, subject, attachment_filename)

    def send_dual(self, html_body: str, md_content: str, subject: str) -> bool:
        """兼容旧调用：现在改为一封邮件正文 + Markdown 附件。"""
        return self.send_report(html_body, md_content, subject)

    def _recipient_list(self) -> List[str]:
        """支持用逗号或分号配置多个收件人。"""
        normalized = self.to_addr.replace(";", ",")
        return [addr.strip() for addr in normalized.split(",") if addr.strip()]

    def _default_attachment_filename(self, subject: str) -> str:
        safe = subject.replace("|", "-").replace("/", "-").replace("\\", "-").strip()
        safe = safe or "shibao"
        return f"{safe}.md"

    def _build_resend_payload(
        self,
        html_body: str,
        md_content: str,
        subject: str,
        attachment_filename: str,
    ) -> dict:
        attachment = base64.b64encode(md_content.encode("utf-8")).decode("ascii")
        return {
            "from": self.from_addr,
            "to": self._recipient_list(),
            "subject": subject,
            "html": html_body,
            "text": md_content,
            "attachments": [
                {
                    "filename": attachment_filename,
                    "content": attachment,
                }
            ],
        }

    def _send_via_resend(
        self,
        html_body: str,
        md_content: str,
        subject: str,
        attachment_filename: str,
    ) -> bool:
        logger = get_logger()
        try:
            payload = self._build_resend_payload(
                html_body,
                md_content,
                subject,
                attachment_filename,
            )
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
                logger.info(f"Resend 邮件已发送 -> {self.to_addr} (id: {result.get('id', '?')})")
                return True

        except Exception as e:
            logger.error(f"Resend 发送失败: {e}")
            return False

    def _send_via_smtp(
        self,
        html_body: str,
        md_content: str,
        subject: str,
        attachment_filename: str,
    ) -> bool:
        logger = get_logger()
        smtp_user = os.environ.get("SHIBAO_EMAIL_USER", "")
        smtp_pass = os.environ.get("SHIBAO_EMAIL_PASS", "")
        recipients = self._recipient_list()

        if not smtp_user or not smtp_pass or not recipients:
            logger.error("SMTP 未配置：缺少 SHIBAO_EMAIL_USER、SHIBAO_EMAIL_PASS 或 SHIBAO_EMAIL_TO")
            return False

        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.from_addr or smtp_user
            msg["To"] = ", ".join(recipients)
            msg.set_content(md_content, subtype="plain", charset="utf-8")
            msg.add_alternative(html_body, subtype="html", charset="utf-8")
            msg.add_attachment(
                md_content.encode("utf-8"),
                maintype="text",
                subtype="markdown",
                filename=attachment_filename,
            )

            ctx = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls(context=ctx)
                server.login(smtp_user, smtp_pass)
                server.send_message(msg, from_addr=smtp_user, to_addrs=recipients)

            logger.info(f"SMTP 邮件已发送（HTML 正文 + Markdown 附件）-> {self.to_addr}")
            return True

        except Exception as e:
            logger.error(f"SMTP 发送失败: {e}")
            return False
