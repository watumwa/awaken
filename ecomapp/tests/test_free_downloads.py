import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from ecomapp.models import Category, FreeBookDownload, Product


class FreeBookDownloadTests(TestCase):
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
        creator = get_user_model().objects.create_user(
            email="editor@example.com",
            first_name="Book",
            last_name="Editor",
            password="test-password",
        )
        category = Category.objects.create(cat_name="Growth", cat_slug="growth")
        self.file_content = b"A free test book"
        self.product = Product.objects.create(
            category=category,
            created_by=creator,
            title="Growing in Faith",
            author="Awakening Saints",
            product_slug="growing-in-faith",
            product_price=Decimal("25.00"),
            qty_in_stock=0,
            book_file=SimpleUploadedFile("faith.pdf", self.file_content),
        )

    def test_books_page_routes_to_free_catalogue(self):
        response = self.client.get(reverse("sales:books"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "free to download")
        self.assertContains(response, reverse("sales:free_book_download", args=[self.product.product_slug]))

    def test_out_of_stock_digital_book_still_has_details_page(self):
        response = self.client.get(self.product.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Download this book free")

    def test_contact_details_and_consent_are_required_before_download(self):
        url = reverse("sales:free_book_download", args=[self.product.product_slug])
        response = self.client.post(
            url,
            {
                "full_name": "Test Reader",
                "email": "reader@example.com",
                "phone": "+256 700 000000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")
        self.assertFalse(FreeBookDownload.objects.exists())

    def test_valid_form_records_reader_and_streams_book_for_free(self):
        url = reverse("sales:free_book_download", args=[self.product.product_slug])
        response = self.client.post(
            url,
            {
                "full_name": "  Test   Reader ",
                "email": "READER@EXAMPLE.COM",
                "phone": "+256 700 000000",
                "privacy_consent": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), self.file_content)
        self.assertIn("attachment;", response.headers["Content-Disposition"])

        download = FreeBookDownload.objects.get()
        self.assertEqual(download.product, self.product)
        self.assertEqual(download.full_name, "Test Reader")
        self.assertEqual(download.email, "reader@example.com")
        self.assertEqual(download.phone, "+256 700 000000")
        self.assertTrue(download.privacy_consent)
        self.assertFalse(download.marketing_consent)

    def test_book_without_file_is_not_offered_as_a_download(self):
        self.product.book_file.delete(save=True)

        response = self.client.get(
            reverse("sales:free_book_download", args=[self.product.product_slug])
        )

        self.assertEqual(response.status_code, 404)

    def test_public_navigation_pages_render(self):
        for route_name in (
            "sales:homeone",
            "sales:about",
            "sales:contact",
            "sales:services",
            "sales:donate",
            "sales:media",
            "sales:orphans",
        ):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
