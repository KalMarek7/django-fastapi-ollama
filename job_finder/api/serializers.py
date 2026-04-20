from home.models import JobListing, Portal, SystemInstruction
from rest_framework.serializers import CharField, ModelSerializer
from tasks.models import Task


class JobListingSerializer(ModelSerializer):
    class Meta:
        model = JobListing
        fields = "__all__"


class TaskSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"

    task_id = CharField(help_text="The id of the task", default="uuid")


class PortalSerializer(ModelSerializer):
    class Meta:
        model = Portal
        fields = "__all__"


class SystemInstructionSerializer(ModelSerializer):
    class Meta:
        model = SystemInstruction
        fields = "__all__"
