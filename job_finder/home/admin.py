from django.contrib import admin

from .models import JobListing, Portal, SystemInstruction


# 1. Register SystemInstruction as a ModelAdmin
@admin.register(SystemInstruction)
class SystemInstructionAdmin(admin.ModelAdmin):
    # Columns to show in the list view
    list_display = ("pk", "name")


# 2. Register others normally (or create classes for them too)
admin.site.register(Portal)


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    # Columns to show in the list view
    list_display = ("company", "portal", "title")
