import random

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import services
from .models import Enemy, Skill, Upgrade

DEFEND_CHANCE = 0.3
DIE_KINDS = ("attack", "defense", "heal")


def home(request):
    return render(request, "game/home.html")


@login_required
def shop(request):
    character = request.user.character
    context = {
        "shop": services.build_shop(character),
        "gold": character.permanent_gold,
    }
    return render(request, "game/shop.html", context)


@login_required
@require_POST
def buy_upgrade(request):
    upgrade = get_object_or_404(Upgrade, pk=request.POST.get("upgrade_id"))
    services.purchase_upgrade(request.user.character, upgrade)
    return redirect("game:shop")


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
        "max_hp": character.max_hp,
        "pending_gold": 0,
        "skills": {},
        "skill_uses": {},
    }
    return redirect("game:battle")


@login_required
@require_POST
def abandon_run(request):
    request.session.pop("run", None)
    return redirect("game:home")


def roll_player_dice(character):
    return {
        kind: random.randint(character.dice_min, character.dice_max)
        for kind in DIE_KINDS
    }


def create_enemy_intent(enemy):
    if random.random() < DEFEND_CHANCE:
        return {
            "type": "defense",
            "armor_gain": random.randint(enemy["dice_min"], enemy["dice_max"]),
        }
    return {
        "type": "attack",
        "damage": random.randint(enemy["dice_min"], enemy["dice_max"]),
        "hits": 1,
    }


def _ensure_enemy(run):
    if "enemy" in run:
        return False

    candidates = list(Enemy.objects.filter(act=run["current_act"], stage=run["current_stage"]))
    enemy = random.choices(candidates, weights=[c.weight for c in candidates])[0]
    run["enemy"] = {
        "name": enemy.name,
        "hp": enemy.hp,
        "max_hp": enemy.hp,
        "dice_min": enemy.dice_min,
        "dice_max": enemy.dice_max,
        "is_boss": enemy.is_boss,
        "gold_dice_min": enemy.gold_dice_min,
        "gold_dice_max": enemy.gold_dice_max,
        "image": enemy.image,
        "armor": 0,
    }
    run["enemy"]["intent"] = create_enemy_intent(run["enemy"])
    run["skill_uses"]["reroll"] = run["skills"].get("reroll", 0)
    return True


def _battle_context(run):
    context = {"run": run}
    phase = run.get("phase")
    if phase == "act_clear":
        context["has_next_act"] = Enemy.objects.filter(act=run["current_act"] + 1).exists()
    if phase == "won":
        options = []
        for skill in Skill.objects.all():
            level = run["skills"].get(skill.code, 0)
            if level < skill.max_level:
                options.append(
                    {
                        "code": skill.code,
                        "name": skill.name,
                        "current_level": level,
                        "next_level": level + 1,
                    }
                )
        context["skill_options"] = options
    return context


def _battle_response(request, run):
    if request.headers.get("HX-Request"):
        if not run:
            response = HttpResponse()
            response["HX-Redirect"] = reverse("game:home")
            return response
        _ensure_enemy(run)
        return render(request, "game/_battle_body.html", _battle_context(run))
    return redirect("game:battle")


@login_required
def battle(request):
    run = request.session.get("run")
    if not run:
        return redirect("game:home")
    if _ensure_enemy(run):
        request.session.modified = True
    run = request.session.get("run")

    template = "game/_battle_body.html" if request.headers.get("HX-Request") else "game/battle.html"
    return render(request, template, _battle_context(run))


@login_required
@require_POST
def battle_roll(request):
    run = request.session.get("run")
    if not run or run.get("phase") != "roll" or "enemy" not in run:
        return _battle_response(request, run)

    character = request.user.character
    run["my_dice"] = roll_player_dice(character)
    run["phase"] = "action"
    request.session.modified = True
    return _battle_response(request, run)


@login_required
@require_POST
def battle_reroll(request):
    run = request.session.get("run")
    if not run or run.get("phase") != "action":
        return _battle_response(request, run)
    
    uses_left = run["skill_uses"].get("reroll", 0)
    if uses_left <= 0:
        return _battle_response(request, run)
    
    run["my_dice"] = roll_player_dice(request.user.character)
    run["skill_uses"]["reroll"] = uses_left -1
    request.session.modified = True
    return _battle_response(request, run)


