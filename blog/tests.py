import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comments.models import Comment

from .models import Category, Post
from .admin import CategoryAdmin, PostAdmin


class PostModelTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="editor", password="password")

    def test_str_returns_title(self):
        post = Post.objects.create(title="First post", slug="first-post", content="Body", author=self.author)

        self.assertEqual(str(post), "First post")

    def test_published_manager_returns_only_public_posts(self):
        published = Post.objects.create(
            title="Published",
            slug="published",
            content="Body",
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        Post.objects.create(title="Draft", slug="draft", content="Body", author=self.author)

        self.assertEqual(list(Post.published.all()), [published])

    def test_published_post_gets_publish_date_when_missing(self):
        post = Post.objects.create(
            title="Published later",
            slug="published-later",
            content="Body",
            author=self.author,
            status=Post.Status.PUBLISHED,
        )

        self.assertIsNotNone(post.published_at)


class CategoryModelTests(TestCase):
    def test_str_returns_name(self):
        category = Category.objects.create(name="Django", slug="django")

        self.assertEqual(str(category), "Django")

    def test_get_absolute_url_uses_category_slug(self):
        category = Category.objects.create(name="Django", slug="django")

        self.assertEqual(category.get_absolute_url(), reverse("blog:category_post_list", kwargs={"category_slug": "django"}))


class PostViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="editor", password="password")
        self.category = Category.objects.create(name="Django", slug="django")
        self.other_category = Category.objects.create(name="Operations", slug="operations")
        self.published = Post.objects.create(
            title="Published",
            slug="published",
            content="<p>Public body</p>",
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        self.published.categories.add(self.category)
        self.draft = Post.objects.create(title="Draft", slug="draft", content="Draft body", author=self.author)
        self.draft.categories.add(self.other_category)

    def post_permission(self, codename):
        return Permission.objects.get(content_type__app_label="blog", codename=codename)

    def test_post_list_shows_only_published_posts(self):
        response = self.client.get(reverse("blog:post_list"))

        self.assertContains(response, self.published.title)
        self.assertContains(response, self.category.name)
        self.assertNotContains(response, self.draft.title)
        self.assertNotContains(response, self.other_category.name)

    def test_category_post_list_shows_only_posts_in_category(self):
        other_published = Post.objects.create(
            title="Other published",
            slug="other-published",
            content="Body",
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        other_published.categories.add(self.other_category)

        response = self.client.get(self.category.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published.title)
        self.assertNotContains(response, other_published.title)

    def test_post_detail_shows_published_post(self):
        response = self.client.get(self.published.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published.title)
        self.assertContains(response, self.category.name)

    def test_post_detail_does_not_show_draft(self):
        response = self.client.get(self.draft.get_absolute_url())

        self.assertEqual(response.status_code, 404)

    def test_comment_submission_creates_unapproved_comment(self):
        response = self.client.post(
            self.published.get_absolute_url(),
            {"name": "Reader", "email": "reader@example.com", "body": "Useful post."},
            follow=True,
        )

        self.assertRedirects(response, self.published.get_absolute_url())
        comment = Comment.objects.get(post=self.published)
        self.assertFalse(comment.is_approved)
        self.assertEqual(comment.email, "reader@example.com")

    def test_post_detail_shows_only_approved_comments(self):
        Comment.objects.create(
            post=self.published,
            name="Approved",
            email="approved@example.com",
            body="Visible comment.",
            is_approved=True,
        )
        Comment.objects.create(
            post=self.published,
            name="Pending",
            email="pending@example.com",
            body="Hidden comment.",
        )

        response = self.client.get(self.published.get_absolute_url())

        self.assertContains(response, "Visible comment.")
        self.assertNotContains(response, "Hidden comment.")

    def test_edit_buttons_are_hidden_without_post_permissions(self):
        response = self.client.get(self.published.get_absolute_url())

        self.assertNotContains(response, reverse("blog:post_update", kwargs={"slug": self.published.slug}))
        self.assertNotContains(response, reverse("blog:post_create"))

    def test_edit_buttons_are_visible_with_post_permissions(self):
        self.author.user_permissions.add(
            self.post_permission("add_post"),
            self.post_permission("change_post"),
        )
        self.client.force_login(self.author)

        list_response = self.client.get(reverse("blog:post_list"))
        detail_response = self.client.get(self.published.get_absolute_url())

        self.assertContains(list_response, reverse("blog:post_create"))
        self.assertContains(list_response, reverse("blog:post_update", kwargs={"slug": self.published.slug}))
        self.assertContains(detail_response, reverse("blog:post_update", kwargs={"slug": self.published.slug}))

    def test_anonymous_user_cannot_open_post_create_page(self):
        response = self.client.get(reverse("blog:post_create"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_authenticated_user_without_permission_cannot_open_post_create_page(self):
        self.client.force_login(self.author)

        response = self.client.get(reverse("blog:post_create"))

        self.assertEqual(response.status_code, 403)

    def test_user_with_add_permission_can_create_post(self):
        self.author.user_permissions.add(self.post_permission("add_post"))
        self.client.force_login(self.author)

        response = self.client.post(
            reverse("blog:post_create"),
            {
                "title": "Editor post",
                "slug": "editor-post",
                "excerpt": "Short summary",
                "content": "<p>Editor body</p>",
                "status": Post.Status.DRAFT,
                "published_at": "",
                "categories": [self.category.pk],
            },
        )

        post = Post.objects.get(slug="editor-post")
        self.assertRedirects(response, reverse("blog:post_list"))
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.categories.get(), self.category)

    def test_user_with_change_permission_can_edit_post(self):
        self.author.user_permissions.add(self.post_permission("change_post"))
        self.client.force_login(self.author)

        response = self.client.post(
            reverse("blog:post_update", kwargs={"slug": self.published.slug}),
            {
                "title": "Updated title",
                "slug": self.published.slug,
                "excerpt": self.published.excerpt,
                "content": "<p>Updated body</p>",
                "status": Post.Status.PUBLISHED,
                "published_at": self.published.published_at.strftime("%Y-%m-%dT%H:%M"),
                "categories": [self.category.pk],
            },
        )

        self.published.refresh_from_db()
        self.assertRedirects(response, self.published.get_absolute_url())
        self.assertEqual(self.published.title, "Updated title")
        self.assertEqual(self.published.content, "<p>Updated body</p>")


class PostAdminTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="editor", password="password")
        self.post_admin = PostAdmin(Post, AdminSite())
        self.category_admin = CategoryAdmin(Category, AdminSite())

    def test_category_admin_prepopulates_slug_from_name(self):
        self.assertEqual(self.category_admin.prepopulated_fields, {"slug": ("name",)})

    def test_view_on_site_is_hidden_for_drafts(self):
        post = Post.objects.create(title="Draft", slug="draft", content="Body", author=self.author)

        self.assertIsNone(self.post_admin.get_view_on_site_url(post))

    def test_view_on_site_is_available_for_published_posts(self):
        post = Post.objects.create(
            title="Published",
            slug="published",
            content="Body",
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )

        self.assertIsNotNone(self.post_admin.get_view_on_site_url(post))


class PostAdminImageUploadTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.client.force_login(self.user)

    def tearDown(self):
        shutil.rmtree(self.media_root, ignore_errors=True)

    @override_settings(
        MEDIA_URL="/media/",
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        },
    )
    def test_admin_content_image_upload_returns_url(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            image = SimpleUploadedFile(
                "pasted.png",
                (
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
                    b"\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
                    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
                ),
                content_type="image/png",
            )

            response = self.client.post(reverse("admin:blog_post_upload_content_image"), {"image": image})

        self.assertEqual(response.status_code, 200)
        self.assertIn("/media/posts/content/", response.json()["url"])
