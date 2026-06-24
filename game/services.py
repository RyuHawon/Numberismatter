from .models import CharacterUpgrade, Upgrade

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


def _apply_effect(character, upgrade):
    amount = upgrade.effect_per_level
    if upgrade.effect == "max_hp":
        character.max_hp += int(amount)
    elif upgrade.effect == "dice_max":
        character.dice_max += int(amount)
    elif upgrade.effect == "dice_min":
        character.dice_min += int(amount)
    elif upgrade.effect == "gold_bonus":
        character.gold_bonus += int(amount)
    elif upgrade.effect == "crit":
        character.crit_chance += amount


def purchase_upgrade(character, upgrade):
    cu = character.upgrades.filter(upgrade=upgrade).first()
    level = cu.level if cu else 0
    if level >= upgrade.max_level:
        return False
    cost = upgrade_cost(upgrade, level)
    if character.permanent_gold < cost:
        return False

    character.permanent_gold -= cost
    _apply_effect(character, upgrade)
    character.save()
    if cu:
        cu.level += 1
        cu.save()
    else:
        CharacterUpgrade.objects.create(character=character, upgrade=upgrade)
    return True
