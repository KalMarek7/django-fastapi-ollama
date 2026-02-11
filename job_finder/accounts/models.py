# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    # Add any extra fields you want here
    email = models.EmailField(unique=True)

    # Tell Django to use email for login instead of username
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # Email is already required by USERNAME_FIELD

    def __str__(self):
        return self.email
