from django.contrib import admin

from .models import JobListing, Portal

# Register your models here.
admin.site.register([JobListing, Portal])
