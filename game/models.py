from django.conf import settings
from django.db import models


class Character(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="character",
    )
    max_hp = models.IntegerField(default=50)
    dice_min = models.IntegerField(default=1)
    dice_max = models.IntegerField(default=6)
    permanent_gold = models.IntegerField(default=0)
    gold_bonus = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "characters"

    def __str__(self):
        return f"{self.user.nickname}'s character"


class Skill(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    max_level = models.IntegerField(default=1)
    effect_per_level = models.FloatField()

    class Meta:
        db_table = "skills"

    def __str__(self):
        return self.name


class Upgrade(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    cost = models.IntegerField()
    effect = models.CharField(max_length=100)
    max_level = models.IntegerField(default=1)
    effect_per_level = models.FloatField()

    class Meta:
        db_table = "upgrades"

    def __str__(self):
        return self.name


class CharacterUpgrade(models.Model):
    character = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name="upgrades",
    )
    upgrade = models.ForeignKey(
        Upgrade,
        on_delete=models.PROTECT,
        related_name="character_upgrades",
    )
    level = models.IntegerField(default=1)

    class Meta:
        db_table = "character_upgrades"
        constraints = [
            models.UniqueConstraint(
                fields=["character", "upgrade"],
                name="unique_character_upgrade",
            )
        ]

    def __str__(self):
        return f"{self.character} - {self.upgrade.name} Lv.{self.level}"


class Enemy(models.Model):
    name = models.CharField(max_length=100)
    image = models.CharField(max_length=100, blank=True, default="")
    hp = models.IntegerField()
    dice_min = models.IntegerField()
    dice_max = models.IntegerField()
    act = models.IntegerField()
    stage = models.IntegerField()
    is_boss = models.BooleanField(default=False)
    gold_dice_min = models.IntegerField(default=1)
    gold_dice_max = models.IntegerField(default=20)

    class Meta:
        db_table = "enemies"
        indexes = [
            models.Index(fields=["act"], name="idx_enemy_act"),
        ]

    def __str__(self):
        return f"[Act{self.act}] {self.name}"
