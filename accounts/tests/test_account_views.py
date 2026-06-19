from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class ProfileEditViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", nickname="원래닉", password="pw-long-1234")
        self.url = reverse("accounts:profile_edit")

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_form_prefilled_with_current_nickname(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, "원래닉")

    def test_nickname_updated(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"nickname": "바뀐닉"})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, "바뀐닉")


class PasswordChangeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", nickname="유저", password="oldpass-1234")
        self.url = reverse("accounts:password_change")

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_password_changed(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "old_password": "oldpass-1234",
                "new_password1": "brandnew-5678",
                "new_password2": "brandnew-5678",
            },
        )
        self.assertRedirects(response, reverse("accounts:password_change_done"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("brandnew-5678"))


class AccountDeleteViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        self.url = reverse("accounts:account_delete")

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_does_not_delete(self):
        # 확인 페이지(GET)는 계정을 비활성화하지 않는다
        self.client.force_login(self.user)
        self.client.get(self.url)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_post_soft_deletes(self):
        # 탈퇴(POST)는 행을 삭제하지 않고 is_active만 False로 바꾼다
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_deleted_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "user@test.com", "password": "pw-long-1234"},
        )
        self.assertFalse(response.wsgi_request.user.is_authenticated)
