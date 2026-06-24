from django.db import migrations


def remove_crit_skill(apps, schema_editor):
    Skill = apps.get_model("game", "Skill")
    Skill.objects.filter(code="critical").delete()


class Migration(migrations.Migration):
    dependencies = [('game', '0014_seed_upgrades')]

    operations = [migrations.RunPython(remove_crit_skill, migrations.RunPython.noop)]
