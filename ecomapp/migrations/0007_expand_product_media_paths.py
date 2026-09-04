from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ecomapp", "0006_align_payment_models"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sermoncontent",
            name="file",
            field=models.FileField(
                blank=True,
                max_length=500,
                null=True,
                upload_to="media_files/",
            ),
        ),
        migrations.AlterField(
            model_name="sermoncontent",
            name="thumbnail",
            field=models.ImageField(
                blank=True,
                max_length=500,
                null=True,
                upload_to="media_thumbnails/",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="product_image",
            field=models.ImageField(
                default="product_images/p2.jpg",
                max_length=500,
                upload_to="product_images/",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="book_file",
            field=models.FileField(
                blank=True,
                max_length=500,
                null=True,
                upload_to="books/",
            ),
        ),
    ]
