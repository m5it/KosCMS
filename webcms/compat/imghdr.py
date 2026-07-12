"""
Compatibility shim for imghdr module removed in Python 3.13+.
"""

import os


def what(file, h=None):
    """Determine image file type from file or bytes."""
    if h is None:
        with open(file, 'rb') as f:
            h = f.read(32)

    tests = [
        _test_jpeg,
        _test_png,
        _test_gif,
        _test_webp,
    ]

    for test in tests:
        result = test(h, file)
        if result:
            return result
    return None


def _test_jpeg(h, f):
    if h[:2] == b'\xff\xd8':
        return 'jpeg'
    return None


def _test_png(h, f):
    if h[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    return None


def _test_gif(h, f):
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    return None


def _test_webp(h, f):
    if h[:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'
    return None
