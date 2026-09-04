import hashlib
import hmac
import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ecomapp.models import *

from .basket import cartbasket

signer = TimestampSigner()


# Show cart page
@login_required
def basket_summary(request):
    cart = cartbasket(request)
    return render(request, "cart/basketapp/cart.html", {"cart": cart})


# Add product to cart
def cart_add(request):
    basket = cartbasket(request)
    if request.POST.get("action") == "post":
        try:
            product_id = int(request.POST.get("product_id"))
            product_qty = int(request.POST.get("productqty"))
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid product ID or quantity"}, status=400)

        product = get_object_or_404(Product, id=product_id)
        basket.add(product=product, qty=product_qty)

        total_qty = len(basket)
        return JsonResponse(
            {
                "message": "Product added",
                "product_id": product_id,
                "qty": product_qty,
                "cart_count": total_qty,
            }
        )
    return JsonResponse({"error": "Invalid action"}, status=400)


# Update product quantity in cart
@require_POST
def cart_update(request):
    basket = cartbasket(request)

    if request.POST.get("action") == "post":
        try:
            product_id = int(request.POST.get("productid"))
            product_qty = int(request.POST.get("productqty"))
            if product_qty < 1:
                product_qty = 1
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid input"}, status=400)

        basket.update(product=product_id, qty=product_qty)

        return JsonResponse(
            {"cart_count": len(basket), "subtotal": basket.get_total_price()}
        )

    return JsonResponse({"error": "Invalid action"}, status=400)


# Remove product from cart
def cart_delete(request):
    cart = cartbasket(request)
    if request.POST.get("action") == "post":
        try:
            product_id = int(request.POST.get("productid"))
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid product ID"}, status=400)

        cart.delete(product=product_id)

        return JsonResponse(
            {"subtotal": cart.get_total_price(), "cart_count": len(cart)}
        )
    return JsonResponse({"error": "Invalid action"}, status=400)


# Checkout view
@login_required
def checkout_view(request):
    basket = cartbasket(request)
    cart_items = []

    for item in basket:
        product = item.get("product")
        if not product:
            continue
        cart_items.append(
            {
                "id": product.id,
                "name": product.title,
                "price": float(product.product_price),
                "qty": item["qty"],
            }
        )

    cart_json = json.dumps(cart_items)
    return render(request, "cart/basketapp/checkout.html", {"cart_json": cart_json})


# -----------------------------
# Lively Integration Functions for LIVE/PRODUCTION
# -----------------------------

# =========================
# LIVEPAY PAYMENT
# =========================


@csrf_exempt
@require_POST
def initiate_livepay_payment(request):
    import requests

    try:
        data = json.loads(request.body)

        order = BookOrder.objects.get(
            id=data.get("order_id"),
            tx_ref=data.get("reference")
        )

        # -------------------------
        # CLEAN PHONE
        # -------------------------
        phone = "".join(filter(str.isdigit, order.phone))

        if phone.startswith("0"):
            phone = "256" + phone[1:]

        if not phone.startswith("256") or len(phone) != 12:
            return JsonResponse({"status": "error", "message": "Invalid phone"}, status=400)

        # -------------------------
        # FIX AMOUNT
        # -------------------------
        amount = int(order.total)

        if amount < 500:
            amount = 500

        payload = {
            "accountNumber": settings.LIVEPAY_ACCOUNT_NUMBER,
            "phoneNumber": phone,
            "amount": amount,
            "currency": "UGX",
            "reference": order.tx_ref,
            "description": f"Order {order.id}",
        }

        headers = {
            "Authorization": f"Bearer {settings.LIVEPAY_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            "https://livepay.me/api/collect-money",
            json=payload,
            headers=headers,
            timeout=30,
        )

        try:
            resp = response.json()
        except:
            return JsonResponse({"status": "error", "message": "Bad LivePay response"}, status=500)

        if response.status_code == 200 and resp.get("success"):
            order.payment_status = "pending"
            order.save()

            PaymentLog.objects.create(
                order=order,
                status="initiated",
                message="Payment started",
                raw_payload=resp,
            )

            return JsonResponse({"status": "success"})

        PaymentLog.objects.create(
            order=order,
            status="failed",
            message=resp.get("error", "failed"),
            raw_payload=resp,
        )

        return JsonResponse({
            "status": "error",
            "message": resp.get("error", "Payment failed")
        }, status=400)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
