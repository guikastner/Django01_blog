# Django Blog

A small Django blog project with PostgreSQL, MinIO-compatible media storage, a separate comments app, and Tailwind CSS loaded without a build step.

## Current Scope

- Blog posts with title, slug, excerpt, WYSIWYG-editable content, cover image, categories, status, publish date, and author.
- Categories with admin-managed names, slugs, descriptions, and public category archive pages.
- Public post list, category-filtered post lists, and post detail pages.
- Blog-styled post creation and editing pages protected by Django's native `add_post` and `change_post` permissions, including category assignment.
- Public comment form on post detail pages.
- Comments are stored unapproved by default and can be moderated in Django admin.
- SQLite for local development and PostgreSQL configuration for production through environment variables.
- Optional S3-compatible media storage for MinIO through `django-storages`.
- Initial model, query, form, and view tests.

## Requirements

- Python 3.12 or newer.
- PostgreSQL for production.
- Access to an existing MinIO bucket when `USE_S3_STORAGE=True`.
- Docker Compose for the included PostgreSQL service.

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy the example environment file and adjust values as needed:

```bash
copy .env.example .env
```

Set `DJANGO_ENV=development` to use the local SQLite database and the `*_DEV` MinIO variables. Set `DJANGO_ENV=production` to use the `*_PROD` PostgreSQL and MinIO variables. Keep real passwords and access keys only in local or deployment environment variables, never in committed files.

Start the Django container. On startup, it can run migrations and create the configured admin user when the user does not exist:

```bash
docker compose up -d
```

The Docker Compose PostgreSQL service remains available for production-like local checks through the `POSTGRES_LOCAL_*` variables, but it is not required for the default development database.

Load the environment variables from `.env` in your shell, then run migrations explicitly when ready. In development, migrations create or update the local SQLite file configured by `SQLITE_NAME_DEV`:

```bash
python manage.py migrate
python manage.py ensure_superuser
python manage.py runserver
```

This repository does not auto-load `.env`; set the variables in your shell or add a local environment loader later.

## Initial Admin

The project includes an idempotent `ensure_superuser` command for container startup. It reads these environment variables:

```text
RUN_MIGRATIONS_ON_STARTUP=true
CREATE_SUPERUSER_ON_STARTUP=true
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=change-me-admin-password
```

When `docker-entrypoint.sh` runs, it runs migrations if `RUN_MIGRATIONS_ON_STARTUP=true`, then creates the configured superuser only if it does not already exist. It does not change the password of an existing user.

## Media Storage

By default, uploaded files use local Django media storage. Set `USE_S3_STORAGE=True` and configure the `AWS_*` variables to use your existing MinIO bucket or another S3-compatible backend.

The project supports separate MinIO settings for development and production:

```text
AWS_STORAGE_BUCKET_NAME_DEV=djangoblogdev
AWS_STORAGE_BUCKET_NAME_PROD=djangoblogprod
AWS_LOCATION_DEV=media
AWS_LOCATION_PROD=media
```

The active bucket is selected by `DJANGO_ENV`. Endpoint, credentials, region, custom domain, addressing style, upload location, and query string auth can also be set separately with the same `_DEV` and `_PROD` suffixes.

The cover image path is organized as:

```text
posts/covers/YYYY/MM/
```

Allowed cover image extensions are JPG, JPEG, PNG, and WebP. The default maximum upload size is 5 MB.

## Categories

Categories are managed in Django admin through the `blog` app. Each category has a unique name and slug, and posts can be assigned to one or more categories from the post edit form.

Public category navigation appears on the home page and post detail pages. Category archive URLs use:

```text
/categories/<slug>/
```

Only categories attached to published posts are shown publicly.

## Tailwind

Tailwind CSS is loaded from the CDN in `templates/base.html`. There is no Node.js build step.

The public interface uses a blog-first editorial design system defined through the Tailwind CDN configuration in `templates/base.html`. Its visual direction is inspired by `https://guikastner.github.io/web/`: premium blue accents, a light grid-backed background, pill navigation, rounded article cards, and the Space Grotesk / Source Serif 4 font pairing. It keeps the post list chronological and constrains article detail text to a readable measure, while preserving visible focus states, accessible form labels and errors, and touch-friendly buttons/links without adding a frontend build pipeline.

## Tests

After installing dependencies and configuring a database, run:

```bash
python manage.py test
```

## Architecture Notes

- `blog` owns posts, categories, public post views, templates, and post admin configuration.
- `comments` owns comment storage, public comment validation, and comment moderation admin.
- Post creation and editing outside the admin use Django class-based generic views plus native auth permissions. Users need `blog.add_post` to create posts and `blog.change_post` to edit posts; superusers have both permissions automatically.
- Django native APIs are preferred for models, forms, views, admin, storage, and database configuration.
- Secrets must stay outside the repository.
