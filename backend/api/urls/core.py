from django.urls import path
from api import views

urlpatterns = [
    path("analyze/",        views.analyze,        name="analyze"),
    path("analyze/upload/", views.analyze_upload, name="analyze-upload"),
    path("health/",         views.health,          name="health"),
    path("stats/",          views.project_stats,   name="stats"),
]
