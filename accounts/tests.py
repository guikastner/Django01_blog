from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SignUpViewTests(TestCase):
    def test_signup_page_uses_custom_template(self):
        response = self.client.get(reverse("accounts:signup"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create your profile.")
        self.assertContains(response, 'name="email"')

    def test_signup_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "reader",
                "email": "reader@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
            follow=True,
        )

        user = get_user_model().objects.get(username="reader")
        self.assertRedirects(response, reverse("blog:post_list"))
        self.assertEqual(user.email, "reader@example.com")
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(user.pk))

    def test_signup_requires_unique_email(self):
        get_user_model().objects.create_user(
            username="existing",
            email="reader@example.com",
            password="ComplexPass123!",
        )

        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "reader",
                "email": "reader@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A user with this email already exists.")
        self.assertFalse(get_user_model().objects.filter(username="reader").exists())
