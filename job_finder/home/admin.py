import csv
import json

from django.contrib import admin, messages
from django.db.models import F, Value
from django.db.models.functions import Replace
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import JobListing, JobMatch, Portal, Resume, SystemInstruction


@admin.register(SystemInstruction)
class SystemInstructionAdmin(admin.ModelAdmin):
    list_display = ("pk", "name")


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


@admin.action(description="Replace api url with frontend url")
def replace_api_url(modeladmin, request, queryset):
    # 1. Filter the selection to ONLY those where the portal is justjoinit
    # We use __iexact for a case-insensitive match
    target_queryset = queryset.filter(portal__name__iexact="JustJoinIT")

    count = target_queryset.count()

    if count == 0:
        modeladmin.message_user(
            request,
            "No JustJoinIT listings were found in your selection.",
            messages.WARNING,
        )
        return

    # 2. Perform the bulk update on the filtered results
    target_queryset.update(
        # Note: If the 'url' field is on the JobListing model, use job_listing__url
        url=Replace(F("url"), Value("api/candidate-api/offers"), Value("job-offer"))
    )

    modeladmin.message_user(
        request, f"Successfully updated {count} JustJoinIT URLs.", messages.SUCCESS
    )


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
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
        "created_at",
        "updated_at",
    )
    actions = [export_as_csv, replace_api_url]


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    # Columns to show in the list view
    list_display = ("pk", "name")


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display = ("match_percentage_display", "job_title", "created_at")
    search_fields = ("job_listing__title",)

    # This solves the "N+1" problem (makes the admin load much faster)
    list_select_related = ("job_listing",)

    readonly_fields = (
        "job_title",
        "job_listing",
        "match_url",
        "pretty_llm_output",
    )
    exclude = ("llm_output",)

    @admin.display(description="Job Title", ordering="job_listing__title")
    def job_title(self, obj):
        return obj.job_listing.title

    @admin.display(description="Match %", ordering="json_match_pct")
    def match_percentage_display(self, obj):
        # Extract from the JSON field
        # Using .get() prevents crashes if the key is missing
        val = obj.llm_output.get("match_percentage", "N/A")
        return f"{val}%" if val != "N/A" else val

    def match_url(self, obj):
        url = obj.job_listing.url
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    def pretty_llm_output(self, obj):
        # Convert the dict to a formatted string with 4-space indentation
        content = json.dumps(obj.llm_output, indent=4, ensure_ascii=False)
        return mark_safe(
            f'<pre style="padding: 10px; border-radius: 5px; white-space: pre-wrap; word-break: break-word; max-width: 800px; border: 1px solid #ccc;">{content}</pre>'
        )

    # Optional: If you want to sort by the percentage inside the JSON
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # This creates a "virtual" field the database can sort on
        return qs.annotate(json_match_pct=F("llm_output__match_percentage"))
