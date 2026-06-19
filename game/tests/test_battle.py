from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from game.models import Enemy

User = get_user_model()


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
