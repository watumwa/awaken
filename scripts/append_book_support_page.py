#!/usr/bin/env python3
"""Append the branded Awakening Saints support page to published book PDFs.

The command is intentionally idempotent: a PDF whose final page contains the
embedded support-page marker is skipped. It renders one A4 back-matter page,
appends it without rasterising the book, validates the new page count, and only
then replaces the original file.
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

import qrcode
import qrcode.image.svg


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = PROJECT_ROOT / "media" / "books"
TEMPLATE_PATH = Path(__file__).with_name("book_support_page.html")
SUPPORT_MARKER = "AWAKENING-SAINTS-SUPPORT-PAGE-V1"
WHATSAPP_NUMBER = "256706344822"
WHATSAPP_MESSAGE = (
    "Hello Pastor Denis, I read one of your books and would like to connect."
)

PUBLISHED_BOOKS = (
    "Adultery_3.pdf",
    "FREEDOM_IGNORED-11111.pdf",
    "Generational_mandate_Final-1.pdf",
    "MARRIAGE.pdf",
    "MUSIC_3.pdf",
    "SPIRITUAL_FATHERSs.pdf",
    "SPIRITUAL_MATURITY.pdf",
    "THE_CRISIS_OF_SELF.pdf",
    "THE_WATCHMANS_CALL_2.pdf",
    "WHEN_GOD_INTERRUPTS_YOUR_LABOUR_3.pdf",
    "masturbation_3.pdf",
)


def require_command(*names: str) -> str:
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise RuntimeError(f"Required command not found: {' or '.join(names)}")


def run(command: list[str], *, capture: bool = False) -> str:
    try:
        result = subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or "").strip()
        command_name = Path(command[0]).name
        raise RuntimeError(
            f"{command_name} failed with exit code {exc.returncode}"
            + (f": {details}" if details else ".")
        ) from exc
    return result.stdout if capture else ""


def page_count(pdfinfo: str, pdf_path: Path) -> int:
    output = run([pdfinfo, str(pdf_path)], capture=True)
    for line in output.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError(f"Could not read page count from {pdf_path}")


def already_has_support_page(
    pdfinfo: str, pdftotext: str, pdf_path: Path
) -> bool:
    final_page = page_count(pdfinfo, pdf_path)
    text = run(
        [pdftotext, "-f", str(final_page), "-l", str(final_page), str(pdf_path), "-"],
        capture=True,
    )
    return SUPPORT_MARKER in text


def build_qr_svg() -> str:
    contact_url = (
        f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(WHATSAPP_MESSAGE)}"
    )
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(contact_url)
    qr.make(fit=True)
    image = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    output = io.BytesIO()
    image.save(output)
    svg = output.getvalue().decode("utf-8")
    return svg.replace("<svg ", '<svg class="generated-qr" aria-hidden="true" ')


def render_support_pdf(chrome: str, work_dir: Path) -> Path:
    html = TEMPLATE_PATH.read_text(encoding="utf-8").replace(
        "{{QR_SVG}}", build_qr_svg()
    )
    html_path = work_dir / "support-page.html"
    pdf_path = work_dir / "support-page.pdf"
    html_path.write_text(html, encoding="utf-8")

    run(
        [
            chrome,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            f"--user-data-dir={work_dir / 'chrome-profile'}",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ]
    )
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        raise RuntimeError("Chrome did not produce the support-page PDF.")
    return pdf_path


def append_page(
    pdfunite: str,
    pdfinfo: str,
    book_path: Path,
    support_pdf: Path,
    work_dir: Path,
) -> None:
    original_pages = page_count(pdfinfo, book_path)
    output_path = work_dir / f"{book_path.stem}-with-support.pdf"
    original_mode = book_path.stat().st_mode

    run([pdfunite, str(book_path), str(support_pdf), str(output_path)])
    appended_pages = page_count(pdfinfo, output_path)
    if appended_pages != original_pages + 1:
        raise RuntimeError(
            f"Validation failed for {book_path.name}: expected "
            f"{original_pages + 1} pages, found {appended_pages}."
        )

    os.chmod(output_path, original_mode)
    os.replace(output_path, book_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "books",
        nargs="*",
        type=Path,
        help="Optional PDF paths. Defaults to every published book in the library.",
    )
    parser.add_argument(
        "--render-only",
        type=Path,
        metavar="OUTPUT",
        help="Render the support page for review without changing any books.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chrome = require_command("google-chrome", "chromium", "chromium-browser")
    pdfinfo = require_command("pdfinfo")
    pdftotext = require_command("pdftotext")
    pdfunite = require_command("pdfunite")

    with tempfile.TemporaryDirectory(prefix="awakening-support-page-") as temp_name:
        work_dir = Path(temp_name)
        support_pdf = render_support_pdf(chrome, work_dir)

        if page_count(pdfinfo, support_pdf) != 1:
            raise RuntimeError("The support-page layout overflowed beyond one A4 page.")

        if args.render_only:
            destination = args.render_only.resolve()
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(support_pdf, destination)
            print(f"Rendered support page: {destination}")
            return 0

        books = [path.resolve() for path in args.books] or [
            BOOKS_DIR / filename for filename in PUBLISHED_BOOKS
        ]
        changed = 0
        skipped = 0

        for book_path in books:
            if not book_path.is_file():
                raise FileNotFoundError(f"Book PDF not found: {book_path}")
            if book_path.suffix.lower() != ".pdf":
                raise ValueError(f"Book is not a PDF: {book_path}")

            if already_has_support_page(pdfinfo, pdftotext, book_path):
                print(f"Skipped (already attached): {book_path.name}")
                skipped += 1
                continue

            append_page(pdfunite, pdfinfo, book_path, support_pdf, work_dir)
            print(f"Attached support page: {book_path.name}")
            changed += 1

        print(f"Done. Updated {changed} book(s); skipped {skipped}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
