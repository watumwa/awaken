from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from ecomapp.admin import ProductAdmin
from ecomapp.models import Category, Product


class ProductAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password="admin-password",
        )
        self.category = Category.objects.create(cat_name="Growth", cat_slug="growth")

    def test_new_product_is_assigned_to_the_logged_in_administrator(self):
        request = RequestFactory().post("/admin/ecomapp/product/add/")
        request.user = self.admin_user
        product = Product(
            category=self.category,
            title="Test Product",
            author="Test Author",
            product_slug="test-product",
            product_price=Decimal("10.00"),
            qty_in_stock=1,
        )

        ProductAdmin(Product, AdminSite()).save_model(
            request, product, form=None, change=False
        )

        self.assertEqual(product.created_by, self.admin_user)

    def test_admin_renders_the_missing_cover_status_without_an_html_error(self):
        product = Product(
            category=self.category,
            created_by=self.admin_user,
            title="Legacy Cover",
            author="Test Author",
            product_slug="legacy-cover",
            product_price=Decimal("10.00"),
            qty_in_stock=1,
        )
        product.product_image.name = "product_images/p2.jpg"
        product_admin = ProductAdmin(Product, AdminSite())

        self.assertIn("Upload a cover", product_admin.product_image_display(product))
        self.assertIn("Missing", product_admin.book_file_status(product))
