from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class SignUpViewTest(TestCase):
    def setUp(self):
        self.url = reverse("accounts:signup")

    def test_get_renders_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/signup.html")

    def test_post_creates_user_and_redirects(self):
        response = self.client.post(
            self.url,
            {
                "email": "new@test.com",
                "nickname": "새유저",
                "password1": "pw-long-1234",
                "password2": "pw-long-1234",
            },
        )
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertTrue(User.objects.filter(email="new@test.com").exists())


class LoginLogoutViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        self.login_url = reverse("accounts:login")
        self.logout_url = reverse("accounts:logout")

    def test_login_success(self):
        response = self.client.post(self.login_url, {"username": "user@test.com", "password": "pw-long-1234"})
        self.assertRedirects(response, "/")
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_wrong_password(self):
        response = self.client.post(self.login_url, {"username": "user@test.com", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_get_not_allowed(self):
        # Django 5+ 부터 GET 로그아웃은 허용되지 않는다
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 405)

    def test_logout_post(self):
        self.client.force_login(self.user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 302)
