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
from .admin import PostAdmin


ONE_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
    b"\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


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


class PostViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="editor", password="password")
        self.published = Post.objects.create(
            title="Published",
            slug="published",
            content="<p>Public body</p>",
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        self.draft = Post.objects.create(title="Draft", slug="draft", content="Draft body", author=self.author)

    def test_post_list_shows_only_published_posts(self):
        response = self.client.get(reverse("blog:post_list"))

        self.assertContains(response, self.published.title)
        self.assertNotContains(response, self.draft.title)

    def test_post_detail_shows_published_post(self):
        response = self.client.get(self.published.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published.title)

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

    def test_public_navigation_hides_editor_actions_for_anonymous_users(self):
        response = self.client.get(reverse("blog:post_list"))

        self.assertContains(response, 'data-nav-icon="posts"')
        self.assertNotContains(response, "New post")
        self.assertNotContains(response, "Admin")

    def test_public_navigation_shows_visible_editor_actions_for_staff(self):
        staff_user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.client.force_login(staff_user)

        response = self.client.get(self.published.get_absolute_url())

        self.assertContains(response, "New post")
        self.assertContains(response, "Edit post")
        self.assertContains(response, "Admin")
        self.assertContains(response, 'data-nav-icon="new-post"')
        self.assertContains(response, 'data-nav-icon="edit-post"')
        self.assertContains(response, 'data-nav-icon="admin"')
        self.assertContains(response, reverse("blog:post_create"))
        self.assertContains(response, reverse("blog:post_update", kwargs={"slug": self.published.slug}))
        self.assertNotContains(response, reverse("admin:blog_post_add"))
        self.assertNotContains(response, reverse("admin:blog_post_change", args=[self.published.pk]))


class PostEditorViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="editor", password="password")
        self.post = Post.objects.create(
            title="Editable",
            slug="editable",
            content="<p>Old body</p>",
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )

    def add_permission(self, user, codename):
        user.user_permissions.add(Permission.objects.get(codename=codename))

    def test_create_post_requires_add_permission(self):
        user = get_user_model().objects.create_user(username="writer", password="password")
        self.client.force_login(user)

        response = self.client.get(reverse("blog:post_create"))

        self.assertEqual(response.status_code, 403)

    def test_create_post_uses_public_editor_for_authorized_user(self):
        user = get_user_model().objects.create_user(username="writer", password="password")
        self.add_permission(user, "add_post")
        self.client.force_login(user)

        response = self.client.get(reverse("blog:post_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create post")
        self.assertContains(response, "blog/post_editor.js")
        self.assertContains(response, reverse("blog:post_content_upload"))

    def test_authorized_user_can_create_post(self):
        user = get_user_model().objects.create_user(username="writer", password="password")
        self.add_permission(user, "add_post")
        self.client.force_login(user)

        response = self.client.post(
            reverse("blog:post_create"),
            {
                "title": "New draft",
                "slug": "new-draft",
                "excerpt": "Short",
                "content": "<p>Created body</p>",
                "status": Post.Status.DRAFT,
                "published_at": "",
            },
        )

        created = Post.objects.get(slug="new-draft")
        self.assertRedirects(response, reverse("blog:post_list"))
        self.assertEqual(created.author, user)
        self.assertEqual(created.content, "<p>Created body</p>")

    def test_edit_post_requires_change_permission(self):
        user = get_user_model().objects.create_user(username="reader", password="password")
        self.client.force_login(user)

        response = self.client.get(reverse("blog:post_update", kwargs={"slug": self.post.slug}))

        self.assertEqual(response.status_code, 403)

    def test_authorized_user_can_edit_post_in_public_editor(self):
        user = get_user_model().objects.create_user(username="publisher", password="password")
        self.add_permission(user, "change_post")
        self.client.force_login(user)

        get_response = self.client.get(reverse("blog:post_update", kwargs={"slug": self.post.slug}))

        self.assertContains(get_response, "Edit post")
        self.assertContains(get_response, "Update post")
        self.assertContains(get_response, 'data-editor-icon="update-post"')

        response = self.client.post(
            reverse("blog:post_update", kwargs={"slug": self.post.slug}),
            {
                "title": "Updated title",
                "slug": "updated-title",
                "excerpt": "Updated excerpt",
                "content": "<p>Updated body</p>",
                "status": Post.Status.PUBLISHED,
                "published_at": self.post.published_at.strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.post.refresh_from_db()
        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertEqual(self.post.title, "Updated title")
        self.assertEqual(self.post.slug, "updated-title")
        self.assertEqual(self.post.content, "<p>Updated body</p>")

    def test_content_upload_requires_editor_permission(self):
        user = get_user_model().objects.create_user(username="reader", password="password")
        self.client.force_login(user)
        image = SimpleUploadedFile("pasted.png", b"not-a-real-image", content_type="image/png")

        response = self.client.post(reverse("blog:post_content_upload"), {"image": image})

        self.assertEqual(response.status_code, 403)

    @override_settings(
        MEDIA_URL="/media/",
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        },
    )
    def test_content_upload_accepts_image_for_authorized_user(self):
        media_root = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(media_root, ignore_errors=True))
        user = get_user_model().objects.create_user(username="uploader", password="password")
        self.add_permission(user, "change_post")
        self.client.force_login(user)

        with override_settings(MEDIA_ROOT=media_root):
            image = SimpleUploadedFile(
                "pasted.png",
                ONE_PIXEL_PNG,
                content_type="image/png",
            )

            response = self.client.post(reverse("blog:post_content_upload"), {"image": image})

        self.assertEqual(response.status_code, 200)
        self.assertIn("/media/posts/content/", response.json()["url"])

    def test_content_upload_rejects_spoofed_image_content(self):
        user = get_user_model().objects.create_user(username="spoofed-uploader", password="password")
        self.add_permission(user, "change_post")
        self.client.force_login(user)
        image = SimpleUploadedFile("pasted.png", b"not-a-real-image", content_type="image/png")

        response = self.client.post(reverse("blog:post_content_upload"), {"image": image})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Uploaded file is not a valid JPEG, PNG, or WebP image.")

    def test_content_upload_rejects_declared_type_mismatch(self):
        user = get_user_model().objects.create_user(username="mismatch-uploader", password="password")
        self.add_permission(user, "change_post")
        self.client.force_login(user)
        image = SimpleUploadedFile("pasted.jpg", ONE_PIXEL_PNG, content_type="image/jpeg")

        response = self.client.post(reverse("blog:post_content_upload"), {"image": image})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Uploaded image content does not match its declared type.")


class DashboardViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="editor", password="password")
        self.published = Post.objects.create(
            title="Published",
            slug="dashboard-published",
            content="<p>Public body</p>",
            author=self.author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        self.draft = Post.objects.create(
            title="Draft dashboard post",
            slug="dashboard-draft",
            content="<p>Draft body</p>",
            author=self.author,
        )
        self.user = get_user_model().objects.create_user(username="manager", password="password")

    def add_permission(self, user, codename, app_label="blog"):
        user.user_permissions.add(Permission.objects.get(codename=codename, content_type__app_label=app_label))

    def test_dashboard_requires_post_view_permission(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("blog:dashboard_posts"))

        self.assertEqual(response.status_code, 403)

    def test_dashboard_lists_all_posts_for_authorized_user(self):
        self.add_permission(self.user, "view_post")
        self.client.force_login(self.user)

        response = self.client.get(reverse("blog:dashboard_posts"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published.title)
        self.assertContains(response, self.draft.title)

    def test_authorized_user_can_delete_post_from_dashboard(self):
        self.add_permission(self.user, "view_post")
        self.add_permission(self.user, "delete_post")
        self.client.force_login(self.user)

        response = self.client.post(reverse("blog:dashboard_post_delete", kwargs={"slug": self.draft.slug}))

        self.assertRedirects(response, reverse("blog:dashboard_posts"))
        self.assertFalse(Post.objects.filter(pk=self.draft.pk).exists())

    def test_authorized_user_can_add_category(self):
        self.add_permission(self.user, "add_category")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("blog:dashboard_categories"),
            {"name": "Django", "slug": "django", "description": "Django notes."},
        )

        self.assertRedirects(response, reverse("blog:dashboard_categories"))
        self.assertTrue(Category.objects.filter(slug="django").exists())

    def test_post_form_accepts_categories(self):
        category = Category.objects.create(name="Python", slug="python")
        self.add_permission(self.user, "add_post")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("blog:post_create"),
            {
                "title": "Categorized",
                "slug": "categorized",
                "excerpt": "",
                "content": "<p>Body</p>",
                "categories": [str(category.pk)],
                "status": Post.Status.DRAFT,
                "published_at": "",
            },
        )

        post = Post.objects.get(slug="categorized")
        self.assertRedirects(response, reverse("blog:post_list"))
        self.assertEqual(list(post.categories.all()), [category])

    def test_authorized_user_can_moderate_comments(self):
        comment = Comment.objects.create(
            post=self.published,
            name="Reader",
            email="reader@example.com",
            body="Needs approval.",
        )
        self.add_permission(self.user, "change_comment", app_label="comments")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("blog:dashboard_comments"),
            {"comment_id": comment.pk, "action": "approve"},
        )

        comment.refresh_from_db()
        self.assertRedirects(response, reverse("blog:dashboard_comments"))
        self.assertTrue(comment.is_approved)

    def test_delete_comment_requires_delete_permission(self):
        comment = Comment.objects.create(
            post=self.published,
            name="Reader",
            email="reader@example.com",
            body="Remove me.",
        )
        self.add_permission(self.user, "change_comment", app_label="comments")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("blog:dashboard_comments"),
            {"comment_id": comment.pk, "action": "delete"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())


