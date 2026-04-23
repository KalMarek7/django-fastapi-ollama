from django_filters.rest_framework import DjangoFilterBackend
from home.models import JobListing, Portal, SystemInstruction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from tasks.models import Task

from .serializers import (
    JobListingSerializer,
    PortalSerializer,
    SystemInstructionSerializer,
    TaskSerializer,
)


class TaskList(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["task_id"]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        task_id = request.data.get("task_id")
        obj = Task.objects.filter(task_id=task_id).first()
        # Check if task already exists
        if obj:
            # Update existing
            serializer = self.get_serializer(obj, data=request.data, partial=True)
        else:
            # Create new
            serializer = self.get_serializer(obj, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        res_status = status.HTTP_201_CREATED if not obj else status.HTTP_200_OK
        return Response(serializer.data, status=res_status)


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "task_id"


class JobListingList(generics.ListCreateAPIView):
    queryset = JobListing.objects.all()
    serializer_class = JobListingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "url"]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        url = request.data.get("url")
        # Check if job already exists
        obj = JobListing.objects.filter(url=url).first()
        if obj:
            # Update existing
            serializer = self.get_serializer(obj, data=request.data, partial=True)
        else:
            # Create new
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        res_status = status.HTTP_201_CREATED if not obj else status.HTTP_200_OK
        return Response(serializer.data, status=res_status)


class JobListingDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = JobListing.objects.all()
    serializer_class = JobListingSerializer
    permission_classes = [permissions.IsAuthenticated]


class PortalList(generics.ListCreateAPIView):
    queryset = Portal.objects.all()
    serializer_class = PortalSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]


class SystemInstructionList(generics.ListCreateAPIView):
    queryset = SystemInstruction.objects.all()
    serializer_class = SystemInstructionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id"]
