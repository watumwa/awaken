from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from ecomapp.models import Category, Product


BOOKS = [
    {
        "title": "Adultery: Satan's Nuclear Weapon Against the Mighty",
        "pdf": "Adultery_3.pdf",
        "cover": "awake8.jpg",
        "aliases": ["Adultery"],
    },
    {
        "title": "Freedom Ignored",
        "pdf": "FREEDOM_IGNORED-11111.pdf",
        "cover": "FREEDOM_IGN.png",
    },
    {
        "title": "Generational Mandate",
        "pdf": "Generational_mandate_Final-1.pdf",
        "cover": "GENERATIONAL_MANDATE_2.png",
    },
    {
        "title": "A Sacred Covenant: The Divine Design of a Christian Marriage",
        "pdf": "MARRIAGE.pdf",
        "cover": "awake6.png",
        "aliases": ["Marriage", "Covenant"],
    },
    {
        "title": "Music: A Gate to Glory or Darkness",
        "pdf": "MUSIC_3.pdf",
        "cover": "awake1.png",
    },
    {
        "title": "Spiritual Fathers",
        "pdf": "SPIRITUAL_FATHERSs.pdf",
        "cover": "SPIRITUAL_FATHER.png",
    },
    {
        "title": "Spiritual Maturity",
        "pdf": "SPIRITUAL_MATURITY.pdf",
        "cover": "awake7.png",
        "aliases": ["Spiritual Maturity"],
    },
    {
        "title": "The Crisis of Self",
        "pdf": "THE_CRISIS_OF_SELF.pdf",
        "cover": "FORG.png",
    },
    {
        "title": "The Watchman's Call: Understanding the 8 Prayer Watches",
        "pdf": "THE_WATCHMANS_CALL_2.pdf",
        "cover": "awake3.png",
    },
    {
        "title": "When God Interrupts Your Labour",
        "pdf": "WHEN_GOD_INTERRUPTS_YOUR_LABOUR_3.pdf",
        "cover": "when_god.png",
    },
    {
        "title": "A Call for Deliverance: Masturbation is a Demon",
        "pdf": "masturbation_3.pdf",
        "cover": "awake9.jpg",
        "aliases": ["Masturbation is a Demon"],
    },
]


class Command(BaseCommand):
    help = "Create/update free book records for the PDFs and covers already in media/books and media/product_images."

    def add_arguments(self, parser):
        parser.add_argument(
            "--created-by-email",
            dest="created_by_email",
            help="Email address of the user who should own newly created product records.",
        )
        parser.add_argument(
            "--category",
            default="Free Books",
            help="Category name to use (default: Free Books).",
        )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        books_dir = media_root / "books"
        covers_dir = media_root / "product_images"

        if not books_dir.exists():
            raise CommandError(f"Books directory not found: {books_dir}")

        User = get_user_model()
        owner = None
        if options.get("created_by_email"):
            owner = User.objects.filter(email__iexact=options["created_by_email"]).first()
            if owner is None:
                raise CommandError("No user exists with the supplied --created-by-email address.")
        else:
            owner = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first() or User.objects.first()

        if owner is None:
            raise CommandError(
                "No user exists yet. Create an admin user first, or run the command after your production users are available."
            )

        category_name = options["category"].strip() or "Free Books"
        base_slug = slugify(category_name) or "free-books"
        category = Category.objects.filter(cat_name__iexact=category_name).first()
        if category is None:
            slug = base_slug
            suffix = 2
            while Category.objects.filter(cat_slug=slug).exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            category = Category.objects.create(cat_name=category_name, cat_slug=slug)
            self.stdout.write(self.style.SUCCESS(f"Created category: {category.cat_name}"))

        created = 0
        updated = 0
        skipped = 0

        for item in BOOKS:
            pdf_path = books_dir / item["pdf"]
            cover_path = covers_dir / item["cover"]
            if not pdf_path.is_file():
                self.stdout.write(self.style.WARNING(f"Skipped {item['title']}: missing {pdf_path.name}"))
                skipped += 1
                continue

            # Prefer updating a visible existing book instead of creating a duplicate.
            product = Product.objects.filter(product_image__endswith=item["cover"]).first()
            if product is None:
                product = Product.objects.filter(title__iexact=item["title"]).first()
            if product is None:
                for alias in item.get("aliases", []):
                    product = Product.objects.filter(title__iexact=alias).first()
                    if product is not None:
                        break

            was_created = product is None
            if product is None:
                base_slug = slugify(item["title"])[:240] or "book"
                slug = base_slug
                suffix = 2
                while Product.objects.filter(product_slug=slug).exists():
                    slug = f"{base_slug}-{suffix}"
                    suffix += 1
                product = Product(
                    category=category,
                    created_by=owner,
                    title=item["title"],
                    author="Pastor Denis Kalungi",
                    product_slug=slug,
                )
            elif not product.category_id:
                product.category = category

            if not product.author:
                product.author = "Pastor Denis Kalungi"
            product.product_price = 0
            product.qty_in_stock = max(product.qty_in_stock or 0, 1)
            product.is_active = True
            product.book_file.name = f"books/{item['pdf']}"
            if cover_path.is_file() and not product.product_image:
                product.product_image.name = f"product_images/{item['cover']}"
            if not product.description:
                product.description = "Available as a free digital book from Awakening Saints."
            product.save()

            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {product.title}"))
            else:
                updated += 1
                self.stdout.write(f"Updated: {product.title}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created {created}, updated {updated}, skipped {skipped}. Public downloads are free."
            )
        )
