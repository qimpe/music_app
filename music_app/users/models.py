from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    country = models.CharField(max_length=70, default="Russian Federation")
    is_label = models.BooleanField(default=False)

    def __str__(self):
        return self.username
