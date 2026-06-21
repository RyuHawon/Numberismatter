from django.db import migrations


def seed_act2_act3(apps, schema_editor):
    Enemy = apps.get_model("game", "Enemy")
    Enemy.objects.filter(act__in=[2, 3]).delete()
    Enemy.objects.bulk_create(
        [
            # Act 2 일반몹 (stage 1~3)
            Enemy(name="쥐2",   hp=15, stage=1, dice_min=2, dice_max=5,  act=2, is_boss=False, image="game/enemies/mouse.png"),
            Enemy(name="벌2",   hp=28, stage=2, dice_min=3, dice_max=7,  act=2, is_boss=False, image="game/enemies/bee.png"),
            Enemy(name="슬라임2", hp=45, stage=3, dice_min=4, dice_max=8,  act=2, is_boss=False, image="game/enemies/slime.png"),
            # Act 2 보스 (stage 4, 둘 중 랜덤)
            Enemy(name="해골2", hp=70,  stage=4, dice_min=7, dice_max=12, act=2, is_boss=True,  image="game/enemies/skeleton.png"),
            Enemy(name="데빌2", hp=90,  stage=4, dice_min=8, dice_max=14, act=2, is_boss=True,  image="game/enemies/devil.png"),

            # Act 3 일반몹 (stage 1~3)
            Enemy(name="쥐3",   hp=25, stage=1, dice_min=3, dice_max=7,  act=3, is_boss=False, image="game/enemies/mouse.png"),
            Enemy(name="벌3",   hp=45, stage=2, dice_min=4, dice_max=9,  act=3, is_boss=False, image="game/enemies/bee.png"),
            Enemy(name="슬라임3", hp=70, stage=3, dice_min=5, dice_max=10, act=3, is_boss=False, image="game/enemies/slime.png"),
            # Act 3 보스 (stage 4, 둘 중 랜덤)
            Enemy(name="해골3", hp=110, stage=4, dice_min=9,  dice_max=15, act=3, is_boss=True,  image="game/enemies/skeleton.png"),
            Enemy(name="데빌3", hp=140, stage=4, dice_min=10, dice_max=17, act=3, is_boss=True,  image="game/enemies/devil.png"),
        ]
    )


def reverse_seed(apps, schema_editor):
    Enemy = apps.get_model("game", "Enemy")
    Enemy.objects.filter(act__in=[2, 3]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0008_alter_character_max_hp"),
    ]

    operations = [
        migrations.RunPython(seed_act2_act3, reverse_seed),
    ]
