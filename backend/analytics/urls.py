from django.urls import path
from . import views

urlpatterns = [
    path("overview/",    views.overview,       name="analytics-overview"),
    path("languages/",   views.by_language,    name="analytics-languages"),
    path("top-errors/",  views.top_errors,     name="analytics-top-errors"),
    path("daily/",       views.daily_activity, name="analytics-daily"),
    path("users/",       views.user_list,      name="analytics-users"),
    path("users/<int:uid>/", views.user_detail, name="analytics-user-detail"),
    path("quota/",       views.quota_summary,  name="analytics-quota"),
]
