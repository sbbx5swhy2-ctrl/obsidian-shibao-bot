"""
邮件发送模块 - 通过 SMTP 发送邮件
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
from src.logger import get_logger


class EmailSender:
    """SMTP 邮件发送器"""

    def __init__(self):
        self.smtp_host = os.environ.get("SHIBAO_SMTP_HOST", "smtp-mail.outlook.com")
        self.smtp_port = int(os.environ.get("SHIBAO_SMTP_PORT", "587"))
        self.username = os.environ.get("SHIBAO_EMAIL_USER", "")
        self.password = os.environ.get("SHIBAO_EMAIL_PASS", "")
        self.to_addr = os.environ.get("SHIBAO_EMAIL_TO", "")
        self.from_addr = os.environ.get("SHIBAO_EMAIL_FROM", self.username)

    def is_configured(self) -> bool:
        """检查邮件配置是否完整"""
        return bool(self.username and self.password and self.to_addr)

    def send_dual(
        self,
        html_body: str,
        md_content: str,
        subject: str,
    ) -> bool:
        """发送两份邮件：一份 HTML 正文，一份 Markdown 附件"""
        logger = get_logger()
        if not self.is_configured():
            logger.error("邮件未配置：缺少 SHIBAO_EMAIL_USER / SHIBAO_EMAIL_PASS / SHIBAO_EMAIL_TO")
            return False

        success = True
        # 邮件 1: HTML 正文
        if not self._send_html(html_body, subject):
            success = False
        # 邮件 2: Markdown 附件
        if not self._send_markdown_attachment(md_content, f"{subject} [Markdown]"):
            success = False

        return success

    def _send_html(self, html_body: str, subject: str) -> bool:
        """发送 HTML 邮件"""
        logger = get_logger()
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = self.to_addr

            msg.attach(MIMEText(html_body, "html", "utf-8"))

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.from_addr, self.to_addr, msg.as_string())

            logger.info(f"HTML 邮件已发送 → {self.to_addr}")
            return True
        except Exception as e:
            logger.error(f"HTML 邮件发送失败: {e}")
            return False

    def _send_markdown_attachment(self, md_content: str, subject: str) -> bool:
        """发送带 Markdown 附件的邮件"""
        logger = get_logger()
        try:
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = self.to_addr

            # 简短的文本正文
            text_body = "📎 时报 Markdown 文档见附件。\n\n打开方式：用 Obsidian / Typora / VS Code 等 Markdown 编辑器打开。"
            msg.attach(MIMEText(text_body, "plain", "utf-8"))

            # Markdown 附件
            part = MIMEBase("application", "octet-stream")
            part.set_payload(md_content.encode("utf-8"))
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="时报-{subject.replace("[Markdown]", "").strip()}.md"',
            )
            msg.attach(part)

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.from_addr, self.to_addr, msg.as_string())

            logger.info(f"Markdown 附件邮件已发送 → {self.to_addr}")
            return True
        except Exception as e:
            logger.error(f"Markdown 邮件发送失败: {e}")
            return False