@login_required
@require_POST
def battle_action(request):
    run = request.session.get("run")
    if not run or run.get("phase") != "action" or "my_dice" not in run:
        return _battle_response(request, run)

    choice = request.POST.get("choice")
    if choice not in DIE_KINDS:
        return _battle_response(request, run)

    enemy = run["enemy"]
    intent = enemy["intent"]
    value = run["my_dice"][choice]

    block = 0
    damage_dealt = 0
    heal_done = 0
    damage_taken = 0
    is_crit = False

    if choice == "attack":
        attack_value = value

        if random.random() < request.user.character.crit_chance:
            attack_value *= 2
            is_crit = True

        after_armor = max(attack_value - enemy["armor"], 0)
        enemy["armor"] = max(enemy["armor"] - attack_value, 0)
        damage_dealt = min(after_armor, enemy["hp"])
        enemy["hp"] -= damage_dealt

    elif choice == "defense":
        block = value

    else:
        heal_done = min(value, run["max_hp"] - run["hp"])
        run["hp"] += heal_done

    if enemy["hp"] > 0:
        enemy["armor"] = 0
        if intent["type"] == "attack":
            remaining_block = block
            for _ in range(intent["hits"]):
                absorbed = min(intent["damage"], remaining_block)
                remaining_block -= absorbed
                damage_taken += intent["damage"] - absorbed

            run["hp"] = max(run["hp"] - damage_taken, 0)

        else:
            enemy["armor"] = intent["armor_gain"]

    run["last_result"] = {
        "choice": choice,
        "value": value,
        "is_crit": is_crit,
        "damage_dealt": damage_dealt,
        "heal_done": heal_done,
        "damage_taken": damage_taken,
        "intent": intent,
    }

    if enemy["hp"] <= 0:
        character = request.user.character
        gold = random.randint(enemy["gold_dice_min"], enemy["gold_dice_max"]) + character.gold_bonus
        run["pending_gold"] += gold
        run["gold_gained"] = gold
        run["phase"] = "act_clear" if enemy["is_boss"] else "won"
        enemy.pop("intent", None)
    elif run["hp"] <= 0:
        run["phase"] = "dead"
        enemy.pop("intent", None)
    else:
        enemy["intent"] = create_enemy_intent(enemy)
        run["phase"] = "roll"

    run.pop("my_dice", None)
    request.session.modified = True
    return _battle_response(request, run)


@login_required
@require_POST
def choose_skill(request):
    run = request.session.get("run")
    if not run or run.get("phase") != "won":
        return _battle_response(request, run)

    code = request.POST.get("skill")
    if code and code != "skip":
        skill = Skill.objects.filter(code=code).first()
        if skill:
            current = run["skills"].get(code, 0)
            if current < skill.max_level:
                run["skills"][code] = current + 1

    run["current_stage"] += 1
    run.pop("enemy", None)
    run.pop("last_result", None)
    run.pop("gold_gained", None)
    run["phase"] = "roll"
    request.session.modified = True
    return _battle_response(request, run)


@login_required
@require_POST
def return_run(request):
    run = request.session.get("run")
    if not run or run.get("phase") != "act_clear":
        return redirect("game:battle")
    character = request.user.character
    character.permanent_gold += run["pending_gold"]
    character.save()
    request.session.pop("run", None)
    return redirect("game:home")


@login_required
@require_POST
def challenge_next_act(request):
    run = request.session.get("run")
    if not run or run.get("phase") != "act_clear":
        return redirect("game:battle")
    next_act = run["current_act"] + 1
    if not Enemy.objects.filter(act=next_act).exists():
        return redirect("game:battle")
    run["current_act"] = next_act
    run["current_stage"] = 1
    run["hp"] = run["max_hp"]
    run.pop("enemy", None)
    run.pop("last_result", None)
    run.pop("gold_gained", None)
    run["phase"] = "roll"
    request.session.modified = True
    return _battle_response(request, run)
