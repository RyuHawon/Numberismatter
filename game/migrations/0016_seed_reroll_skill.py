from django.db import migrations


def seed_reroll_skill(apps, schema_editor):
    Skill = apps.get_model("game", "Skill")
    Skill.objects.update_or_create(
        code="reroll",
        defaults={
            "name": "재굴림",
            "description": "해당 런 동안 전투 당 한번씩 공격,수비,회복 주사위를 모두 다시 굴립니다. 레벨당 사용 횟수 +1",
            "max_level": 3,
            "effect_per_level": 1,
        }
    )


def remove_reroll_skill(apps, schema_editor):
    Skill = apps.get_model("game", "Skill")
    Skill.objects.filter(code="reroll").delete()


class Migration(migrations.Migration):

    dependencies = [('game', '0015_remove_critical_skill')]

    operations = [migrations.RunPython(seed_reroll_skill, remove_reroll_skill),]
