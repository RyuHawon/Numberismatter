from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST


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
