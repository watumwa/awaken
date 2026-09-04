import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required

# import requests
# from itertools import islice
from django.core.mail import send_mass_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import get_valid_filename
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import (
    BookPreview,
    BookReview,
    Category,
    EmailSubscriber,
    Product,
    SermonComment,
    SermonContent,
    SubscriberMessage,
)
from .forms import FreeBookDownloadForm
from .utils import get_media_duration  # if using separate utils file


def indexone(request):
    return render(request, "site/index.html")


def about(request):
    return render(request, "site/about.html")


def contactone(request):
    return render(request, "site/contact.html")


def services(request):
    return render(request, "site/services.html")


def donate(request):
    return render(request, "site/donate.html")


def orphans(request):
    return render(request, "site/organisation.html")


def media(request):
    media_items = SermonContent.objects.all()

    def serialize(media):
        duration = "00:00"
        if media.media_type in ["audio", "video"] and media.file:
            try:
                file_path = media.file.path
                duration = get_media_duration(file_path, media.media_type)
            except Exception:
                duration = "00:00"

        text_body = media.text_body or ""
        pages = (
            text_body.split("\n\n")
            if "\n\n" in text_body
            else [text_body]
            if text_body
            else []
        )

        return {
            "id": media.id,
            "type": media.media_type,
            "title": media.title,
            "artist": media.preacher or "Uploaded by Admin",
            "duration": duration,
            "date": media.uploaded_at.strftime("%b %d, %Y"),
            "description": media.description or "No description yet.",
            "scripture": media.scripture or "",
            "src": media.get_file_url(),
            "thumbnail": media.get_thumbnail_url(),
            "excerpt": media.get_excerpt(),
            "text_body": text_body,
            "expanded": False,
            "currentPage": 0,
            "pages": pages,
            "comments": [
                {
                    "username": comment.user.first_name or comment.user.last_name,
                    "text": comment.comment,
                    "timestamp": comment.timestamp.strftime("%b %d, %Y"),
                }
                for comment in media.comments.all().order_by("-timestamp")
            ],
        }

    audios = [serialize(m) for m in media_items.filter(media_type="audio")]
    videos = [serialize(m) for m in media_items.filter(media_type="video")]
    texts = [serialize(m) for m in media_items.filter(media_type="text")]

    context = {
        "audio_json": json.dumps(audios, cls=DjangoJSONEncoder),
        "video_json": json.dumps(videos, cls=DjangoJSONEncoder),
        "text_json": json.dumps(texts, cls=DjangoJSONEncoder),
    }

    return render(request, "site/media.html", context)


@csrf_exempt  # Optional if you're passing CSRF tokens via JS
@login_required
def add_comment(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid method"}, status=405
        )

    try:
        data = json.loads(request.body)
        media_id = data.get("media_id")
        comment_text = data.get("comment")

        if not media_id or not comment_text.strip():
            return JsonResponse(
                {"status": "error", "message": "Missing comment or media ID"},
                status=400,
            )

        media = SermonContent.objects.get(id=media_id)
        comment = SermonComment.objects.create(
            user=request.user,
            media=media,
            comment=comment_text.strip(),
            timestamp=timezone.now(),
        )

        return JsonResponse(
            {
                "status": "ok",
                "comment": {
                    "username": request.user.first_name or request.user.last_name,
                    "text": comment.comment,
                    "timestamp": "Just now",
                },
            }
        )

    except SermonContent.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Media not found"}, status=404
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


