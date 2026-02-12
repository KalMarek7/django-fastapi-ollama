from django.contrib import admin

from .models import Task


# Register your models here.
# 1. Create a custom Admin class for Task
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # Columns to show in the list view
    list_display = ("task_id", "status", "created_at", "updated_at")

    # Add filters on the right sidebar
    list_filter = ("status", "created_at")

    # Make the task_id searchable
    search_fields = ("task_id",)

    # Optional: Make it read-only if you don't want to accidentally edit IDs
    readonly_fields = ("task_id", "created_at", "updated_at")
