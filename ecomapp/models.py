from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.templatetags.static import static
from django_ckeditor_5.fields import CKEditor5Field

from .utils import extract_text_from_file


# =========================
# PRODUCT MANAGER
# =========================
class ProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


# =========================
# CATEGORY
# =========================
class Category(models.Model):
    cat_name = models.CharField(max_length=255, db_index=True)
    cat_slug = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "categories"

    def get_absolute_url(self):
        return reverse("sales:shop_list", args=[self.cat_slug])

    def __str__(self):
        return self.cat_name


# =========================
# PRODUCT
# =========================
class Product(models.Model):
    category = models.ForeignKey(
        Category, related_name="product", on_delete=models.CASCADE
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_creator",
    )

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, default="admin")

    description = CKEditor5Field(blank=True, null=True)

    product_image = models.ImageField(
        upload_to="product_images/", blank=True, max_length=500
    )

    product_slug = models.CharField(max_length=255, unique=True)
    product_price = models.DecimalField(max_digits=30, decimal_places=2)

    qty_in_stock = models.DecimalField(max_digits=20, decimal_places=0, default=0)

    book_file = models.FileField(
        upload_to="books/", blank=True, null=True, max_length=500
    )

    in_stock = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    products = ProductManager()

    class Meta:
        verbose_name_plural = "products"
        ordering = ("-created",)

    def save(self, *args, **kwargs):
        self.in_stock = (self.qty_in_stock or 0) > 0
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("sales:product_detail", args=[self.product_slug])

    def get_cover_url(self):
        if self.product_image:
            return self.product_image.url
        return static("assets/images/logo.png")

    def __str__(self):
        return self.title


# =========================
# FREE BOOK DOWNLOADS
# =========================
class FreeBookDownload(models.Model):
    """Consent-based contact record created when a visitor downloads a book."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="free_downloads"
    )
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    privacy_consent = models.BooleanField(default=False)
    marketing_consent = models.BooleanField(default=False)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-downloaded_at",)
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["product", "downloaded_at"]),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.product.title}"


# =========================
# BOOK ORDER (LIVEPAY CORE)
# =========================
class BookOrder(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "collected"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending Payment"),
        (STATUS_PAID, "Paid & Ready"),
        (STATUS_FAILED, "Payment Failed"),
    ]

    PAYMENT_PENDING = "pending"
    PAYMENT_COMPLETED = "completed"
    PAYMENT_FAILED = "failed"

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_COMPLETED, "Completed"),
        (PAYMENT_FAILED, "Failed"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("livepay", "LivePay"),
    ]

    # Customer info
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="book_orders",
    )

    # Address
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, default="Kampala")
    country = models.CharField(max_length=100, default="Uganda")

    # Reference
    tx_ref = models.CharField(max_length=100, unique=True)

    # Money
    subtotal = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")

    # Payment
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default="livepay"
    )

    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING
    )

    payment_date = models.DateTimeField(blank=True, null=True)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created",)
        indexes = [
            models.Index(fields=["tx_ref"]),
            models.Index(fields=["email"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_status"]),
        ]

    def save(self, *args, **kwargs):

        if self.payment_status == self.PAYMENT_COMPLETED:
            if not self.payment_date:
                self.payment_date = timezone.now()
                self.paid_at = timezone.now()

            self.status = self.STATUS_PAID

        elif self.payment_status == self.PAYMENT_FAILED:
            if self.status != self.STATUS_PAID:
                self.status = self.STATUS_FAILED

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.full_name} - {self.total}"

    @property
    def is_paid(self):
        return self.payment_status == self.PAYMENT_COMPLETED

    @property
    def can_download(self):
        return self.status == self.STATUS_PAID


# =========================
# ORDER ITEMS
# =========================
class BookOrderItem(models.Model):
    order = models.ForeignKey(BookOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    downloaded = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def get_total(self):
        return (self.price or 0) * (self.quantity or 0)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"


# =========================
# PAYMENT LOG (OPTIONAL BUT USEFUL)
# =========================
class PaymentLog(models.Model):
    order = models.ForeignKey(
        BookOrder, on_delete=models.CASCADE, related_name="payment_logs"
    )

    status = models.CharField(max_length=20)
    message = models.TextField(blank=True, null=True)

    internal_reference = models.CharField(max_length=255, blank=True, null=True)
    customer_reference = models.CharField(max_length=255, blank=True, null=True)

    raw_payload = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"PaymentLog - {self.status} - {self.order.tx_ref}"


# =========================
# OTHER MODELS (UNCHANGED)
# =========================
class BookPreview(models.Model):
    book = models.OneToOneField(
        "Product", on_delete=models.CASCADE, related_name="preview"
    )
    chapter_title = models.CharField(max_length=255)
    content = CKEditor5Field()

    def __str__(self):
        return f"Preview of {self.book.title}"


class BookReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(
        "Product", on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} review on {self.book.title}"


class SermonContent(models.Model):
    MEDIA_TYPES = [
        ("audio", "Audio"),
        ("video", "Video"),
        ("text", "Text"),
    ]

    title = models.CharField(max_length=255)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)

    file = models.FileField(
        upload_to="media_files/", blank=True, null=True, max_length=500
    )
    text_body = CKEditor5Field(blank=True, null=True)

    thumbnail = models.ImageField(
        upload_to="media_thumbnails/", blank=True, null=True, max_length=500
    )

    preacher = models.CharField(max_length=255, blank=True)
    scripture = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.media_type == "text" and self.file and not self.text_body:
            try:
                self.text_body = extract_text_from_file(self.file.path)
            except Exception as e:
                print(f"Text extraction failed: {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.media_type.upper()}: {self.title}"

    def get_file_url(self):
        return self.file.url if self.file else ""

    def get_thumbnail_url(self):
        return self.thumbnail.url if self.thumbnail else static("assets/images/logo.png")

    def get_excerpt(self, length=180):
        text = strip_tags(self.text_body or "").strip()
        if len(text) <= length:
            return text
        return f"{text[:length].rsplit(' ', 1)[0]}…"


class SermonComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    media = models.ForeignKey(
        SermonContent, on_delete=models.CASCADE, related_name="comments"
    )
    comment = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} on {self.media.title}"


class EmailSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class SubscriberMessage(models.Model):
    title = models.CharField(max_length=255)
    body = CKEditor5Field()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
