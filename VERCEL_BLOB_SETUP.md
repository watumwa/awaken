# Vercel Blob setup for Django media uploads

The production application runs inside Vercel Functions. `/var/task` is
read-only, so Django cannot persist uploaded PDFs, cover images, sermon media,
or thumbnails there.

This project now uses `ecom.storage.VercelBlobStorage` automatically whenever
the `VERCEL` environment variable is present.

## 1. Create/connect the Blob store

In Vercel:

1. Open the **Awakening Saints** project.
2. Open **Storage**.
3. Create/connect a **Blob** store.
4. Use **Public** access for this project (covers are rendered directly in the
   public site; PDF Blob URLs are not shown in the normal download flow).
5. Attach the store to **Production** (and Preview if desired).
6. Confirm the project has the environment variable:

   `BLOB_READ_WRITE_TOKEN`

Do not commit the token to Git.

## 2. Deploy this code

The dependency list includes the official Vercel Python SDK:

`vercel==0.10.0`

Redeploy after the Blob store is connected.

## 3. Apply the migration

Run:

```bash
python manage.py migrate
```

Migration `0007_expand_product_media_paths` increases FileField/ImageField
lengths so complete immutable Blob URLs can be stored safely.

## 4. Test

In Django Admin:

1. Open **Products**.
2. Edit or create a product.
3. Upload a cover image and PDF.
4. Save.
5. Confirm no `/var/task/media/... Read-only file system` exception appears.
6. Open the public books page and test the free-download form.

Existing media already committed under `media/` remains compatible; only new
uploads use Blob storage.

## File-size note

Django Admin uploads are server uploads and therefore still pass through the
Vercel Function request. For very large future files, use direct-to-Blob client
uploads instead. The current supplied book PDFs and cover images are within the
range used by this project.
