from .models import Upgrade

COST_STEP = 10


def upgrade_cost(upgrade, level):
    return upgrade.cost + level * COST_STEP


def build_shop(character):
    owned = {cu.upgrade_id: cu.level for cu in character.upgrades.all()}
    shop = []
    for upg in Upgrade.objects.all():
        level = owned.get(upg.id, 0)
        cost = upgrade_cost(upg, level)
        shop.append(
            {
                "id": upg.id,
                "name": upg.name,
                "description": upg.description,
                "level": level,
                "max_level": upg.max_level,
                "maxed": level >= upg.max_level,
                "cost": cost,
                "affordable": character.permanent_gold >= cost,
            }
        )
    return shop
