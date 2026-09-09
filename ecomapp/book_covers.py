"""Generate lightweight web covers from uploaded PDF books."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import pypdfium2 as pdfium
from django.core.files.base import ContentFile
from django.utils.text import slugify
from PIL import Image


logger = logging.getLogger(__name__)

MAX_COVER_WIDTH = 960
MAX_COVER_HEIGHT = 1440
WEBP_QUALITY = 84


class CoverGenerationError(Exception):
    """Raised when a PDF exists but its first page cannot become a cover."""


def is_pdf_book(product) -> bool:
    """Return whether a product has a PDF file, including remote storage URLs."""
    if not product.book_file:
        return False
    file_path = urlparse(str(product.book_file.name)).path
    return Path(file_path).suffix.lower() == ".pdf"


def can_generate_cover(product) -> bool:
    """Only fill missing/legacy covers; an administrator's cover always wins."""
    return is_pdf_book(product) and not product.has_usable_cover


def render_pdf_first_page(pdf_bytes: bytes) -> bytes:
    """Render a PDF's first page and return an optimized WebP image."""
    document = None
    page = None
    bitmap = None

    try:
        document = pdfium.PdfDocument(pdf_bytes)
        if len(document) < 1:
            raise ValueError("The PDF does not contain any pages.")

        page = document[0]
        page_width, page_height = page.get_size()
        if page_width <= 0 or page_height <= 0:
            raise ValueError("The PDF first page has invalid dimensions.")

        scale = min(
            MAX_COVER_WIDTH / page_width,
            MAX_COVER_HEIGHT / page_height,
        )
        # Avoid excessive upscaling of unusually small PDF pages.
        scale = max(0.1, min(scale, 3.0))

        bitmap = page.render(scale=scale)
        rendered = bitmap.to_pil().convert("RGB").copy()
        rendered.thumbnail(
            (MAX_COVER_WIDTH, MAX_COVER_HEIGHT),
            Image.Resampling.LANCZOS,
        )

        output = BytesIO()
        rendered.save(
            output,
            format="WEBP",
            quality=WEBP_QUALITY,
            method=6,
        )
        return output.getvalue()
    except Exception as exc:
        raise CoverGenerationError(
            "The first PDF page could not be converted into a cover image."
        ) from exc
    finally:
        if bitmap is not None:
            bitmap.close()
        if page is not None:
            page.close()
        if document is not None:
            document.close()


def generate_product_cover(product) -> bool:
    """Generate and save a missing product cover from its PDF's first page.

    The file is opened through Django storage instead of using ``.path`` so the
    same code works with local Namecheap files and remote object storage.
    """
    if not can_generate_cover(product):
        return False

    try:
        with product.book_file.open("rb") as book_file:
            pdf_bytes = book_file.read()
        cover_bytes = render_pdf_first_page(pdf_bytes)

        filename_base = slugify(product.title)[:80] or f"book-{product.pk}"
        product.product_image.save(
            f"{filename_base}-cover.webp",
            ContentFile(cover_bytes),
            save=False,
        )
        product.save(update_fields=("product_image", "updated"))
    except CoverGenerationError:
        raise
    except Exception as exc:
        logger.exception("Automatic cover generation failed for product %s", product.pk)
        raise CoverGenerationError(
            "The generated cover could not be saved."
        ) from exc

    return True
