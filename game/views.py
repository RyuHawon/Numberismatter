import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Enemy, Skill

DEFEND_CHANCE = 0.3
DIE_KINDS = ("attack", "defense", "heal")


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
        "max_hp": character.max_hp,
        "pending_gold": 0,
        "skills": {},
    }
    return redirect("game:battle")


@login_required
@require_POST
def abandon_run(request):
    request.session.pop("run", None)
    return redirect("game:home")


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
            "image": enemy.image,
            "armor": 0,
        }
        run["enemy"]["intent"] = create_enemy_intent(run["enemy"])
        request.session.modified = True

    context = {"run": run}
    if run.get("phase") == "act_clear":
        context["has_next_act"] = Enemy.objects.filter(act=run["current_act"] + 1).exists()
    if run.get("phase") == "won":
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

    return render(request, "game/battle.html", context)


@login_required
@require_POST
def battle_roll(request):
    run = request.session.get("run")
    if not run or run.get("phase") != "roll" or "enemy" not in run:
        return redirect("game:battle")
    
    character = request.user.character
    run["my_dice"] = {
        kind: random.randint(character.dice_min, character.dice_max)
        for kind in DIE_KINDS
    }
    run["phase"] = "action"
    request.session.modified = True
    return redirect("game:battle")



@login_required
@require_POST
def battle_action(request):
    run = request.session.get("run")
    if not run or run.get("phase") != "action" or "my_dice" not in run:
        return redirect("game:battle")
    
    choice = request.POST.get("choice")
    if choice not in DIE_KINDS:
        return redirect("game:battle")
    
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

        crit_level = run["skills"].get("critical", 0)
        if crit_level > 0:
            crit_skill = Skill.objects.filter(code="critical").first()
            if crit_skill and random.random() < crit_level * crit_skill.effect_per_level:
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
    return redirect("game:battle")


@login_required
@require_POST
def choose_skill(request):
    run = request.session.get("run")
    if not run or run.get("phase") != "won":
        return redirect("game:battle")

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
    return redirect("game:battle")


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
    return redirect("game:battle")
