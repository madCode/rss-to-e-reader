from email.message import EmailMessage
import smtplib
from typing import List, Union

def default_send_file_in_email(
        to_emails: Union[str, List[str]], filestub: str, email_user: str,
        smtp_url: str, smtp_port: int, email_password: str, article_ids = []
    ):
    try:
        msg = EmailMessage()
        msg.set_content("Articles: " + ", ".join(article_ids))

        # this subject line is optimized for Kindle.
        #   Sending "Convert" in the subject line will ask the Kindle servers to try
        #   converting the file to be optimized for Kindle.
        msg['Subject'] = f'Convert' 
        msg['From'] = email_user
        msg['To'] = to_emails

        fn = filestub + '.html'

        with open(fn, 'rb') as fp:
            data = fp.read()
            ctype = 'application/hta'
            maintype, subtype = ctype.split('/', 1)
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=fn)

        server = smtplib.SMTP_SSL(smtp_url, smtp_port)
        server.ehlo()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.close()
        print('Email sent!')
    except Exception as e:
        print(f'Unable to send emails: {str(e)}')