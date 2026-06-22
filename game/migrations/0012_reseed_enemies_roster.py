from django.db import migrations

# (이름, 이미지, HP, 주사위min, 주사위max, act, stage, 보스, 골드min, 골드max, 가중치)
ENEMIES = [
    # Act1 — 자연
    ("길 잃은 쥐", "field_rat", 12, 2, 4, 1, 1, False, 8, 14, 485),
    ("화난 경비벌", "stinger_bee", 14, 2, 5, 1, 1, False, 8, 14, 485),
    ("전설의 바퀴벌레", "roach", 16, 1, 3, 1, 1, False, 30, 50, 30),  # 3% 등장, 골드 多
    ("거미 군단", "spider_legion", 16, 3, 5, 1, 2, False, 12, 20, 100),
    ("브루드마더", "broodmother", 20, 3, 6, 1, 3, False, 14, 22, 100),
    ("초코베로스", "chocoberus", 30, 4, 7, 1, 4, True, 25, 40, 100),
    # Act2 — 던전
    ("젤리 슬라임", "slime", 22, 3, 5, 2, 1, False, 18, 28, 100),
    ("뒹굴맨더", "salamander", 24, 3, 6, 2, 1, False, 18, 28, 100),
    ("점액 군주", "ooze_king", 26, 4, 6, 2, 2, False, 20, 30, 100),
    ("롤러 스켈레톤", "skeleton_skater", 24, 3, 6, 2, 2, False, 20, 30, 100),
    ("냥홀더", "hydra_cat", 28, 4, 7, 2, 3, False, 22, 34, 100),
    ("붉은 포식귀", "devourer", 30, 4, 7, 2, 3, False, 22, 34, 100),
    ("백족룡", "centipede_king", 42, 5, 8, 2, 4, True, 40, 60, 100),
    # Act3 — 지하
    ("임프", "imp", 32, 4, 7, 3, 1, False, 35, 50, 100),
    ("핏빛 손아귀", "gazer", 38, 5, 8, 3, 2, False, 38, 55, 100),
    ("백면거미", "wraith_spider", 42, 5, 8, 3, 3, False, 40, 58, 100),
    ("심연의 심장", "abyss_heart", 44, 5, 9, 3, 3, False, 40, 58, 100),
    ("거짓 우상", "false_idol", 60, 6, 10, 3, 4, True, 60, 90, 100),
]


def reseed(apps, schema_editor):
    Enemy = apps.get_model("game", "Enemy")
    Enemy.objects.all().delete()
    Enemy.objects.bulk_create(
        [
            Enemy(
                name=name,
                image=f"game/enemies/{img}.png",
                hp=hp,
                dice_min=dmin,
                dice_max=dmax,
                act=act,
                stage=stage,
                is_boss=boss,
                gold_dice_min=gmin,
                gold_dice_max=gmax,
                weight=weight,
            )
            for (name, img, hp, dmin, dmax, act, stage, boss, gmin, gmax, weight) in ENEMIES
        ]
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0011_enemy_weight"),
    ]
    operations = [
        migrations.RunPython(reseed, noop),
    ]
