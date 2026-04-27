from django.db import models


# Create your models here.
class JobListing(models.Model):
    title = models.CharField(null=True, blank=True, max_length=200)
    text_content = models.TextField()
    expiry_date = models.DateField(
        null=True,
        blank=True,
    )
    url = models.URLField(null=True, blank=True, unique=True, max_length=350)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    company = models.CharField(null=True, blank=True, max_length=200)
    years_of_experience = models.IntegerField(null=True, blank=True, verbose_name="YoE")
    salary = models.CharField(null=True, blank=True, max_length=200)
    portal = models.ForeignKey("Portal", on_delete=models.CASCADE)
    posted_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.url}"

    class Meta:
        ordering = ["-created_at"]


class Portal(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-name"]


class SystemInstruction(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    instruction = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]


class Resume(models.Model):
    name = models.CharField(max_length=100)
    text_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class JobMatch(models.Model):
    # resume = models.ForeignKey('Resume', on_delete=models.CASCADE)
    job_listing = models.ForeignKey("JobListing", on_delete=models.CASCADE)
    llm_output = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.job_listing}"

    class Meta:
        # Prevent duplicate analysis for the same resume/job pair
        unique_together = ["job_listing"]
        verbose_name_plural = "Job matches"
