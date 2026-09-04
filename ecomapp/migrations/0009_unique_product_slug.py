from django.db import migrations, models
from django.db.models import Count


def dedupe_product_slugs(apps, schema_editor):
    """Duplicate product_slug values were possible before this constraint (the
    admin only suggests a slug from the title, it never enforced uniqueness),
    and get_object_or_404(Product, product_slug=...) raises MultipleObjectsReturned
    for any slug shared by more than one product. Keep the oldest product on the
    original slug and rename the rest before the unique index is created."""
    Product = apps.get_model("ecomapp", "Product")
    duplicates = (
        Product.objects.values("product_slug")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )
    for entry in duplicates:
        slug = entry["product_slug"]
        dupes = list(Product.objects.filter(product_slug=slug).order_by("id"))
        for product in dupes[1:]:
            suffix = 2
            new_slug = f"{slug}-{suffix}"
            while Product.objects.filter(product_slug=new_slug).exists():
                suffix += 1
                new_slug = f"{slug}-{suffix}"
            product.product_slug = new_slug
            product.save(update_fields=["product_slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("ecomapp", "0008_fix_product_image_default"),
    ]

    operations = [
        migrations.RunPython(dedupe_product_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="product",
            name="product_slug",
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
