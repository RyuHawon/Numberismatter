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


class PurchaseUpgradeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@test.com", nickname="유저", password="pw-long-1234")
        self.character = self.user.character
        Upgrade.objects.all().delete()
        # 최대 HP 업그레이드: 비용 30, 레벨당 +10, 최대 2레벨
        self.hp = Upgrade.objects.create(
            name="최대 HP", description="", cost=30, effect="max_hp", max_level=2, effect_per_level=10
        )

    def test_purchase_deducts_gold_levels_up_and_applies_effect(self):
        # 구매 성공: 골드 차감 + 레벨업 + 효과가 캐릭터 스탯에 반영
        self.character.permanent_gold = 100
        self.character.max_hp = 50
        self.character.save()
        ok = services.purchase_upgrade(self.character, self.hp)
        self.assertTrue(ok)
        self.character.refresh_from_db()
        self.assertEqual(self.character.permanent_gold, 70)  # 100 - 30
        self.assertEqual(self.character.max_hp, 60)  # 50 + 10
        self.assertEqual(self.character.upgrades.get(upgrade=self.hp).level, 1)

    def test_second_purchase_costs_more(self):
        # 두 번째 구매는 비용이 레벨만큼 오른다 (30 → 40)
        self.character.permanent_gold = 100
        self.character.save()
        services.purchase_upgrade(self.character, self.hp)  # Lv0→1, 30골드
        services.purchase_upgrade(self.character, self.hp)  # Lv1→2, 40골드
        self.character.refresh_from_db()
        self.assertEqual(self.character.permanent_gold, 30)  # 100 - 30 - 40
        self.assertEqual(self.character.upgrades.get(upgrade=self.hp).level, 2)

    def test_purchase_fails_when_gold_insufficient(self):
        # 골드 부족이면 실패: 차감·효과·레벨 모두 변화 없음
        self.character.permanent_gold = 10  # < 30
        self.character.max_hp = 50
        self.character.save()
        ok = services.purchase_upgrade(self.character, self.hp)
        self.assertFalse(ok)
        self.character.refresh_from_db()
        self.assertEqual(self.character.permanent_gold, 10)
        self.assertEqual(self.character.max_hp, 50)
        self.assertFalse(self.character.upgrades.filter(upgrade=self.hp).exists())

    def test_purchase_fails_at_max_level(self):
        # 최대 레벨이면 골드가 많아도 구매 불가
        CharacterUpgrade.objects.create(character=self.character, upgrade=self.hp, level=2)  # max_level=2
        self.character.permanent_gold = 1000
        self.character.save()
        ok = services.purchase_upgrade(self.character, self.hp)
        self.assertFalse(ok)
        self.character.refresh_from_db()
        self.assertEqual(self.character.permanent_gold, 1000)  # 차감 안 됨
        self.assertEqual(self.character.upgrades.get(upgrade=self.hp).level, 2)

    def test_each_effect_routes_to_correct_stat(self):
        # effect 종류별로 올바른 캐릭터 스탯에 반영되는지 (max_hp는 위에서 검증)
        self.character.permanent_gold = 1000
        self.character.dice_max = 6
        self.character.dice_min = 1
        self.character.gold_bonus = 0
        self.character.crit_chance = 0.0
        self.character.save()
        specs = [("dice_max", 1), ("dice_min", 1), ("gold_bonus", 2), ("crit", 0.1)]
        for effect, epl in specs:
            upg = Upgrade.objects.create(
                name=effect, description="", cost=10, effect=effect, max_level=1, effect_per_level=epl
            )
            services.purchase_upgrade(self.character, upg)
        self.character.refresh_from_db()
        self.assertEqual(self.character.dice_max, 7)
        self.assertEqual(self.character.dice_min, 2)
        self.assertEqual(self.character.gold_bonus, 2)
        self.assertAlmostEqual(self.character.crit_chance, 0.1)
