"""Analytics helpers for the Awakening Saints administration dashboard."""

import json
from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone

from .models import FreeBookDownload, Product


def downloads_today_badge(request):
    """Show today's new download count beside the sidebar navigation item."""
    count = FreeBookDownload.objects.filter(downloaded_at__date=timezone.localdate()).count()
    return str(count) if count else None


def dashboard_callback(request, context):
    """Add concise, live download analytics to Unfold's admin index page."""
    today = timezone.localdate()
    periods = {
        "7": {"label": "7 days", "days": 7},
        "14": {"label": "14 days", "days": 14},
        "30": {"label": "30 days", "days": 30},
        "90": {"label": "90 days", "days": 90},
    }
    selected_period = request.GET.get("period", "14")
    if selected_period not in periods:
        selected_period = "14"
    period = periods[selected_period]
    chart_start = today - timedelta(days=period["days"] - 1)

    downloads = FreeBookDownload.objects.all()
    period_downloads = downloads.filter(downloaded_at__date__gte=chart_start)
    daily_rows = (
        period_downloads
        .annotate(day=TruncDate("downloaded_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )
    daily_counts = {row["day"]: row["total"] for row in daily_rows}
    chart_dates = [
        chart_start + timedelta(days=offset) for offset in range(period["days"])
    ]

    top_books = list(
        Product.objects.annotate(
            download_count=Count(
                "free_downloads",
                filter=Q(free_downloads__downloaded_at__date__gte=chart_start),
            )
        )
        .filter(download_count__gt=0)
        .order_by("-download_count", "title")[:5]
    )
    recent_downloads = list(
        period_downloads.select_related("product").order_by("-downloaded_at")[:8]
    )

    chart_data = {
        "labels": [day.strftime("%b %-d") for day in chart_dates],
        "datasets": [
            {
                "label": f"Downloads — last {period['days']} days",
                "data": [daily_counts.get(day, 0) for day in chart_dates],
                "borderColor": "#0284c7",
                "backgroundColor": "rgba(14, 165, 233, 0.14)",
                "fill": True,
                "tension": 0.35,
                "pointBackgroundColor": "#0284c7",
                "pointRadius": 3,
            }
        ],
    }
    chart_options = {
        "plugins": {"legend": {"display": False}},
        "scales": {
            "x": {"grid": {"display": False}},
            "y": {
                "beginAtZero": True,
                "ticks": {"precision": 0, "stepSize": 1},
                "grid": {"color": "rgba(148, 163, 184, 0.22)"},
            },
        },
    }

    context.update(
        {
            "download_metrics": {
                "total": period_downloads.count(),
                "readers": period_downloads.values("email").distinct().count(),
                "opted_in": period_downloads.filter(marketing_consent=True).count(),
                "top_book": top_books[0] if top_books else None,
            },
            "analytics_periods": [
                {"value": value, "label": option["label"]}
                for value, option in periods.items()
            ],
            "selected_period": selected_period,
            "period_label": f"Last {period['days']} days",
            "top_books": top_books,
            "recent_downloads": recent_downloads,
            "download_chart": json.dumps(chart_data),
            "download_chart_options": json.dumps(chart_options),
            "download_list_url": reverse("admin:ecomapp_freebookdownload_changelist"),
            "book_list_url": reverse("admin:ecomapp_product_changelist"),
            "add_book_url": reverse("admin:ecomapp_product_add"),
        }
    )
    return context