class AuthenticationViewTests(TestCase):
    def test_login_page_uses_public_template(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in to write.")
        self.assertContains(response, 'name="username"')

    def test_public_navigation_shows_login_link_for_anonymous_users(self):
        response = self.client.get(reverse("blog:post_list"))

        self.assertContains(response, reverse("login"))
        self.assertContains(response, "Login")
        self.assertContains(response, reverse("accounts:signup"))
        self.assertContains(response, "Register")

    def test_public_navigation_shows_logout_button_for_authenticated_users(self):
        user = get_user_model().objects.create_user(username="reader", password="password")
        self.client.force_login(user)

        response = self.client.get(reverse("blog:post_list"))

        self.assertContains(response, reverse("logout"))
        self.assertContains(response, "Logout")
        self.assertNotContains(response, "Login")

    def test_logout_requires_post_and_redirects_to_post_list(self):
        user = get_user_model().objects.create_user(username="reader", password="password")
        self.client.force_login(user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("blog:post_list"))
        self.assertNotIn("_auth_user_id", self.client.session)


class PostAdminTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="editor", password="password")
        self.post_admin = PostAdmin(Post, AdminSite())

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
                ONE_PIXEL_PNG,
                content_type="image/png",
            )

            response = self.client.post(reverse("admin:blog_post_upload_content_image"), {"image": image})

        self.assertEqual(response.status_code, 200)
        self.assertIn("/media/posts/content/", response.json()["url"])

    def test_admin_content_image_upload_rejects_spoofed_content(self):
        image = SimpleUploadedFile("pasted.png", b"not-a-real-image", content_type="image/png")

        response = self.client.post(reverse("admin:blog_post_upload_content_image"), {"image": image})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Uploaded file is not a valid JPEG, PNG, or WebP image.")
