from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.basket_summary, name="cart_summary"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("confirmation/", views.confirmation, name="confirm"),
    path("track/", views.tracking, name="track"),
    path("add-to-cart/", views.cart_add, name="cart_add"),
    path("delete/", views.cart_delete, name="cart_delete"),
    path("update/", views.cart_update, name="cart_update"),
    # path("submit-order/", views.submit_order, name="submit_order"),
    # # path('payment-waiting/', views.payment_waiting, name='payment_waiting'),
    # path("payment-success/", views.payment_success, name="payment_success"),
    # PesaPal URLs
    path("save-order/", views.save_order, name="save_order"),
    # path('initiate-pesapal-payment/', views.initiate_pesapal_payment, name='initiate_pesapal_payment'),
    # path('pesapal-callback/', views.pesapal_callback, name='pesapal_callback'),
    # # path('pesapal-ipn/', views.pesapal_ipn, name='pesapal_ipn'),
    # path('order-status/<int:order_id>/', views.order_status, name='order_status'),
    # Download URLs
    path("download/<str:signed_value>/", views.download_book, name="download_book"),
    path("downloads/<int:order_id>/", views.download_page, name="download_page"),
    path("livepay/initiate/", views.initiate_livepay_payment, name="initiate_livepay_payment",),
    path("livepay/webhook/", views.livepay_webhook, name="livepay_webhook"),
    path("livepay/callback/", views.livepay_callback, name="livepay_callback"),
    path("check-payment-status/<int:order_id>/", views.check_payment_status, name="check_payment_status",),
]
# path('download/<int:order_id>/<int:product_id>/', views.download_book, name='download_book'),
