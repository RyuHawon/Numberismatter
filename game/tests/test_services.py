from django.contrib.auth import get_user_model
from django.test import TestCase

from game import services
from game.models import CharacterUpgrade, Upgrade

User = get_user_model()


class UpgradeCostTest(TestCase):
    def test_cost_scales_with_level(self):
        # 비용 = 기본비용 + 레벨 × COST_STEP(10)
        upg = Upgrade.objects.create(
            name="테스트", description="", cost=30, effect="max_hp", max_level=5, effect_per_level=10
        )
        self.assertEqual(services.upgrade_cost(upg, 0), 30)  # 처음 구매 = 기본
        self.assertEqual(services.upgrade_cost(upg, 1), 40)  # +10
        self.assertEqual(services.upgrade_cost(upg, 3), 60)  # +30


class BuildShopTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@test.com", nickname="유저", password="pw-long-1234")
        self.character = self.user.character
        # 시드된 업그레이드를 지우고 통제된 1종으로 검증한다
        Upgrade.objects.all().delete()
        self.hp = Upgrade.objects.create(
            name="최대 HP", description="최대 체력 +10", cost=30, effect="max_hp", max_level=3, effect_per_level=10
        )

    def test_unowned_upgrade_is_level_zero(self):
        # 보유 안 한 업그레이드는 레벨 0, 기본 비용으로 나온다
        self.character.permanent_gold = 100
        self.character.save()
        item = services.build_shop(self.character)[0]
        self.assertEqual(item["level"], 0)
        self.assertEqual(item["cost"], 30)
        self.assertFalse(item["maxed"])
        self.assertTrue(item["affordable"])  # 100 >= 30

    def test_owned_level_and_scaled_cost(self):
        # 보유 레벨이 반영되고 비용이 레벨만큼 오른다
        CharacterUpgrade.objects.create(character=self.character, upgrade=self.hp, level=2)
        self.character.permanent_gold = 100
        self.character.save()
        item = services.build_shop(self.character)[0]
        self.assertEqual(item["level"], 2)
        self.assertEqual(item["cost"], 50)  # 30 + 2×10
        self.assertFalse(item["maxed"])

    def test_maxed_at_max_level(self):
        # 최대 레벨에 도달하면 maxed=True
        CharacterUpgrade.objects.create(character=self.character, upgrade=self.hp, level=3)  # max_level=3
        item = services.build_shop(self.character)[0]
        self.assertTrue(item["maxed"])

    def test_not_affordable_when_gold_low(self):
        # 골드가 비용보다 적으면 affordable=False
        self.character.permanent_gold = 10
        self.character.save()
        item = services.build_shop(self.character)[0]
        self.assertFalse(item["affordable"])  # 10 < 30
