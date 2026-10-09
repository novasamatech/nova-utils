import io

import cairosvg
from PIL import Image

SIZE = 256
_SVG_PROLOGS = (b"<svg", b"<?xml", b"<!--")

# The app draws logos straight onto its near-black background. A mark that brings no background of
# its own and is dark all over would vanish there, so its brightness is flipped while its hues stay.
MIN_TRANSPARENT_SHARE = 0.2
VISIBLE_VALUE = 100
MAX_VISIBLE_SHARE = 0.05


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


def _is_invisible_on_dark(img: Image.Image) -> bool:
    alpha = img.getchannel("A")
    opaque = alpha.point(lambda a: 255 if a > 128 else 0)
    opaque_count = opaque.histogram()[255]
    if opaque_count == 0 or 1 - opaque_count / (img.width * img.height) < MIN_TRANSPARENT_SHARE:
        return False

    value = img.convert("HSV").getchannel("V")
    bright = value.point(lambda v: 255 if v > VISIBLE_VALUE else 0)
    bright.paste(0, mask=opaque.point(lambda o: 255 - o))
    return bright.histogram()[255] / opaque_count < MAX_VISIBLE_SHARE


def _lighten_for_dark_ui(img: Image.Image) -> Image.Image:
    if not _is_invisible_on_dark(img):
        return img

    hue, saturation, value = img.convert("HSV").split()
    lightened = Image.merge("HSV", (hue, saturation, value.point(lambda v: 255 - v))).convert("RGBA")
    lightened.putalpha(img.getchannel("A"))
    return lightened


def normalize(raw: bytes) -> bytes:
    """Return a SIZE×SIZE RGBA PNG for any supported logo, or raise LogoError."""
    img = _open_svg(raw) if _is_svg(raw) else _open_raster(raw)
    out = io.BytesIO()
    _lighten_for_dark_ui(_fit(img)).save(out, "PNG", compress_level=9)
    return out.getvalue()
