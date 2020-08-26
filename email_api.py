import config
from email.message import EmailMessage
import smtplib

def send_email(article_ids, to_emails, filestub):
    try:
        msg = EmailMessage()
        msg.set_content("Articles: " + ", ".join(article_ids))

        msg['Subject'] = f'To Kindle: {filestub}'
        msg['From'] = config.email_user
        msg['To'] = to_emails

        fn = filestub + '.html'

        with open(fn, 'rb') as fp:
            data = fp.read()
            ctype = 'application/hta'
            maintype, subtype = ctype.split('/', 1)
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=fn)

        server = smtplib.SMTP_SSL(config.smtp_url, config.smtp_port)
        server.ehlo()
        server.login(config.email_user, config.email_password)
        server.send_message(msg)
        server.close()
        print('Email sent!')
    except Exception as e:
        print(f'Unable to send emails: {str(e)}')