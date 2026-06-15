from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import SignUpForm

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        self.assertEqual(user.email, "user@test.com")
        self.assertEqual(user.nickname, "유저")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        # 비밀번호는 평문이 아니라 해싱되어 저장되어야 한다
        self.assertNotEqual(user.password, "pw-long-1234")
        self.assertTrue(user.check_password("pw-long-1234"))

    def test_create_superuser(self):
        admin = User.objects.create_superuser(email="admin@test.com", nickname="관리자", password="pw-long-1234")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.nickname, "관리자")

    def test_nickname_in_required_fields(self):
        # createsuperuser가 nickname을 입력받아야 빈 닉네임/UNIQUE 충돌이 발생하지 않는다
        self.assertIn("nickname", User.REQUIRED_FIELDS)

    def test_email_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", nickname="유저", password="pw-long-1234")

    def test_str_returns_nickname(self):
        user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        self.assertEqual(str(user), "유저")


class SignUpFormTest(TestCase):
    def _valid_data(self, **overrides):
        data = {
            "email": "new@test.com",
            "nickname": "새유저",
            "password1": "pw-long-1234",
            "password2": "pw-long-1234",
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = SignUpForm(self._valid_data())
        self.assertTrue(form.is_valid())

    def test_invalid_email_format(self):
        form = SignUpForm(self._valid_data(email="notanemail"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_password_mismatch(self):
        form = SignUpForm(self._valid_data(password2="different-9999"))
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_duplicate_email(self):
        User.objects.create_user(email="dup@test.com", nickname="기존", password="pw-long-1234")
        form = SignUpForm(self._valid_data(email="dup@test.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_duplicate_nickname(self):
        User.objects.create_user(email="other@test.com", nickname="중복닉", password="pw-long-1234")
        form = SignUpForm(self._valid_data(nickname="중복닉"))
        self.assertFalse(form.is_valid())
        self.assertIn("nickname", form.errors)


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
