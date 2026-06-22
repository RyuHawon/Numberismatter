from .models import 


COST_STEP = 10


def upgrade_cost(upgrade, level):
    return upgrade.cost + level * COST_STEP