from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("mainapp/", include("mainapp.urls")),
    path("admin/", admin.site.urls),
    path("result/", include("mainapp.urls")),
    path("report/", include("mainapp.urls"))
]
