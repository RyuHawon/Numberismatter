from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class HomeViewTest(TestCase):
    def setUp(self):
        self.url = reverse("game:home")

    def test_home_renders_for_anonymous(self):
        # 비로그인 상태에서도 홈은 정상 응답하고 게임 시작 버튼은 보이지 않는다
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game/home.html")
        self.assertNotContains(response, "게임 시작")

    def test_home_shows_start_button_for_authenticated(self):
        # 로그인 상태에서는 닉네임과 게임 시작 버튼이 보인다
        user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertContains(response, "유저")
        self.assertContains(response, "게임 시작")
