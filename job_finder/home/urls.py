from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("update/", views.update_view, name="update"),
]
