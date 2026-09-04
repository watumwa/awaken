from django.db import migrations, models
from django.utils import timezone


def fill_required_order_fields(apps, schema_editor):
    BookOrder = apps.get_model("ecomapp", "BookOrder")
    BookOrderItem = apps.get_model("ecomapp", "BookOrderItem")
    current_time = timezone.now()
    BookOrder.objects.filter(city__isnull=True).update(city="Kampala")
    BookOrder.objects.filter(country__isnull=True).update(country="Uganda")
    BookOrder.objects.filter(created__isnull=True).update(created=current_time)
    BookOrder.objects.filter(updated__isnull=True).update(updated=current_time)
    BookOrderItem.objects.filter(created__isnull=True).update(created=current_time)


class Migration(migrations.Migration):

    dependencies = [
        ("ecomapp", "0005_freebookdownload"),
    ]

    operations = [
        migrations.RenameField(
            model_name="paymentlog",
            old_name="status_code",
            new_name="status",
        ),
        migrations.RenameField(
            model_name="paymentlog",
            old_name="status_description",
            new_name="message",
        ),
        migrations.RenameField(
            model_name="paymentlog",
            old_name="pesapal_tracking_id",
            new_name="internal_reference",
        ),
        migrations.RenameField(
            model_name="paymentlog",
            old_name="ipn_data",
            new_name="raw_payload",
        ),
        migrations.AddField(
            model_name="paymentlog",
            name="customer_reference",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="paymentlog",
            name="status",
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name="paymentlog",
            name="message",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RemoveField(
            model_name="bookorder",
            name="pesapal_order_id",
        ),
        migrations.RemoveField(
            model_name="bookorder",
            name="pesapal_redirect_url",
        ),
        migrations.RemoveField(
            model_name="bookorder",
            name="pesapal_tracking_id",
        ),
        migrations.RunPython(fill_required_order_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="bookorder",
            name="city",
            field=models.CharField(default="Kampala", max_length=100),
        ),
        migrations.AlterField(
            model_name="bookorder",
            name="country",
            field=models.CharField(default="Uganda", max_length=100),
        ),
        migrations.AlterField(
            model_name="bookorder",
            name="created",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="bookorder",
            name="updated",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="bookorder",
            name="payment_method",
            field=models.CharField(
                choices=[("livepay", "LivePay")], default="livepay", max_length=20
            ),
        ),
        migrations.AlterField(
            model_name="bookorderitem",
            name="created",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="product",
            name="qty_in_stock",
            field=models.DecimalField(decimal_places=0, default=0, max_digits=20),
        ),
    ]
