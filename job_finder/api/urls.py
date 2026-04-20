from django.urls import include, path

from . import views

urlpatterns = [
    path("auth/", include("rest_framework.urls")),
    path("tasks/", views.TaskList.as_view()),
    path("tasks/<uuid:task_id>/", views.TaskDetail.as_view()),
    path("job_listings/", views.JobListingList.as_view()),
    path("job_listings/<int:pk>/", views.JobListingDetail.as_view()),
    path("portals/", views.PortalList.as_view()),
    path("system_instructions/", views.SystemInstructionList.as_view()),
]
