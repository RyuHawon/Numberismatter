from django.contrib import admin
from .models import Character, Skill, Upgrade, CharacterUpgrade, Enemy


admin.site.register(Character)
admin.site.register(Skill)
admin.site.register(Upgrade)
admin.site.register(CharacterUpgrade)
admin.site.register(Enemy)