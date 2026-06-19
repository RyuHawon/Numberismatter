from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Character, Enemy

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


class RunSessionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        self.start_url = reverse("game:start_run")
        self.abandon_url = reverse("game:abandon_run")

    def test_login_required(self):
        response = self.client.post(self.start_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_get_not_allowed(self):
        # 런 시작/포기는 상태 변경이라 POST만 허용한다
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.start_url).status_code, 405)
        self.assertEqual(self.client.get(self.abandon_url).status_code, 405)

    def test_start_creates_run_with_default_state(self):
        self.client.force_login(self.user)
        self.client.post(self.start_url)
        run = self.client.session["run"]
        self.assertEqual(run["phase"], "roll")
        self.assertEqual(run["current_act"], 1)
        self.assertEqual(run["current_stage"], 1)
        self.assertEqual(run["hp"], self.user.character.max_hp)
        self.assertEqual(run["pending_gold"], 0)
        self.assertEqual(run["skills"], {})

    def test_start_does_not_overwrite_existing_run(self):
        # 이미 진행 중인 런이 있으면 다시 시작해도 덮어쓰지 않는다
        self.client.force_login(self.user)
        session = self.client.session
        session["run"] = {"current_act": 2, "hp": 50}
        session.save()
        self.client.post(self.start_url)
        self.assertEqual(self.client.session["run"]["current_act"], 2)
        self.assertEqual(self.client.session["run"]["hp"], 50)

    def test_abandon_removes_run(self):
        self.client.force_login(self.user)
        self.client.post(self.start_url)
        self.client.post(self.abandon_url)
        self.assertNotIn("run", self.client.session)


class BattleViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        self.battle_url = reverse("game:battle")
        self.start_url = reverse("game:start_run")

    def test_login_required(self):
        response = self.client.get(self.battle_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_redirects_home_without_run(self):
        # 진행 중인 런이 없으면 전투 화면 대신 홈으로 보낸다
        self.client.force_login(self.user)
        response = self.client.get(self.battle_url)
        self.assertRedirects(response, reverse("game:home"))

    def test_spawns_enemy_for_current_stage(self):
        # 전투 진입 시 현재 act/stage의 적이 뽑히고 hp는 max_hp로 초기화된다
        self.client.force_login(self.user)
        self.client.post(self.start_url)
        self.client.get(self.battle_url)
        run = self.client.session["run"]
        enemy = run["enemy"]
        candidate_names = set(
            Enemy.objects.filter(act=run["current_act"], stage=run["current_stage"]).values_list("name", flat=True)
        )
        self.assertIn(enemy["name"], candidate_names)
        self.assertEqual(enemy["hp"], enemy["max_hp"])

    def test_enemy_persists_on_revisit(self):
        # 전투 화면에 다시 들어와도 같은 적이 유지된다 (세션 저장)
        self.client.force_login(self.user)
        self.client.post(self.start_url)
        self.client.get(self.battle_url)
        first = self.client.session["run"]["enemy"]["name"]
        self.client.get(self.battle_url)
        second = self.client.session["run"]["enemy"]["name"]
        self.assertEqual(first, second)
