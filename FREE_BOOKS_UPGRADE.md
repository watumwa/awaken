# Awakening Saints — Free Books Upgrade

This upgrade changes the public books section from a paid/cart presentation to a free-download library.

## What changed

- Public book cards show **FREE** rather than USD prices.
- A visitor clicks **Download free**, then enters:
  - full name;
  - email address;
  - phone/WhatsApp number.
- The contact is saved in **Django Admin → Free book downloads** before the PDF is served.
- The required privacy acknowledgement is separate from the optional marketing consent checkbox.
- Administrators can filter/search downloader records and export selected records to CSV.
- The book list was rebuilt to fix spacing, inconsistent card sizing, cropped controls and Bootstrap dropdown conflicts.
- The book detail and free-download pages now use the same responsive layout and navigation.
- The books page no longer uses a shopping cart or payment action.
- Hard-coded application/database/email secrets were moved to environment variables.

## Deploy

1. Back up the current website files and database.
2. Copy this project over the current codebase (or apply the patch archive).
3. Create/update your production `.env` using `.env.example` as a guide. Never put the real `.env` in source control.
4. Run migrations:

   ```bash
   python manage.py migrate
   ```

5. Collect static files if your hosting setup requires it:

   ```bash
   python manage.py collectstatic --noinput
   ```

6. Restart the Django/Passenger application.

## Attach the PDFs already supplied in this project

The uploaded project already contains multiple book PDFs and matching covers under `media/books/` and `media/product_images/`.
After the production database and media files are in place, run:

```bash
python manage.py import_existing_books --created-by-email YOUR_ADMIN_EMAIL
```

The command will try to update matching existing books first (using their cover/title), then create only books that are missing. It currently knows about these supplied PDFs:

- Adultery
- Freedom Ignored
- Generational Mandate
- A Sacred Covenant / Marriage
- Music: A Gate to Glory or Darkness
- Spiritual Fathers
- Spiritual Maturity
- The Crisis of Self
- The Watchman's Call
- When God Interrupts Your Labour
- A Call for Deliverance / Masturbation is a Demon

Files such as diagrams, screenshots, DOCX files and the unrelated `LOEM` text file are intentionally not imported as public books.

## Upload additional books manually

In Django Admin:

1. Open **Products**.
2. Add a new product or edit an existing one.
3. Enter the title, author, category and description.
4. Upload the **cover image** under `product_image`.
5. Upload the **PDF/e-book file** under `book_file`.
6. Keep the product active and save it.

The public site will automatically show **Download free** when a `book_file` is present.

## Downloader contact report

Open **Django Admin → Free book downloads**. You can search by name, email, phone or book title, filter by book/date/marketing consent, and use the action **Export selected downloader contacts to CSV**.

## Production media

In production (`DEBUG=False`), Django does not serve `/media/` itself. Ensure your hosting/web server maps the site's `/media/` URL to the project's `media/` directory, otherwise book covers and PDF downloads will return 404 errors.
