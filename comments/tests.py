from django.contrib.auth import get_user_model
from django.test import TestCase

from blog.models import Post

from .forms import CommentForm
from .models import Comment


class CommentModelTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="editor", password="password")
        self.post = Post.objects.create(title="Post", slug="post", content="Body", author=self.author)

    def test_new_comment_is_not_approved_by_default(self):
        comment = Comment.objects.create(
            post=self.post,
            name="Reader",
            email="reader@example.com",
            body="A thoughtful comment.",
        )

        self.assertFalse(comment.is_approved)


class CommentFormTests(TestCase):
    def test_valid_comment_form(self):
        form = CommentForm(
            data={"name": "Reader", "email": "reader@example.com", "body": "A thoughtful comment."}
        )

        self.assertTrue(form.is_valid())

    def test_comment_form_requires_valid_email(self):
        form = CommentForm(data={"name": "Reader", "email": "not-email", "body": "A thoughtful comment."})

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
