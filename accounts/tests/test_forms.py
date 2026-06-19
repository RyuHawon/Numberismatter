from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.forms import SignUpForm

User = get_user_model()


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
