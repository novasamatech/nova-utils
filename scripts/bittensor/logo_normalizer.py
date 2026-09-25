import io

import cairosvg
from PIL import Image

SIZE = 256
_SVG_PROLOGS = (b"<svg", b"<?xml", b"<!--")


class LogoError(Exception):
    pass


def _is_svg(raw: bytes) -> bool:
    head = raw[:4096].lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    return head.startswith(_SVG_PROLOGS) and b"<svg" in head and b"<html" not in head


def _open_svg(raw: bytes) -> Image.Image:
    def render(**kwargs) -> Image.Image:
        # unsafe=False (the default) makes cairosvg resolve only data: URLs, so untrusted
        # SVGs cannot make the job fetch arbitrary URLs or local files.
        png = cairosvg.svg2png(bytestring=raw, unsafe=False, **kwargs)
        return Image.open(io.BytesIO(png))

    try:
        natural = render()
        # Re-render at the target size instead of upscaling a tiny bitmap.
        return render(scale=SIZE / max(natural.size))
    except Exception as e:
        raise LogoError(f"cannot render SVG: {e!r}") from e


def _open_raster(raw: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
        return img
    except Exception as e:
        raise LogoError(f"cannot decode image: {e!r}") from e


def _fit(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    scale = SIZE / max(img.size)
    width, height = max(1, round(img.width * scale)), max(1, round(img.height * scale))
    img = img.resize((width, height), Image.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(img, ((SIZE - width) // 2, (SIZE - height) // 2))
    return canvas


def normalize(raw: bytes) -> bytes:
    """Return a SIZE×SIZE RGBA PNG for any supported logo, or raise LogoError."""
    img = _open_svg(raw) if _is_svg(raw) else _open_raster(raw)
    out = io.BytesIO()
    _fit(img).save(out, "PNG", compress_level=9)
    return out.getvalue()
