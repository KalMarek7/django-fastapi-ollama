from django.db import models


# Create your models here.
class JobListing(models.Model):
    title = models.CharField(null=True, blank=True, max_length=200)
    text_content = models.TextField()
    expiry_date = models.DateField(
        null=True,
        blank=True,
    )
    url = models.URLField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    company = models.CharField(null=True, blank=True, max_length=200)
    years_of_experience = models.IntegerField(null=True, blank=True, verbose_name="YoE")
    salary = models.CharField(null=True, blank=True, max_length=200)
    portal = models.ForeignKey("Portal", on_delete=models.CASCADE)
    posted_at = models.DateField(null=True, blank=True)


class Portal(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SystemInstruction(models.Model):
    name = models.CharField(max_length=100)
    instruction = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
