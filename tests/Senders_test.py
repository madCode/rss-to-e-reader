import base64
import os
import smtplib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

from custom_modules.FolderSender import FolderSender
from custom_modules.ResendSender import ResendSender
from default_modules.SmtpSender import SmtpSender, media_type_for
from default_modules.email_api import default_send_file_in_email

class SenderTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, 'Daily Reading.epub')
        with open(self.path, 'wb') as f:
            f.write(b'EPUB DATA')

    def tearDown(self):
        self.dir.cleanup()

class TestSmtpSender(SenderTestCase):
    def test_media_types(self):
        self.assertEqual(media_type_for('a.epub'), 'application/epub+zip')
        self.assertEqual(media_type_for('a.HTML'), 'text/html')
        self.assertEqual(media_type_for('a.unknownext'), 'application/octet-stream')

    def test_build_message(self):
        sender = SmtpSender(['a@kindle.com', 'b@kindle.com'], 'me@example.com', 'smtp.example.com', info_log_callback=None)
        msg = sender.build_message(self.path)
        self.assertEqual(msg['Subject'], 'Daily Reading')
        self.assertEqual(msg['To'], 'a@kindle.com, b@kindle.com')
        attachment = next(msg.iter_attachments())
        self.assertEqual(attachment.get_content_type(), 'application/epub+zip')
        self.assertEqual(attachment.get_filename(), 'Daily Reading.epub')
        self.assertEqual(attachment.get_content(), b'EPUB DATA')

    def test_send_ssl(self):
        server = MagicMock()
        with patch.object(smtplib, 'SMTP_SSL', return_value=server) as smtp_ssl:
            sent = SmtpSender.gmail('me@gmail.com', 'abcd efgh ijkl mnop', 'me@kindle.com', info_log_callback=None).send(self.path, 'Hi')
        self.assertTrue(sent)
        self.assertEqual(smtp_ssl.call_args.args, ('smtp.gmail.com', 465))
        server.__enter__.return_value.login.assert_called_once_with('me@gmail.com', 'abcdefghijklmnop')
        server.__enter__.return_value.send_message.assert_called_once()

    def test_send_starttls_and_failure(self):
        server = MagicMock()
        with patch.object(smtplib, 'SMTP', return_value=server):
            sender = SmtpSender('me@kindle.com', 'me@example.com', 'smtp.example.com', 587, 'key', username='apikey',
                                security='starttls', info_log_callback=None)
            self.assertTrue(sender.send(self.path))
        server.starttls.assert_called_once()
        server.__enter__.return_value.login.assert_called_once_with('apikey', 'key')

        errors = []
        with patch.object(smtplib, 'SMTP_SSL', side_effect=OSError('refused')):
            sender = SmtpSender('me@kindle.com', 'me@example.com', 'smtp.example.com', error_log_callback=errors.append)
            self.assertFalse(sender.send(self.path))
        self.assertIn('refused', errors[0])

    def test_invalid_security(self):
        self.assertRaises(ValueError, SmtpSender, 'a', 'b', 'c', security='tls')

    def test_legacy_email_api(self):
        with patch.object(SmtpSender, 'send', return_value=True) as send:
            self.assertTrue(default_send_file_in_email('me@kindle.com', self.path[:-5], 'me@x.com', 'smtp.x.com', 465, 'pw', ['1', '2'], '.epub'))
        self.assertEqual(send.call_args.args[0], self.path)

class TestResendSender(SenderTestCase):
    def test_send(self):
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"id": "abc"}'
        with patch.object(requests, 'post', return_value=response) as post:
            self.assertTrue(ResendSender('re_key', 'kindle@me.com', 'me@kindle.com', info_log_callback=None).send(self.path))
        self.assertEqual(post.call_args.kwargs['headers'], {'Authorization': 'Bearer re_key'})
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['to'], ['me@kindle.com'])
        self.assertEqual(payload['subject'], 'Daily Reading')
        self.assertEqual(payload['attachments'], [{'filename': 'Daily Reading.epub', 'content': base64.b64encode(b'EPUB DATA').decode()}])

    def test_api_error(self):
        response = requests.Response()
        response.status_code = 422
        response._content = b'{"message": "domain not verified"}'
        errors = []
        with patch.object(requests, 'post', return_value=response):
            self.assertFalse(ResendSender('re_key', 'kindle@me.com', 'me@kindle.com', error_log_callback=errors.append).send(self.path))
        self.assertIn('domain not verified', errors[0])

class TestFolderSender(SenderTestCase):
    def test_copies_and_prunes(self):
        folder = os.path.join(self.dir.name, 'sync', 'kobo')
        sender = FolderSender(folder, keep_last=2, info_log_callback=None)
        for i in range(3):
            path = os.path.join(self.dir.name, f'{i}.epub')
            with open(path, 'wb') as f:
                f.write(b'x')
            os.utime(path, (1000 + i, 1000 + i))
            self.assertTrue(sender.send(path))
        self.assertEqual(sorted(os.listdir(folder)), ['1.epub', '2.epub'])
