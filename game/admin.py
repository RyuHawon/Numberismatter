from django.contrib import admin

from .models import Character, CharacterUpgrade, Enemy, Skill, Upgrade

admin.site.register(Character)
admin.site.register(Skill)
admin.site.register(Upgrade)
admin.site.register(CharacterUpgrade)
admin.site.register(Enemy)
