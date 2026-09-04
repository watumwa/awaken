import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ecomapp", "0004_paymentlog_alter_bookorder_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="FreeBookDownload",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("full_name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=30)),
                ("privacy_consent", models.BooleanField(default=False)),
                ("marketing_consent", models.BooleanField(default=False)),
                ("downloaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="free_downloads",
                        to="ecomapp.product",
                    ),
                ),
            ],
            options={
                "ordering": ("-downloaded_at",),
                "indexes": [
                    models.Index(fields=["email"], name="ecomapp_fre_email_d37acb_idx"),
                    models.Index(
                        fields=["product", "downloaded_at"],
                        name="ecomapp_fre_product_8526d8_idx",
                    ),
                ],
            },
        ),
    ]
