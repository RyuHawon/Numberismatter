from django.db import migrations


UPGRADES = [
    ("최대 HP", "최대 체력 +10", 30, "max_hp", 5, 10),
    ("주사위 상한", "주사위 최댓값 +1", 50, "dice_max", 3, 1),
    ("주사위 하한", "주사위 최솟값 +1", 100, "dice_min", 2, 1),
    ("크리티컬", "크리티컬 확률 +10%", 30, "crit", 3, 0.1),
    ("골드 보너스", "처치 골드 +2", 25, "gold_bonus", 5, 2),
]


def seed(apps, schema_editor):
    Upgrade = apps.get_model("game", "Upgrade")
    for name, desc, cost, effect, max_level, epl in UPGRADES:
        Upgrade.objects.update_or_create(
            name=name,
            defaults={
                "description": desc, "cost": cost, "effect": effect,
                "max_level": max_level, "effect_per_level": epl,
            }
        )


def unseed(apps, schema_editor):
    Upgrade = apps.get_model("game", "Upgrade")
    Upgrade.objects.filter(name__in=[u[0] for u in UPGRADES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0013_character_crit_chance"),
    ]
    operations = [
        migrations.RunPython(seed, unseed),
    ]