# =========================
# LIVEPAY WEBHOOK
# =========================

@csrf_exempt
@require_POST
def livepay_webhook(request):
    try:
        payload = json.loads(request.body)

        ref = payload.get("customer_reference")
        status = (payload.get("status") or "").lower()

        order = BookOrder.objects.get(tx_ref=ref)

        PaymentLog.objects.create(
            order=order,
            status="webhook_received",
            message=status,
            customer_reference=ref,
            raw_payload=payload,
        )

        if status in ["success", "completed", "paid"]:
            order.payment_status = "completed"
            order.status = "collected"
            order.paid_at = timezone.now()
            order.save()

        else:
            order.payment_status = "failed"
            order.status = "failed"
            order.save()

        return HttpResponse(status=200)

    except Exception as e:
        return HttpResponse(str(e), status=400)


# =========================
# PAYMENT CALLBACK
# =========================


@login_required
def livepay_callback(request):
    import requests

    reference = request.GET.get("reference")

    if not reference:
        messages.error(request, "Missing reference")

        return redirect("cart:checkout")

    try:
        order = BookOrder.objects.get(tx_ref=reference)

        # VERIFY PAYMENT WITH LIVEPAY API
        response = requests.get(
            f"{settings.LIVEPAY_BASE_URL}/collect-money/{reference}",
            headers=get_livepay_headers(),
        )

        data = response.json()

        if data.get("status") == "Success":
            order.status = "collected"
            order.payment_status = "completed"
            order.payment_date = timezone.now()

            order.save()

            return redirect("cart:download_page", order_id=order.id)

        messages.error(request, "Payment not completed")

        return redirect("cart:order_status", order_id=order.id)

    except Exception as e:
        print(e)

        messages.error(request, "Payment verification failed")

        return redirect("cart:checkout")



@login_required
def check_payment_status(request, order_id):
    import requests

    try:
        order = BookOrder.objects.get(id=order_id)

        # already paid
        if order.payment_status == "completed":
            return JsonResponse({
                "paid": True,
                "redirect_url": reverse("cart:download_page", args=[order.id])
            })

        response = requests.get(
            "https://livepay.me/api/transaction-status",
            params={
                "accountNumber": settings.LIVEPAY_ACCOUNT_NUMBER,
                "currency": "UGX",
                "reference": order.tx_ref,
            },
            headers={
                "Authorization": f"Bearer {settings.LIVEPAY_SECRET_KEY}",
                "Content-Type": "application/json",
            },
            timeout=20,
        )

        data = response.json()

        # print(data)

        status = str(data.get("status", "")).lower()

        if status in ["success", "completed", "paid"]:
            order.payment_status = "completed"
            order.status = "collected"
            order.payment_date = timezone.now()
            order.save()

            return JsonResponse({
                "paid": True,
                "redirect_url": reverse("cart:download_page", args=[order.id])
            })

        if status in ["failed", "cancelled"]:
            order.payment_status = "failed"
            order.status = "failed"
            order.save()

            return JsonResponse({"failed": True})

        return JsonResponse({"pending": True})

    except Exception as e:
        print("STATUS ERROR:", str(e))

        return JsonResponse({
            "error": str(e)
        }, status=500)


        

