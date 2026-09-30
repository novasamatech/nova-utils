import io

import pytest
from PIL import Image

from scripts.bittensor.logo_normalizer import SIZE, LogoError, normalize


def encode(img: Image.Image, fmt: str) -> bytes:
    out = io.BytesIO()
    img.save(out, fmt)
    return out.getvalue()


def decode(png: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(png))
    assert img.format == "PNG"
    return img


@pytest.mark.parametrize("fmt, mode", [("PNG", "RGBA"), ("JPEG", "RGB"), ("WEBP", "RGBA"), ("GIF", "P")])
def test_raster_formats_become_256_rgba_png(fmt, mode):
    img = decode(normalize(encode(Image.new(mode, (40, 40)), fmt)))
    assert img.size == (SIZE, SIZE)
    assert img.mode == "RGBA"


def test_ico_uses_largest_frame():
    source = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
    img = decode(normalize(encode(source, "ICO")))
    assert img.size == (SIZE, SIZE)
    assert img.getpixel((SIZE // 2, SIZE // 2)) == (255, 0, 0, 255)


def test_svg_is_rasterised():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="#00ff00"/></svg>'
    img = decode(normalize(svg))
    assert img.size == (SIZE, SIZE)
    assert img.getpixel((SIZE // 2, SIZE // 2)) == (0, 255, 0, 255)


def test_svg_with_xml_prolog_is_rasterised():
    svg = b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"><rect width="4" height="4"/></svg>'
    assert decode(normalize(svg)).size == (SIZE, SIZE)


def test_non_square_keeps_aspect_with_transparent_padding():
    wide = Image.new("RGBA", (200, 100), (0, 0, 255, 255))
    img = decode(normalize(encode(wide, "PNG")))
    assert img.getpixel((SIZE // 2, 5)) == (0, 0, 0, 0)
    assert img.getpixel((SIZE // 2, SIZE // 2)) == (0, 0, 255, 255)
    assert img.getpixel((2, SIZE // 2)) == (0, 0, 255, 255)


def test_output_is_deterministic():
    raw = encode(Image.new("RGB", (33, 17), (10, 20, 30)), "JPEG")
    assert normalize(raw) == normalize(raw)


@pytest.mark.parametrize("raw", [
    b"<!DOCTYPE html><html><body><svg></svg></body></html>",
    b"<html><head></head></html>",
    b"not an image at all",
    b"",
])
def test_rejects_non_images(raw):
    with pytest.raises(LogoError):
        normalize(raw)


def test_svg_external_references_are_not_fetched():
    svg = (b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="4" height="4">'
           b'<image xlink:href="http://127.0.0.1:9/x.png" width="4" height="4"/></svg>')
    assert decode(normalize(svg)).size == (SIZE, SIZE)
