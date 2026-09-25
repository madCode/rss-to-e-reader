from base_classes.sender import Sender
from email.message import EmailMessage
import mimetypes
import os
import smtplib
import ssl
from typing import Callable, List, Optional, Union

# Amazon rejects Send to Kindle emails over 50MB. Many providers' limits are lower (Gmail: 25MB).
KINDLE_EMAIL_LIMIT_BYTES = 50 * 1024 * 1024

MEDIA_TYPES = {
    '.epub': 'application/epub+zip',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.pdf': 'application/pdf',
    '.txt': 'text/plain',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

def media_type_for(filepath: str) -> str:
    extension = os.path.splitext(filepath)[1].lower()
    return MEDIA_TYPES.get(extension) or mimetypes.guess_type(filepath)[0] or 'application/octet-stream'

"""
SmtpSender emails a file through any SMTP server.

For Send to Kindle, add the from_email address to the Approved Personal Document E-mail List at
amazon.com/myk (Preferences -> Personal Document Settings) and send to your device's @kindle.com address.

Works with:
- Gmail: needs 2-Step Verification and an App Password (myaccount.google.com/apppasswords). See SmtpSender.gmail().
- Fastmail, iCloud, Outlook/Proton (via Bridge), ...: use the provider's SMTP settings and an app-specific password.
- Transactional email services (Resend, Brevo, Postmark, Mailgun, SendGrid...), which all offer SMTP relays with
  API-key logins. See also ResendSender, which uses Resend's HTTP API when SMTP ports are blocked.
"""
class SmtpSender(Sender):
    def __init__(
        self, to_emails: Union[str, List[str]], from_email: str, smtp_host: str, smtp_port: int = 465,
        password: str = "", username: Optional[str] = None, security: str = "ssl", timeout: float = 60,
        error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print):
        """
        Parameters
        ----------
        to_emails: str or List[str]
            Where to send the file, e.g. your_name@kindle.com
        from_email: str
            The address the email comes from. Must be on your Kindle's approved sender list.
        smtp_host: str
            e.g. smtp.gmail.com, smtp.fastmail.com, smtp.resend.com
        smtp_port: int, optional
            Defaults to 465 (implicit TLS). Use 587 with security="starttls".
        password: str, optional
            SMTP password, app password or API key.
        username: str, optional
            SMTP username if it differs from from_email (e.g. "resend" or "apikey").
        security: str, optional
            "ssl" (implicit TLS, usually port 465), "starttls" (usually port 587) or "none". Defaults to "ssl".
        timeout: float, optional
            Seconds to wait on the SMTP server. Defaults to 60.
        """
        super().__init__(error_log_callback, info_log_callback)
        if security not in ("ssl", "starttls", "none"):
            raise ValueError('security must be "ssl", "starttls" or "none"')
        self.to_emails = [to_emails] if isinstance(to_emails, str) else list(to_emails)
        self.from_email = from_email
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.password = password
        self.username = username if username is not None else from_email
        self.security = security
        self.timeout = timeout

    @classmethod
    def gmail(cls, gmail_address: str, app_password: str, to_emails: Union[str, List[str]], **kwargs) -> 'SmtpSender':
        """
        Sends through Gmail. Google no longer accepts your normal password from scripts: turn on
        2-Step Verification, then create an App Password at https://myaccount.google.com/apppasswords.
        (Some Google Workspace admins disable App Passwords; use another provider or ResendSender then.)
        """
        return cls(to_emails, gmail_address, 'smtp.gmail.com', 465, app_password.replace(' ', ''), **kwargs)

    def build_message(self, filepath: str, subject: str = "", body: str = "") -> EmailMessage:
        filename = os.path.basename(filepath)
        msg = EmailMessage()
        msg['Subject'] = subject or os.path.splitext(filename)[0]
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.to_emails)
        msg.set_content(body or f'Attached: {filename}')
        maintype, subtype = media_type_for(filepath).split('/', 1)
        with open(filepath, 'rb') as fp:
            msg.add_attachment(fp.read(), maintype=maintype, subtype=subtype, filename=filename)
        return msg

    def _connect(self) -> smtplib.SMTP:
        context = ssl.create_default_context()
        if self.security == "ssl":
            return smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=self.timeout, context=context)
        server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.timeout)
        if self.security == "starttls":
            server.starttls(context=context)
        return server

    def send(self, filepath: str, subject: str = "", body: str = "") -> bool:
        try:
            size = os.path.getsize(filepath)
            if size > KINDLE_EMAIL_LIMIT_BYTES:
                self.log_error(f'{filepath} is {size // (1024 * 1024)}MB; Send to Kindle rejects emails over 50MB.')
            msg = self.build_message(filepath, subject, body)
            with self._connect() as server:
                if self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
            self.log_info(f'Emailed {filepath} to {", ".join(self.to_emails)}')
            return True
        except Exception as e:
            self.log_error(f'Unable to send email: {e}')
            return False
