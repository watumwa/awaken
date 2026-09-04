# Vercel deployment fix

The previous repository bundled a local `venv`, generated `staticfiles`, a SQLite database, logs, large media files, and a very broad `requirements.txt`. Vercel packages a Django app as one Python Function, so those files pushed the function over the 500 MB uncompressed standard limit.

## What this patch changes

1. Adds `.python-version` (`3.12`).
2. Replaces the development-wide requirements list with the runtime packages actually used by this project.
3. Removes MoviePy/FFmpeg/NumPy from the runtime by reading supported media duration metadata with Mutagen.
4. Adds `.vercelignore` for local/generated files.
5. Adds `vercel.json` `excludeFiles` so source static/media assets are not copied into the Python Function.
6. On Vercel, the existing `media/` directory is collected under `/static/media/` and served by Vercel's CDN. `media/books/` is intentionally kept available to the function because the current free-book download view streams the PDF after saving the downloader's details.

## One-time Git cleanup before the next deployment

Run from the repository root:

```bash
git rm -r --cached venv staticfiles 2>/dev/null || true
git rm --cached db.sqlite3 stderr.log 2>/dev/null || true
git add .gitignore .vercelignore .python-version vercel.json requirements.txt ecom/settings.py ecomapp/utils.py
git commit -m "Reduce Vercel Django function bundle size"
git push origin main
```

Do not delete the local `venv` if you still use it for development; `git rm --cached` removes it from Git tracking only.

## Important limitation for future uploads

Vercel Functions do not provide durable application filesystem storage. The existing media that is committed in Git can be deployed and served from the CDN, but files uploaded later through Django Admin should be moved to persistent object storage (for example S3-compatible storage) if they must survive deployments. For the current 11 free books, keeping the PDFs in `media/books/` is fine and only adds about 10 MB.
