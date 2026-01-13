from django.urls import path

from . import views

app_name = "scanner"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("refresh/", views.overview_refresh, name="overview_refresh"),
    path("<int:host_id>/", views.host_detail, name="host_detail"),
]
