from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = None
    email = models.EmailField(max_length=255, unique=True)
    nickname = models.CharField(max_length=30, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.nickname