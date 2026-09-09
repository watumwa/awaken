import tempfile
from decimal import Decimal
from io import BytesIO
from unittest.mock import Mock

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from PIL import Image

from ecomapp.admin import ProductAdmin
from ecomapp.book_covers import CoverGenerationError, generate_product_cover
from ecomapp.models import Category, Product


def make_pdf_upload(filename="automatic-cover.pdf"):
    """Build a small real PDF without adding a binary fixture to the repository."""
    pdf = BytesIO()
    Image.new("RGB", (400, 600), "#102a43").save(pdf, format="PDF", resolution=72)
    return SimpleUploadedFile(
        filename,
        pdf.getvalue(),
        content_type="application/pdf",
    )


def make_image_upload(filename="manual-cover.jpg"):
    image = BytesIO()
    Image.new("RGB", (300, 450), "#1098e8").save(image, format="JPEG")
    return SimpleUploadedFile(
        filename,
        image.getvalue(),
        content_type="image/jpeg",
    )


class AutomaticBookCoverTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media_directory = tempfile.TemporaryDirectory()
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_directory.name)
        cls.media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.media_override.disable()
        cls.media_directory.cleanup()

    def setUp(self):
        self.creator = get_user_model().objects.create_user(
            email="cover-editor@example.com",
            first_name="Cover",
            last_name="Editor",
            password="test-password",
        )
        self.category = Category.objects.create(
            cat_name="Automatic Covers",
            cat_slug="automatic-covers",
        )

    def product_fields(self, **overrides):
        fields = {
            "category": self.category,
            "created_by": self.creator,
            "title": "A Book With an Automatic Cover",
            "author": "Awakening Saints",
            "product_slug": "a-book-with-an-automatic-cover",
            "product_price": Decimal("0.00"),
            "qty_in_stock": 0,
            "book_file": make_pdf_upload(),
        }
        fields.update(overrides)
        return fields

    def test_admin_upload_generates_optimized_cover_from_pdf_first_page(self):
        product = Product(**self.product_fields(created_by=None))
        request = RequestFactory().post("/admin/ecomapp/product/add/")
        request.user = self.creator
        product_admin = ProductAdmin(Product, AdminSite())
        product_admin.message_user = Mock()

        product_admin.save_model(request, product, form=None, change=False)

        product.refresh_from_db()
        self.assertTrue(product.product_image)
        self.assertTrue(product.product_image.name.endswith("-cover.webp"))
        with product.product_image.open("rb") as cover_file:
            cover = Image.open(cover_file)
            cover.load()

        self.assertEqual(cover.format, "WEBP")
        self.assertLessEqual(cover.width, 960)
        self.assertLessEqual(cover.height, 1440)
        product_admin.message_user.assert_called_once()

    def test_manual_cover_is_never_replaced(self):
        product = Product.objects.create(
            **self.product_fields(product_image=make_image_upload())
        )
        original_cover_name = product.product_image.name

        generated = generate_product_cover(product)

        product.refresh_from_db()
        self.assertFalse(generated)
        self.assertEqual(product.product_image.name, original_cover_name)

    def test_invalid_pdf_does_not_create_a_broken_cover(self):
        product = Product.objects.create(
            **self.product_fields(
                title="Invalid PDF",
                product_slug="invalid-pdf",
                book_file=SimpleUploadedFile(
                    "invalid.pdf",
                    b"This is not a PDF.",
                    content_type="application/pdf",
                ),
            )
        )

        with self.assertRaises(CoverGenerationError):
            generate_product_cover(product)

        product.refresh_from_db()
        self.assertFalse(product.product_image)
