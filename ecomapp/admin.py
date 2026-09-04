import csv

from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from .models import (
    BookOrder,
    BookOrderItem,
    BookPreview,
    BookReview,
    Category,
    EmailSubscriber,
    FreeBookDownload,
    PaymentLog,
    Product,
    SermonComment,
    SermonContent,
    SubscriberMessage,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("cat_name", "cat_slug")
    prepopulated_fields = {"cat_slug": ("cat_name",)}
    search_fields = ("cat_name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "product_image_display",
        "book_file_status",
        "free_download_count",
        "is_active",
    )
    list_filter = ("is_active", "category")
    prepopulated_fields = {"product_slug": ("title",)}
    search_fields = ("title", "author", "category__cat_name")
    list_select_related = ("category",)
    fieldsets = (
        ("Book details", {"fields": ("title", "author", "category", "product_slug", "description", "is_active")}),
        ("Free digital download", {"fields": ("product_image", "book_file")}),
        ("Legacy commerce fields", {
            "fields": ("product_price", "qty_in_stock"),
            "description": "These fields are kept for backwards compatibility. Public book downloads are free and do not use the cart or payment flow.",
            "classes": ("collapse",),
        }),
    )

    def save_model(self, request, obj, form, change):
        """Record the administrator who creates each product."""
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_free_download_count=Count("free_downloads"))

    @admin.display(description="Downloads", ordering="_free_download_count")
    def free_download_count(self, obj):
        return obj._free_download_count

    @admin.display(description="PDF / file")
    def book_file_status(self, obj):
        if obj.book_file:
            return mark_safe('<span style="color:#137333;font-weight:700;">Ready</span>')
        return mark_safe('<span style="color:#b3261e;font-weight:700;">Missing</span>')

    @admin.display(description="Cover")
    def product_image_display(self, obj):
        if obj.product_image:
            try:
                return mark_safe(f'<img src="{obj.product_image.url}" height="58" style="border-radius:4px;" alt=""/>')
            except (ValueError, OSError):
                pass
        return "-"


@admin.action(description="Export selected downloader contacts to CSV")
def export_download_contacts(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="awakening-saints-free-book-downloads.csv"'
    writer = csv.writer(response)
    writer.writerow(["Full name", "Email", "Phone", "Book", "Marketing consent", "Downloaded at"])
    for row in queryset.select_related("product"):
        writer.writerow([
            row.full_name,
            row.email,
            row.phone,
            row.product.title,
            "Yes" if row.marketing_consent else "No",
            row.downloaded_at.isoformat(),
        ])
    return response


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
    list_filter = ("marketing_consent", "product", "downloaded_at")
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
    list_per_page = 50
    actions = (export_download_contacts,)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BookPreview)
class BookPreviewAdmin(admin.ModelAdmin):
    list_display = ("book", "chapter_title")
    search_fields = ("book__title", "chapter_title")
    autocomplete_fields = ("book",)


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "rating", "timestamp")
    list_filter = ("rating", "timestamp")
    search_fields = ("user__email", "book__title")


@admin.register(SermonComment)
class SermonCommentAdmin(admin.ModelAdmin):
    list_display = ("user", "media", "timestamp")
    search_fields = ("user__email", "media__title")


class SermonCommentInline(admin.TabularInline):
    model = SermonComment
    extra = 0


@admin.register(SermonContent)
class SermonContentAdmin(admin.ModelAdmin):
    inlines = (SermonCommentInline,)
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


class BookOrderItemInline(admin.TabularInline):
    model = BookOrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price", "get_total")


@admin.register(BookOrder)
class BookOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "tx_ref", "payment_status", "total", "created")
    list_filter = ("status", "payment_status")
    search_fields = ("full_name", "email", "tx_ref")
    inlines = (BookOrderItemInline,)


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "created_at")
    search_fields = ("order__tx_ref",)


@admin.register(EmailSubscriber)
class EmailSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "subscribed_on")
    search_fields = ("email",)


@admin.register(SubscriberMessage)
class SubscriberMessageAdmin(admin.ModelAdmin):
    list_display = ("title", "sent_at")
    readonly_fields = ("sent_at",)
