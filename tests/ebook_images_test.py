import base64
import unittest
from unittest.mock import MagicMock, patch

import requests

import default_modules.ebook_images as ebook_images
from default_modules.ebook_images import download_image

def streamed(chunks, status=200):
    response = MagicMock()
    response.status_code = status
    response.iter_content.return_value = iter(chunks)
    if status >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(str(status))
    return response

class TestDownloadImage(unittest.TestCase):
    def test_streams_the_image_with_image_headers(self):
        with patch.object(requests, 'get', return_value=streamed([b'ab', b'cd'])) as get:
            data = download_image('https://cdn.example.com/a.jpg', referer='https://example.com/article', timeout=5)
        self.assertEqual(data, b'abcd')
        headers = get.call_args.kwargs['headers']
        self.assertEqual(headers['Referer'], 'https://example.com/article')
        self.assertTrue(headers['Accept'].startswith('image/'))
        self.assertEqual(get.call_args.kwargs['timeout'], 5)
        self.assertTrue(get.call_args.kwargs['stream'])

    def test_uses_the_session(self):
        session = MagicMock()
        session.get.return_value = streamed([b'x'])
        with patch.object(requests, 'get') as get:
            self.assertEqual(download_image('https://cdn.example.com/a.png', session=session), b'x')
        get.assert_not_called()
        self.assertNotIn('Referer', session.get.call_args.kwargs['headers'])

    def test_stops_at_the_size_limit(self):
        with patch.object(ebook_images, 'MAX_DOWNLOAD_BYTES', 3), \
             patch.object(requests, 'get', return_value=streamed([b'ab', b'cd'])):
            self.assertIsNone(download_image('https://cdn.example.com/huge.jpg'))

    def test_errors_return_none(self):
        with patch.object(requests, 'get', return_value=streamed([], status=404)):
            self.assertIsNone(download_image('https://cdn.example.com/missing.jpg'))
        with patch.object(requests, 'get', side_effect=requests.ConnectionError('down')):
            self.assertIsNone(download_image('https://cdn.example.com/a.jpg'))

    def test_svg_is_skipped_without_a_request(self):
        with patch.object(requests, 'get') as get:
            self.assertIsNone(download_image('https://cdn.example.com/logo.SVG?v=2'))
        get.assert_not_called()

    def test_data_uris(self):
        encoded = base64.b64encode(b'\x89PNG').decode()
        self.assertEqual(download_image(f'data:image/png;base64,{encoded}'), b'\x89PNG')
        self.assertEqual(download_image('data:text/plain,hello'), b'hello')
        self.assertIsNone(download_image('data:image/png;base64,abc'))  # bad padding
        self.assertIsNone(download_image('data:nonsense'))
