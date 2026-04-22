# Django Blog

A small Django blog project with PostgreSQL, MinIO-compatible media storage, a separate comments app, and Tailwind CSS loaded without a build step.

## Current Scope

- Blog posts with title, slug, excerpt, WYSIWYG-editable content, cover image, status, publish date, and author.
- Public post list and post detail pages.
- Permission-protected public post creation and editing screens, separate from Django admin.
- Custom editorial dashboard for authenticated users with native Django permissions. It lists every post, links to edit/delete actions, manages categories, and moderates comments.
- Post categories with a many-to-many relationship to posts.
- Public login page using Django's native authentication views.
- Public registration page with a custom signup form and automatic login after account creation.
- Public comment form on post detail pages.
- Comments are stored unapproved by default and can be moderated in the custom dashboard or Django admin.
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

## Tailwind

Tailwind CSS is loaded from the CDN in `templates/base.html`. There is no Node.js build step.

The public interface uses a blog-first editorial design system defined through the Tailwind CDN configuration in `templates/base.html`. Its visual direction is inspired by `https://guikastner.github.io/web/`: premium blue accents, a light grid-backed background, pill navigation, rounded article cards, and the Space Grotesk / Source Serif 4 font pairing. It keeps the post list chronological and constrains article detail text to a readable measure, while preserving visible focus states, accessible form labels and errors, and touch-friendly buttons/links without adding a frontend build pipeline.

The public navigation uses inline SVG icons, so it does not require an icon package or build step. Editorial actions are shown with Django's native template permission checks: users with `blog.add_post` can open the public post creation screen, users with `blog.change_post` can edit the current post from its detail page, and staff users can access the admin index.

## Custom Dashboard

The custom dashboard starts at `/dashboard/` and uses the same Tailwind CDN visual system as the public site. It is not a replacement for Django's built-in admin internals; it is a focused editorial interface for common blog operations.

Dashboard permissions use Django's native model permissions:

```text
blog.view_post        view every existing post, including drafts
blog.change_post      edit posts
blog.delete_post      delete posts
blog.add_category     add categories
comments.change_comment approve or reject comments
comments.delete_comment delete comments
```

Users without the required permission receive a forbidden response even when logged in. Superusers have access to all dashboard sections.

## Editorial Editor

Post creation and post editing use the blog's own public editor at `/posts/new/` and `/posts/<slug>/edit/`. These screens use Django class-based views and native permissions: `blog.add_post` for creating posts and `blog.change_post` for editing posts.

The content editor is a local WYSIWYG control backed by the `Post.content` field. It supports standardized formatting controls, links, uploaded images, pasted image media, and a dedicated HTML tab inside the editor for source editing. Editor media is saved through Django's configured default storage under:

```text
posts/content/YYYY/MM/
```

The media upload endpoint uses the same type and size validation configured for blog images and works with local media storage or the configured MinIO-compatible storage.

## Authentication

Django's built-in authentication URLs are mounted under `/accounts/`. The public login screen is available at `/accounts/login/`, uses `templates/registration/login.html`, and redirects authenticated users back to the post list by default.

Custom registration lives in the `accounts` app without adding a custom user model. The signup screen is available at `/accounts/signup/`, uses `templates/registration/signup.html`, requires a unique email address, creates the user through Django's native `UserCreationForm`, and logs the new user in after a successful signup.

## Tests

After installing dependencies and configuring a database, run:

```bash
python manage.py test
```

The Compose file also includes a test container that reuses the app image, disables startup migrations/superuser creation, and runs the same Django test suite against a temporary SQLite database:

```bash
docker compose run --rm test
```

## Architecture Notes

- `blog` owns posts, categories, public post views, custom dashboard views/templates, and post admin configuration.
- `comments` owns comment storage, public comment validation, and comment moderation admin.
- `accounts` owns custom public registration while still using Django's built-in user model and authentication views for login/logout.
- Django native APIs are preferred for models, forms, views, admin, storage, and database configuration.
- Secrets must stay outside the repository.
