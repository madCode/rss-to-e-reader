"""
Kept for backwards compatibility. New code should use a Sender: SmtpSender, ResendSender or FolderSender.
"""
from default_modules.SmtpSender import SmtpSender
from typing import List, Union

def default_send_file_in_email(
        to_emails: Union[str, List[str]], filestub: str, email_user: str,
        smtp_url: str, smtp_port: int, email_password: str, article_ids = [], file_extension: str = '.html'
    ) -> bool:
    sender = SmtpSender(to_emails, email_user, smtp_url, smtp_port, email_password)
    return sender.send(filestub + file_extension, subject='Articles', body="Articles: " + ", ".join(article_ids))
