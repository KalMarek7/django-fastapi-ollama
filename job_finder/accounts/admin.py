from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Add 'bio' to the fieldsets so it shows up in the admin edit page
    list_display = ["email", "username", "is_staff", "is_superuser"]
