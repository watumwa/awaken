import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.templatetags.static import static
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
        self.creator = get_user_model().objects.create_user(
            email="editor@example.com",
            first_name="Book",
            last_name="Editor",
            password="test-password",
        )
        category = Category.objects.create(cat_name="Growth", cat_slug="growth")
        self.file_content = b"A free test book"
        self.product = Product.objects.create(
            category=category,
            created_by=self.creator,
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
        self.assertContains(response, "available to download free")
        self.assertContains(response, reverse("sales:free_book_download", args=[self.product.product_slug]))

    def test_legacy_missing_cover_uses_the_library_placeholder(self):
        self.product.product_image.name = "product_images/p2.jpg"

        self.assertFalse(self.product.has_usable_cover)
        self.assertEqual(
            self.product.get_cover_url(),
            static("assets/images/book-cover-placeholder.svg"),
        )

        response = self.client.get(reverse("sales:books"))
        self.assertContains(response, "book-cover-placeholder.svg")

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

    def test_valid_form_records_reader_then_opens_the_book_from_success_page(self):
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

        success_url = reverse("sales:free_book_download_success", args=[self.product.product_slug])
        self.assertRedirects(response, success_url, fetch_redirect_response=False)

        success_response = self.client.get(success_url)
        self.assertContains(success_response, "Your book is ready")

        file_response = self.client.get(
            reverse("sales:free_book_file", args=[self.product.product_slug])
        )
        self.assertEqual(file_response.status_code, 200)
        self.assertEqual(b"".join(file_response.streaming_content), self.file_content)
        self.assertIn("attachment;", file_response.headers["Content-Disposition"])

        download = FreeBookDownload.objects.get()
        self.assertEqual(download.product, self.product)
        self.assertEqual(download.full_name, "Test Reader")
        self.assertEqual(download.email, "reader@example.com")
        self.assertEqual(download.phone, "+256 700 000000")
        self.assertTrue(download.privacy_consent)
        self.assertFalse(download.marketing_consent)

    @override_settings(IS_VERCEL=True)
    def test_vercel_redirects_the_book_file_to_the_cdn_after_recording_download(self):
        response = self.client.post(
            reverse("sales:free_book_download", args=[self.product.product_slug]),
            {
                "full_name": "Vercel Reader",
                "email": "vercel@example.com",
                "phone": "+256 700 000000",
                "privacy_consent": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse("sales:free_book_download_success", args=[self.product.product_slug]),
            fetch_redirect_response=False,
        )
        file_response = self.client.get(
            reverse("sales:free_book_file", args=[self.product.product_slug])
        )
        self.assertRedirects(file_response, self.product.book_file.url, fetch_redirect_response=False)
        self.assertTrue(
            FreeBookDownload.objects.filter(email="vercel@example.com", product=self.product).exists()
        )

    def test_download_success_and_file_routes_require_a_saved_reader_record(self):
        success_url = reverse("sales:free_book_download_success", args=[self.product.product_slug])
        form_url = reverse("sales:free_book_download", args=[self.product.product_slug])
        file_url = reverse("sales:free_book_file", args=[self.product.product_slug])

        self.assertRedirects(
            self.client.get(success_url), form_url, fetch_redirect_response=False
        )
        self.assertRedirects(self.client.get(file_url), form_url, fetch_redirect_response=False)

    def test_honeypot_rejects_automated_download_submissions(self):
        response = self.client.post(
            reverse("sales:free_book_download", args=[self.product.product_slug]),
            {
                "full_name": "Automated Reader",
                "email": "bot@example.com",
                "phone": "+256 700 000000",
                "privacy_consent": "on",
                "website": "https://spam.example",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please try again")
        self.assertFalse(FreeBookDownload.objects.exists())

    def test_books_page_shows_featured_library_titles(self):
        FreeBookDownload.objects.create(
            product=self.product,
            full_name="Featured Reader",
            email="featured@example.com",
            phone="+256 700 000000",
            privacy_consent=True,
        )

        response = self.client.get(reverse("sales:books"))

        self.assertContains(response, "Library highlights")
        self.assertContains(response, "featured-products-data")

    def test_book_detail_suggests_other_books_in_its_category(self):
        related_book = Product.objects.create(
            category=self.product.category,
            created_by=self.creator,
            title="Living with Purpose",
            author="Awakening Saints",
            product_slug="living-with-purpose",
            product_price=Decimal("25.00"),
            qty_in_stock=0,
            book_file=SimpleUploadedFile("purpose.pdf", b"purpose"),
        )

        response = self.client.get(self.product.get_absolute_url())

        self.assertContains(response, "More in Growth")
        self.assertContains(response, related_book.title)

    def test_admin_dashboard_shows_reader_and_most_downloaded_book(self):
        FreeBookDownload.objects.create(
            product=self.product,
            full_name="Dashboard Reader",
            email="dashboard@example.com",
            phone="+256 700 000000",
            privacy_consent=True,
        )
        self.creator.is_staff = True
        self.creator.is_superuser = True
        self.creator.is_active = True
        self.creator.save(update_fields=["is_staff", "is_superuser", "is_active"])
        self.client.force_login(self.creator)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Book download overview")
        self.assertContains(response, "Dashboard Reader")
        self.assertContains(response, self.product.title)
        self.assertContains(response, "Most downloaded")

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
