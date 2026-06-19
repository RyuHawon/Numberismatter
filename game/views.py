import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Enemy


def home(request):
    return render(request, "game/home.html")


@login_required
@require_POST
def start_run(request):
    if "run" in request.session:
        return redirect("game:home")
    character = request.user.character
    request.session["run"] = {
        "phase": "roll",
        "current_act": 1,
        "current_stage": 1,
        "hp": character.max_hp,
        "pending_gold": 0,
        "skills": {},
    }
    return redirect("game:home")


@login_required
@require_POST
def abandon_run(request):
    request.session.pop("run", None)
    return redirect("game:home")


@login_required
def battle(request):
    run = request.session.get("run")
    if not run:
        return redirect("game:home")

    if "enemy" not in run:
        candidates = Enemy.objects.filter(act=run["current_act"], stage=run["current_stage"])
        enemy = random.choice(list(candidates))
        run["enemy"] = {
            "name": enemy.name,
            "hp": enemy.hp,
            "max_hp": enemy.hp,
            "dice_min": enemy.dice_min,
            "dice_max": enemy.dice_max,
            "is_boss": enemy.is_boss,
        }
        request.session.modified = True

    return render(request, "game/battle.html", {"run": run})
