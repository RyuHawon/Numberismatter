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


class BattleTurnTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        self.battle_url = reverse("game:battle")
        self.start_url = reverse("game:start_run")
        self.roll_url = reverse("game:battle_roll")
        self.action_url = reverse("game:battle_action")

    def _setup_battle(
        self,
        phase="action",
        my_roll=3,
        enemy_hp=20,
        enemy_dice=(2, 2),
        my_hp=100,
        is_boss=False,
        gold_dice=(5, 5),
        current_stage=1,
        pending_gold=0,
    ):
        # 무작위 주사위에 의존하지 않도록 세션에 통제된 전투 상태를 직접 세팅한다
        self.client.force_login(self.user)
        session = self.client.session
        session["run"] = {
            "phase": phase,
            "current_act": 1,
            "current_stage": current_stage,
            "hp": my_hp,
            "pending_gold": pending_gold,
            "skills": {},
            "enemy": {
                "name": "테스트적",
                "hp": enemy_hp,
                "max_hp": enemy_hp,
                "dice_min": enemy_dice[0],
                "dice_max": enemy_dice[1],
                "is_boss": is_boss,
                "gold_dice_min": gold_dice[0],
                "gold_dice_max": gold_dice[1],
            },
            "my_roll": my_roll,
        }
        session.save()

    def test_roll_transitions_to_action(self):
        # 주사위 굴리기는 phase를 action으로 바꾸고 캐릭터 주사위 범위 내 값을 저장한다
        self.client.force_login(self.user)
        self.client.post(self.start_url)
        self.client.get(self.battle_url)
        self.client.post(self.roll_url)
        run = self.client.session["run"]
        self.assertEqual(run["phase"], "action")
        character = self.user.character
        self.assertGreaterEqual(run["my_roll"], character.dice_min)
        self.assertLessEqual(run["my_roll"], character.dice_max)

    def test_attack_damages_enemy_and_takes_retaliation(self):
        self._setup_battle(my_roll=3, enemy_hp=20, enemy_dice=(2, 2), my_hp=100)
        self.client.post(self.action_url, {"mode": "attack"})
        run = self.client.session["run"]
        self.assertEqual(run["enemy"]["hp"], 17)  # 20 - 3
        self.assertEqual(run["hp"], 98)  # 100 - 2 (적 반격)
        self.assertEqual(run["phase"], "roll")

    def test_attack_kills_enemy_without_retaliation(self):
        # 적이 죽으면 반격하지 않는다
        self._setup_battle(my_roll=5, enemy_hp=5, enemy_dice=(6, 6), my_hp=100)
        self.client.post(self.action_url, {"mode": "attack"})
        run = self.client.session["run"]
        self.assertEqual(run["enemy"]["hp"], 0)
        self.assertEqual(run["hp"], 100)  # 반격 없음
        self.assertEqual(run["phase"], "won")

    def test_defend_blocks_all_damage(self):
        # 수비는 적이 굴려도 피해를 전부 막는다
        self._setup_battle(my_roll=3, enemy_hp=20, enemy_dice=(6, 6), my_hp=100)
        self.client.post(self.action_url, {"mode": "defend"})
        run = self.client.session["run"]
        self.assertEqual(run["hp"], 100)  # 피해 없음
        self.assertEqual(run["enemy"]["hp"], 20)  # 적도 그대로
        self.assertEqual(run["last_result"]["damage_taken"], 0)
        self.assertIsNotNone(run["last_result"]["enemy_roll"])  # 적은 굴림
        self.assertEqual(run["phase"], "roll")

    def test_player_death(self):
        # HP가 0 이하가 되면 phase가 dead가 된다
        self._setup_battle(my_roll=1, enemy_hp=50, enemy_dice=(6, 6), my_hp=1)
        self.client.post(self.action_url, {"mode": "attack"})
        run = self.client.session["run"]
        self.assertEqual(run["hp"], 0)
        self.assertEqual(run["phase"], "dead")

    def test_action_ignored_in_roll_phase(self):
        # roll 단계에서 공격 요청이 와도 무시된다 (중복 요청 방어)
        self._setup_battle(phase="roll", enemy_hp=20)
        self.client.post(self.action_url, {"mode": "attack"})
        run = self.client.session["run"]
        self.assertEqual(run["enemy"]["hp"], 20)
        self.assertEqual(run["phase"], "roll")

    def test_roll_ignored_in_action_phase(self):
        # action 단계에서 주사위 굴리기 요청이 와도 무시된다
        self._setup_battle(phase="action", my_roll=3)
        self.client.post(self.roll_url)
        run = self.client.session["run"]
        self.assertEqual(run["my_roll"], 3)
        self.assertEqual(run["phase"], "action")

    def test_win_awards_gold(self):
        # 일반몹 처치 시 골드(골드주사위 + gold_bonus)가 pending_gold에 누적된다
        self._setup_battle(my_roll=5, enemy_hp=5, gold_dice=(5, 5), pending_gold=10)
        self.client.post(self.action_url, {"mode": "attack"})
        run = self.client.session["run"]
        self.assertEqual(run["phase"], "won")
        self.assertEqual(run["gold_gained"], 5)  # 골드주사위 5 + gold_bonus 0
        self.assertEqual(run["pending_gold"], 15)  # 기존 10 + 5

    def test_boss_kill_sets_act_clear(self):
        # 보스를 처치하면 phase가 act_clear가 된다
        self._setup_battle(my_roll=5, enemy_hp=5, is_boss=True, gold_dice=(5, 5))
        self.client.post(self.action_url, {"mode": "attack"})
        self.assertEqual(self.client.session["run"]["phase"], "act_clear")

    def test_battle_next_advances_stage(self):
        # 다음으로 진행하면 스테이지가 오르고 적/턴결과가 초기화된다
        self._setup_battle(phase="won", current_stage=1)
        next_url = reverse("game:battle_next")
        self.client.post(next_url)
        run = self.client.session["run"]
        self.assertEqual(run["current_stage"], 2)
        self.assertNotIn("enemy", run)
        self.assertEqual(run["phase"], "roll")

    def test_battle_next_ignored_when_not_won(self):
        # won 상태가 아니면 다음 진행 요청은 무시된다
        self._setup_battle(phase="roll", current_stage=1)
        self.client.post(reverse("game:battle_next"))
        self.assertEqual(self.client.session["run"]["current_stage"], 1)
