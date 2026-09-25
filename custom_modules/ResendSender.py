from base_classes.sender import Sender
import base64
import os
import requests
from typing import Callable, List, Optional, Union

"""
ResendSender emails a file using Resend's HTTP API (https://resend.com). No SMTP, OAuth or app passwords:
just an API key, which makes it easy to run from cron, GitHub Actions or a cloud host that blocks SMTP ports.
The free tier (100 emails/day) is plenty for a daily digest.

Setup:
1. Create a Resend account, add and verify a domain you own, and create an API key.
2. Add the from_email address (e.g. kindle@yourdomain.com) to your Kindle's Approved Personal Document E-mail List
   at amazon.com/myk (Preferences -> Personal Document Settings).
"""
class ResendSender(Sender):
    API_URL = 'https://api.resend.com/emails'
    MAX_ATTACHMENT_BYTES = 40 * 1024 * 1024  # Resend's limit, after base64 encoding

    def __init__(
        self, api_key: str, from_email: str, to_emails: Union[str, List[str]], timeout: float = 120,
        error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print):
        """
        Parameters
        ----------
        api_key: str
            A Resend API key (starts with "re_"). Keep it out of your code, e.g. in an environment variable.
        from_email: str
            Sender address on your verified domain. Can include a name: "Reader <kindle@yourdomain.com>".
        to_emails: str or List[str]
            Where to send the file, e.g. your_name@kindle.com
        timeout: float, optional
            Seconds to wait for Resend's API. Defaults to 120.
        """
        super().__init__(error_log_callback, info_log_callback)
        self.api_key = api_key
        self.from_email = from_email
        self.to_emails = [to_emails] if isinstance(to_emails, str) else list(to_emails)
        self.timeout = timeout

    def send(self, filepath: str, subject: str = "", body: str = "") -> bool:
        filename = os.path.basename(filepath)
        try:
            with open(filepath, 'rb') as fp:
                encoded = base64.b64encode(fp.read()).decode('ascii')
            if len(encoded) > ResendSender.MAX_ATTACHMENT_BYTES:
                self.log_error(f'{filepath} is too large for Resend (40MB limit after encoding).')
                return False
            response = requests.post(
                ResendSender.API_URL,
                headers={'Authorization': f'Bearer {self.api_key}'},
                json={
                    'from': self.from_email,
                    'to': self.to_emails,
                    'subject': subject or os.path.splitext(filename)[0],
                    'text': body or f'Attached: {filename}',
                    'attachments': [{'filename': filename, 'content': encoded}],
                },
                timeout=self.timeout,
            )
            if response.status_code >= 300:
                self.log_error(f'Resend rejected the email ({response.status_code}): {response.text}')
                return False
            self.log_info(f'Emailed {filepath} to {", ".join(self.to_emails)} (Resend id {response.json().get("id")})')
            return True
        except Exception as e:
            self.log_error(f'Unable to send email through Resend: {e}')
            return False
