from django.contrib.auth import get_user_model
from django.test import TestCase

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
