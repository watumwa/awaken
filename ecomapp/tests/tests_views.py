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