@csrf_exempt
@require_POST
def save_order(request):
    try:
        data = json.loads(request.body)

        full_name = data.get("full_name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()

        if not full_name or not email or not phone:
            return JsonResponse({"status": "error", "message": "Missing fields"}, status=400)

        cart_items = data.get("cart", [])
        if not cart_items:
            return JsonResponse({"status": "error", "message": "Cart empty"}, status=400)

        # -------------------------
        # CALCULATE TOTAL SERVER SIDE
        # -------------------------
        subtotal = Decimal("0.00")

        for item in cart_items:
            try:
                product = Product.objects.get(pk=item["id"])
                qty = int(item["qty"])
                subtotal += product.product_price * qty
            except:
                continue

        # -------------------------
        # MINIMUM $1 = 500 UGX
        # -------------------------
        if subtotal < 500:
            subtotal = Decimal("500.00")

        reference = data.get("reference") or f"LIVEPAY-{uuid.uuid4().hex[:10].upper()}"

        order = BookOrder.objects.create(
            full_name=full_name,
            email=email,
            phone=phone,
            address=data.get("address", ""),
            city=data.get("city", "Kampala"),
            country="Uganda",
            tx_ref=reference,
            subtotal=subtotal,
            total=subtotal,
            currency="UGX",
            payment_status="pending",
            status="pending",
            user=request.user if request.user.is_authenticated else None,
        )

        for item in cart_items:
            try:
                product = Product.objects.get(pk=item["id"])
                BookOrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=int(item["qty"]),
                    price=product.product_price,
                )
            except:
                continue

        return JsonResponse({
            "status": "success",
            "order_id": order.id,
            "reference": order.tx_ref,
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    
# Check order status
@login_required
def order_status(request, order_id):
    """Display order payment status"""
    order = get_object_or_404(BookOrder, id=order_id, email=request.user.email)

    # If payment is completed, redirect to downloads
    if order.status == "collected":
        messages.success(request, "Payment successful! Your downloads are ready.")
        return redirect("cart:download_page", order_id=order.id)

    return render(request, "cart/basketapp/order_status.html", {"order": order})


# -----------------------------
# Legacy submit_order (for compatibility)
# -----------------------------
# @csrf_exempt
# @require_POST
# def submit_order(request):
#     """Legacy endpoint - redirects to new PesaPal flow"""
#     try:
#         data = json.loads(request.body)

#         # Generate new reference for PesaPal
#         reference = f"PESAPAL-LIVE-{uuid.uuid4().hex[:12].upper()}"

#         # Return success to trigger frontend PesaPal flow
#         return JsonResponse(
#             {
#                 "status": "ok",
#                 "reference": reference,
#                 "message": "Proceed with PesaPal payment",
#             }
#         )

#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)}, status=500)


# -----------------------------
# Download functions
# -----------------------------
def generate_download_link(order_item):
    value = f"{order_item.order.id}:{order_item.product.id}"
    signed_value = signer.sign(value)
    return reverse("cart:download_book", args=[signed_value])


@login_required
def download_book(request, signed_value):
    try:
        value = signer.unsign(signed_value, max_age=1800)
    except SignatureExpired:
        return HttpResponseForbidden("Download link has expired.")
    except BadSignature:
        return HttpResponseForbidden("Invalid download link.")

    order_id, product_id = value.split(":")
    order = get_object_or_404(
        BookOrder, id=order_id, email=request.user.email, status="collected"
    )
    order_item = get_object_or_404(BookOrderItem, order=order, product_id=product_id)

    if order_item.downloaded:
        return HttpResponseForbidden("This download link has already been used.")

    book_file = order_item.product.book_file
    if not book_file:
        raise Http404("Book file not found")

    order_item.downloaded = True
    order_item.save(update_fields=["downloaded"])

    # Storage-agnostic read: works for both legacy local media and Vercel Blob.
    mime_type, _ = mimetypes.guess_type(book_file.name)
    try:
        with book_file.open("rb") as f:
            response = HttpResponse(
                f.read(), content_type=mime_type or "application/octet-stream"
            )
    except (FileNotFoundError, OSError):
        raise Http404("Book file not found")

    response["Content-Disposition"] = (
        f'attachment; filename="{order_item.product.title}.pdf"'
    )
    return response


@login_required
def download_page(request, order_id):
    order = get_object_or_404(
        BookOrder.objects.prefetch_related("items"),
        id=order_id,
        email=request.user.email,
        status="collected",
    )

    links = []
    for item in order.items.all():
        if item.product.book_file and not item.downloaded:
            expires_at = now() + timedelta(minutes=30)
            links.append(
                {
                    "title": item.product.title,
                    "cover_image": item.product.product_image.url
                    if item.product.product_image
                    else None,
                    "order_number": order.id,
                    "purchase_date": order.created.strftime("%B %d, %Y %I:%M %p"),
                    "author": item.product.author,
                    "file_size": f"{item.product.book_file.size / (1024 * 1024):.2f} MB"
                    if item.product.book_file
                    else "N/A",
                    "formats": ["PDF"],
                    "link": generate_download_link(item),
                    "expires_at": expires_at.isoformat(),
                }
            )

    return render(request, "download_page.html", {"order": order, "links": links})


def confirmation(request):
    return render(request, "cart/basketapp/confirmation.html")


def tracking(request):
    return render(request, "cart/basketapp/tracking.html")
