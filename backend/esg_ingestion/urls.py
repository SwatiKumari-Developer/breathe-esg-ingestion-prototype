from django.contrib import admin
from django.urls import include, path

from .views import react_app

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("ingestion.urls")),
    path("", react_app),
    path("<path:unused>", react_app),
]
