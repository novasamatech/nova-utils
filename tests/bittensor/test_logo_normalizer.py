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


def glyph_on_transparent(color, size=40):
    """A square mark in `color` on a transparent canvas, about a third of the pixels opaque."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img.paste(Image.new("RGBA", (size // 2, size // 2), color), (size // 4, size // 4))
    return img


def center(png):
    return decode(png).getpixel((SIZE // 2, SIZE // 2))


def test_black_mark_on_transparent_background_becomes_white():
    assert center(normalize(encode(glyph_on_transparent((0, 0, 0, 255)), "PNG"))) == (255, 255, 255, 255)


def test_dark_blue_mark_on_transparent_background_becomes_light_blue():
    r, g, b, a = center(normalize(encode(glyph_on_transparent((10, 30, 90, 255)), "PNG")))
    assert a == 255 and b >= 150 and b > r


def test_transparent_pixels_stay_transparent_when_a_mark_is_lightened():
    assert decode(normalize(encode(glyph_on_transparent((0, 0, 0, 255)), "PNG"))).getpixel((2, 2))[3] == 0


def test_bright_colored_mark_on_transparent_background_is_kept():
    assert center(normalize(encode(glyph_on_transparent((120, 60, 220, 255)), "PNG"))) == (120, 60, 220, 255)


def test_white_mark_on_opaque_black_square_is_kept():
    img = Image.new("RGBA", (40, 40), (0, 0, 0, 255))
    img.paste(Image.new("RGBA", (20, 20), (255, 255, 255, 255)), (10, 10))
    out = decode(normalize(encode(img, "PNG")))
    assert out.getpixel((SIZE // 2, SIZE // 2)) == (255, 255, 255, 255)
    assert out.getpixel((2, 2)) == (0, 0, 0, 255)


def test_black_mark_on_opaque_white_square_is_kept():
    img = Image.new("RGBA", (40, 40), (255, 255, 255, 255))
    img.paste(Image.new("RGBA", (20, 20), (0, 0, 0, 255)), (10, 10))
    assert center(normalize(encode(img, "PNG"))) == (0, 0, 0, 255)
