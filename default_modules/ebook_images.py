"""
Downloads article images and shrinks them for e-readers.

E-ink screens are ~1264x1680 at most, many are grayscale, and Send-to-Kindle (and email in general) has size
limits, so every image is downscaled and re-encoded as a JPEG. Formats e-readers struggle with (webp, avif,
palette PNGs with transparency, animated GIFs) all come out as plain JPEGs. SVGs are dropped.
"""
import base64
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from io import BytesIO
import re
from typing import Dict, Iterable, Optional

from PIL import Image  # type: ignore
import requests

from default_modules.article_parser import DEFAULT_HEADERS

MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024
MIN_DIMENSION = 48  # smaller images are icons, avatars and spacers


@dataclass
class ProcessedImage:
    data: bytes
    width: int
    height: int
    media_type: str = 'image/jpeg'
    extension: str = 'jpg'


def process_image(data: bytes, max_dimension: int = 1200, grayscale: bool = False, quality: int = 80) -> Optional[ProcessedImage]:
    """Returns a downscaled JPEG version of the image, or None if it can't be read or is too small to matter."""
    try:
        opened = Image.open(BytesIO(data))
        opened.seek(0)  # first frame of animations
        opened.load()
        image: Image.Image = opened
    except Exception:
        return None
    if min(image.size) < MIN_DIMENSION:
        return None
    image.thumbnail((max_dimension, max_dimension))
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        image = image.convert('RGBA')
        background = Image.new('RGB', image.size, 'white')
        background.paste(image, mask=image.split()[-1])
        image = background
    image = image.convert('L' if grayscale else 'RGB')
    output = BytesIO()
    image.save(output, format='JPEG', quality=quality, optimize=True, progressive=False)
    return ProcessedImage(output.getvalue(), image.width, image.height)


def _data_uri_bytes(uri: str) -> Optional[bytes]:
    match = re.match(r'data:[^;,]*(;base64)?,(.*)', uri, re.S)
    if not match:
        return None
    try:
        return base64.b64decode(match.group(2)) if match.group(1) else match.group(2).encode('latin-1')
    except Exception:
        return None


def download_image(url: str, referer: str = '', timeout: float = 20, session: Optional[requests.Session] = None) -> Optional[bytes]:
    if url.startswith('data:'):
        return _data_uri_bytes(url)
    if url.lower().split('?')[0].endswith('.svg'):
        return None
    headers = dict(DEFAULT_HEADERS)
    headers['Accept'] = 'image/jpeg,image/png,image/gif,image/*;q=0.8'
    if referer:
        headers['Referer'] = referer
    getter = session.get if session is not None else requests.get
    try:
        response = getter(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        chunks = []
        size = 0
        for chunk in response.iter_content(64 * 1024):
            size += len(chunk)
            if size > MAX_DOWNLOAD_BYTES:
                return None
            chunks.append(chunk)
        return b''.join(chunks)
    except Exception:
        return None


def fetch_images(
    urls: Iterable[str], referer: str = '', max_dimension: int = 1200, grayscale: bool = False,
    quality: int = 80, timeout: float = 20, max_workers: int = 6, session: Optional[requests.Session] = None,
) -> Dict[str, ProcessedImage]:
    """Downloads and processes images in parallel. Images that fail are left out of the result."""
    unique = list(dict.fromkeys(urls))

    def work(url: str) -> Optional[ProcessedImage]:
        data = download_image(url, referer, timeout, session)
        return process_image(data, max_dimension, grayscale, quality) if data else None

    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
        results = executor.map(work, unique)
        return {url: image for url, image in zip(unique, results) if image is not None}