def index(request, cat_slug=None):
    """Render the free digital library.

    Prices and cart actions are intentionally not exposed here: every public book
    download is free, while the downloader contact form is handled by
    ``free_book_download``.
    """
    products = Product.products.select_related("category")
    if cat_slug:
        category = get_object_or_404(Category, cat_slug=cat_slug)
        products = products.filter(category=category)

    def image_url(product):
        try:
            return product.product_image.url if product.product_image else static("assets/images/logo.png")
        except (ValueError, OSError):
            return static("assets/images/logo.png")

    product_data = [
        {
            "id": product.id,
            "title": product.title,
            "author": product.author,
            "image": image_url(product),
            "category_name": product.category.cat_name,
            "category_slug": product.category.cat_slug,
            "slug": product.product_slug,
            "details_url": reverse("sales:product_detail", args=[product.product_slug]),
            "download_url": reverse("sales:free_book_download", args=[product.product_slug]),
            "has_file": bool(product.book_file),
        }
        for product in products
    ]

    categories = Category.objects.order_by("cat_name")
    category_data = [{"name": cat.cat_name, "slug": cat.cat_slug} for cat in categories]

    return render(
        request,
        "main/ecomapp/index.html",
        {
            "products_data": product_data,
            "categories_data": category_data,
        },
    )


def single_product(request, product_slug):
    product = get_object_or_404(Product.products, product_slug=product_slug)
    reviews = product.reviews.select_related("user").order_by("-timestamp")
    context = {
        "product": product,
        "reviews": reviews,
    }
    return render(request, "main/ecomapp/single-product.html", context)


@csrf_exempt
@login_required
def add_review_ajax(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            rating = int(data.get("rating", 0))
            comment = data.get("comment", "").strip()
            book_id = data.get("book_id")

            if not (1 <= rating <= 5):
                return JsonResponse({"success": False, "error": "Invalid rating."})

            book = Product.objects.get(id=book_id)

            review = BookReview.objects.create(
                user=request.user, book=book, rating=rating, comment=comment
            )

            return JsonResponse(
                {
                    "success": True,
                    "username": request.user.get_full_name() or request.user.username,
                    "rating": rating,
                    "comment": comment,
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})


def book_preview(request, product_slug):
    product = get_object_or_404(Product.products, product_slug=product_slug)
    preview = get_object_or_404(BookPreview, book=product)

    context = {
        "product": product,
        "preview": preview,
    }
    return render(request, "main/ecomapp/preview.html", context)


def free_book_download(request, product_slug):
    """Collect clearly disclosed contact details, then serve the book at no cost."""
    product = get_object_or_404(Product.products, product_slug=product_slug)
    if not product.book_file:
        raise Http404("This book is not available for download yet.")

    initial = {}
    if request.user.is_authenticated:
        initial = {
            "full_name": request.user.get_full_name(),
            "email": request.user.email,
            "phone": request.user.phone_number,
        }

    if request.method == "POST":
        form = FreeBookDownloadForm(request.POST)
        if form.is_valid():
            try:
                file_handle = product.book_file.open("rb")
            except (FileNotFoundError, OSError):
                raise Http404("The book file could not be found.")

            download = form.save(commit=False)
            download.product = product
            try:
                download.save()
            except Exception:
                file_handle.close()
                raise

            extension = Path(product.book_file.name).suffix
            filename = f"{get_valid_filename(product.title) or 'book'}{extension}"
            return FileResponse(file_handle, as_attachment=True, filename=filename)
    else:
        form = FreeBookDownloadForm(initial=initial)

    return render(
        request,
        "main/ecomapp/free-book-download.html",
        {"product": product, "form": form},
    )


# subscriptions/views.py
def send_message_to_subscribers(request, message_id):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=401)

    message = get_object_or_404(SubscriberMessage, id=message_id)
    subscribers = EmailSubscriber.objects.all()

    subject = message.title
    body = message.body
    from_email = settings.DEFAULT_FROM_EMAIL

    messages = [(subject, body, from_email, [sub.email]) for sub in subscribers]

    send_mass_mail(messages, fail_silently=False)
    return render(request, "admin/success_mail.html")
    # return HttpResponse("Emails sent successfully.")


@csrf_exempt
def subscribe_email(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if email:
            EmailSubscriber.objects.get_or_create(email=email)
        return HttpResponseRedirect("/?subscribed_successfully=1")
    return HttpResponseRedirect("/?subscription_not_successfully=0")


def contact(request):
    return render(request, "main/ecomapp/contact.html")


def blog(request):
    return render(request, "main/ecomapp/blog.html")


def single_blog(request):
    return render(request, "main/ecomapp/single-blog.html")
