import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import JobListing, Portal, SystemInstruction


# 1. Register SystemInstruction as a ModelAdmin
@admin.register(SystemInstruction)
class SystemInstructionAdmin(admin.ModelAdmin):
    # Columns to show in the list view
    list_display = ("pk", "name")


# 2. Register others normally (or create classes for them too)
admin.site.register(Portal)


@admin.action(description="Export selected jobs to CSV")
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="jobs.csv"'

    writer = csv.writer(response)
    # Headers
    writer.writerow([i for i in modeladmin.list_display])

    for job in queryset:
        writer.writerow([getattr(job, i) for i in modeladmin.list_display])

    return response


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    # Columns to show in the list view,
    list_display = (
        "pk",
        "title",
        "company",
        "years_of_experience",
        "salary",
        "portal",
        "expiry_date",
        "posted_at",
        "url",
    )
    actions = [export_as_csv]
