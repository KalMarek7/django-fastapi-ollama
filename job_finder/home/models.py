from django.db import models


# Create your models here.
class JobListing(models.Model):
    title = models.CharField(max_length=100)
    text_content = models.TextField()
    expiry_date = models.DateField()
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    company = models.CharField(max_length=100)
    score = models.FloatField()
    portal = models.ForeignKey("Portal", on_delete=models.CASCADE)


class Portal(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
