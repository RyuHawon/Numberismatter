from django.db import migrations


def rebalance(apps, schema_editor):
    Enemy = apps.get_model("game", "Enemy")
    Enemy.objects.filter(act__in=[1, 2, 3]).delete()
    Enemy.objects.bulk_create([
        # Act 1 (목표: ~59% 클리어율)
        Enemy(name="쥐",     hp=8,  stage=1, dice_min=1, dice_max=3, act=1, is_boss=False, image="game/enemies/mouse.png"),
        Enemy(name="벌",     hp=12, stage=2, dice_min=2, dice_max=4, act=1, is_boss=False, image="game/enemies/bee.png"),
        Enemy(name="슬라임",  hp=18, stage=3, dice_min=2, dice_max=5, act=1, is_boss=False, image="game/enemies/slime.png"),
        Enemy(name="해골",   hp=22, stage=4, dice_min=3, dice_max=6, act=1, is_boss=True,  image="game/enemies/skeleton.png"),
        Enemy(name="데빌",   hp=25, stage=4, dice_min=3, dice_max=7, act=1, is_boss=True,  image="game/enemies/devil.png"),

        # Act 2 (목표: ~64% 클리어율, crit=3 보유 가정, '도전' 후 완전 회복 가정)
        Enemy(name="쥐2",    hp=9,  stage=1, dice_min=1, dice_max=3, act=2, is_boss=False, image="game/enemies/mouse.png"),
        Enemy(name="벌2",    hp=13, stage=2, dice_min=2, dice_max=4, act=2, is_boss=False, image="game/enemies/bee.png"),
        Enemy(name="슬라임2", hp=19, stage=3, dice_min=2, dice_max=5, act=2, is_boss=False, image="game/enemies/slime.png"),
        Enemy(name="해골2",  hp=22, stage=4, dice_min=3, dice_max=6, act=2, is_boss=True,  image="game/enemies/skeleton.png"),
        Enemy(name="데빌2",  hp=25, stage=4, dice_min=3, dice_max=7, act=2, is_boss=True,  image="game/enemies/devil.png"),

        # Act 3 (목표: ~25% 클리어율, 최종 보스 구간)
        Enemy(name="쥐3",    hp=10, stage=1, dice_min=1, dice_max=3, act=3, is_boss=False, image="game/enemies/mouse.png"),
        Enemy(name="벌3",    hp=15, stage=2, dice_min=2, dice_max=4, act=3, is_boss=False, image="game/enemies/bee.png"),
        Enemy(name="슬라임3", hp=22, stage=3, dice_min=2, dice_max=5, act=3, is_boss=False, image="game/enemies/slime.png"),
        Enemy(name="해골3",  hp=26, stage=4, dice_min=3, dice_max=7, act=3, is_boss=True,  image="game/enemies/skeleton.png"),
        Enemy(name="데빌3",  hp=30, stage=4, dice_min=3, dice_max=8, act=3, is_boss=True,  image="game/enemies/devil.png"),
    ])


def reverse_rebalance(apps, schema_editor):
    Enemy = apps.get_model("game", "Enemy")
    Enemy.objects.filter(act__in=[1, 2, 3]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0009_seed_act2_act3_enemies"),
    ]

    operations = [
        migrations.RunPython(rebalance, reverse_rebalance),
    ]
