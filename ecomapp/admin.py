from django import forms
from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import *


# -----------------------------
# CATEGORY
# -----------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("cat_name", "cat_slug")
    prepopulated_fields = {"cat_slug": ("cat_name",)}
    search_fields = ("cat_name",)


# -----------------------------
# PRODUCT
# -----------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "product_image_display",
        "product_price",
        "qty_in_stock",
        "stock_status",
        "is_active",
    )
    list_filter = ["in_stock", "is_active"]
    prepopulated_fields = {"product_slug": ("title",)}
    list_editable = ["product_price", "qty_in_stock"]
    search_fields = ("title",)

    def stock_status(self, obj):
        if obj.in_stock:
            return mark_safe('<span style="color:green;">In Stock</span>')
        return mark_safe('<span style="color:red;">OUT OF STOCK</span>')

    def product_image_display(self, obj):
        if obj.product_image:
            return mark_safe(f'<img src="{obj.product_image.url}" height="50"/>')
        return "-"


@admin.register(FreeBookDownload)
class FreeBookDownloadAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "phone",
        "product",
        "marketing_consent",
        "downloaded_at",
    )
    list_filter = ("marketing_consent", "privacy_consent", "product", "downloaded_at")
    search_fields = ("full_name", "email", "phone", "product__title")
    readonly_fields = (
        "product",
        "full_name",
        "email",
        "phone",
        "privacy_consent",
        "marketing_consent",
        "downloaded_at",
    )
    date_hierarchy = "downloaded_at"


# -----------------------------
# BOOK PREVIEW
# -----------------------------
@admin.register(BookPreview)
class BookPreviewAdmin(admin.ModelAdmin):
    list_display = ("book", "chapter_title")
    search_fields = ("book__title", "chapter_title")
    autocomplete_fields = ("book",)


# -----------------------------
# BOOK REVIEW (ADDED FIX)
# -----------------------------
@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "rating", "timestamp")
    list_filter = ("rating", "timestamp")
    search_fields = ("user__email", "book__title")


# -----------------------------
# SERMON COMMENT (NEW ADMIN)
# -----------------------------
@admin.register(SermonComment)
class SermonCommentAdmin(admin.ModelAdmin):
    list_display = ("user", "media", "timestamp")
    search_fields = ("user__email", "media__title")


# -----------------------------
# SERMON CONTENT
# -----------------------------
class SermonCommentInline(admin.TabularInline):
    model = SermonComment
    extra = 0


@admin.register(SermonContent)
class SermonContentAdmin(admin.ModelAdmin):
    inlines = [SermonCommentInline]

    list_display = ("title", "media_type", "uploaded_at")
    list_filter = ("media_type",)
    search_fields = ("title",)

    readonly_fields = ("uploaded_at", "file_preview")

    def file_preview(self, obj):
        if obj.media_type == "audio" and obj.file:
            return mark_safe(f"<audio controls src='{obj.file.url}'></audio>")
        if obj.media_type == "video" and obj.file:
            return mark_safe(f"<video controls src='{obj.file.url}'></video>")
        return "-"


# -----------------------------
# ORDER SYSTEM (LIVEPAY READY)
# -----------------------------
class BookOrderItemInline(admin.TabularInline):
    model = BookOrderItem
    extra = 0
    readonly_fields = ["product", "quantity", "price", "get_total"]


@admin.register(BookOrder)
class BookOrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "full_name",
        "email",
        "tx_ref",
        "payment_status",
        "total",
        "created",
    ]

    list_filter = ["status", "payment_status"]
    search_fields = ["full_name", "email", "tx_ref"]

    inlines = [BookOrderItemInline]


# -----------------------------
# PAYMENT LOG (LIVEPAY READY)
# -----------------------------
@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ["order", "status", "created_at"]
    search_fields = ["order__tx_ref"]


# -----------------------------
# EMAIL
# -----------------------------
@admin.register(EmailSubscriber)
class EmailSubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "subscribed_on"]
    search_fields = ["email"]


@admin.register(SubscriberMessage)
class SubscriberMessageAdmin(admin.ModelAdmin):
    list_display = ["title", "sent_at"]
    readonly_fields = ["sent_at"]
