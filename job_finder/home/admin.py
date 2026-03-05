from django.contrib import admin

from .models import JobListing, Portal

# 2. Register others normally (or create classes for them too)
admin.site.register(Portal)


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    # Columns to show in the list view
    list_display = ("company", "portal", "title")
