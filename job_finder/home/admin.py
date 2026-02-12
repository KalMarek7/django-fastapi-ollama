from django.contrib import admin

from .models import JobListing, Portal

# 2. Register others normally (or create classes for them too)
admin.site.register(JobListing)
admin.site.register(Portal)
