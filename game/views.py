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
            "gold_dice_min": enemy.gold_dice_min,
            "gold_dice_max": enemy.gold_dice_max,
        }
        request.session.modified = True

    return render(request, "game/battle.html", {"run": run})


@login_required
@require_POST
def battle_roll(request):
    run = request.session.get("run")
    if not run or run.get("phase") != "roll" or "enemy" not in run:
        return redirect("game:battle")
    character = request.user.character
    run["my_roll"] = random.randint(character.dice_min, character.dice_max)
    run["phase"] = "action"
    request.session.modified = True
    return redirect("game:battle")


@login_required
@require_POST
def battle_action(request):
    run = request.session.get("run")
    if not run or run.get("phase") != "action":
        return redirect("game:battle")
    mode = request.POST.get("mode")
    if mode not in ("attack", "defend"):
        return redirect("game:battle")

    enemy = run["enemy"]
    my_roll = run["my_roll"]
    enemy_roll = None
    damage_taken = 0

    if mode == "attack":
        enemy["hp"] = max(enemy["hp"] - my_roll, 0)
        if enemy["hp"] > 0:
            enemy_roll = random.randint(enemy["dice_min"], enemy["dice_max"])
            damage_taken = enemy_roll
            run["hp"] = max(run["hp"] - enemy_roll, 0)
    else:
        enemy_roll = random.randint(enemy["dice_min"], enemy["dice_max"])

    run["last_result"] = {
        "mode": mode,
        "my_roll": my_roll,
        "enemy_roll": enemy_roll,
        "damage_taken": damage_taken,
    }

    if enemy["hp"] <= 0:
        character = request.user.character
        gold = random.randint(enemy["gold_dice_min"], enemy["gold_dice_max"]) + character.gold_bonus
        run["pending_gold"] += gold
        run["gold_gained"] = gold
        run["phase"] = "act_clear" if enemy["is_boss"] else "won"
    elif run["hp"] <= 0:
        run["phase"] = "dead"
    else:
        run["phase"] = "roll"

    run.pop("my_roll", None)
    request.session.modified = True
    return redirect("game:battle")
