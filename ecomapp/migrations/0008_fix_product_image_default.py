from django.db import migrations, models


def clear_phantom_default_image(apps, schema_editor):
    """product_images/p2.jpg was the field's old default but was never a real
    file. Any row still pointing at it has no real cover, so clear it and let
    the app fall back to the site logo instead of a permanent broken image."""
    Product = apps.get_model("ecomapp", "Product")
    Product.objects.filter(product_image="product_images/p2.jpg").update(product_image="")


class Migration(migrations.Migration):
    dependencies = [
        ("ecomapp", "0007_expand_product_media_paths"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="product_image",
            field=models.ImageField(
                blank=True,
                max_length=500,
                upload_to="product_images/",
            ),
        ),
        migrations.RunPython(clear_phantom_default_image, migrations.RunPython.noop),
    ]
