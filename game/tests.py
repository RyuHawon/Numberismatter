from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Character

User = get_user_model()


class CharacterSignalTest(TestCase):
    def test_character_created_on_user_creation(self):
        # 유저를 만들면 시그널이 연결된 캐릭터를 자동 생성한다
        user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        self.assertTrue(Character.objects.filter(user=user).exists())

    def test_character_has_default_stats(self):
        # 명세서 기본값으로 캐릭터가 생성되어야 한다
        user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        character = user.character
        self.assertEqual(character.max_hp, 100)
        self.assertEqual(character.dice_min, 1)
        self.assertEqual(character.dice_max, 6)
        self.assertEqual(character.permanent_gold, 0)
        self.assertEqual(character.gold_bonus, 0)

    def test_only_one_character_per_user(self):
        # 유저 정보 수정(재저장) 시 캐릭터가 중복 생성되지 않아야 한다
        user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        user.nickname = "변경된닉"
        user.save()
        self.assertEqual(Character.objects.filter(user=user).count(), 1)


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
