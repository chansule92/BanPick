from django.contrib import admin
from django.urls import include, path
from mainapp.views import health_check

urlpatterns = [
    path('', health_check), 
    path("mainapp/", include("mainapp.urls")),
    path("admin/", admin.site.urls),
    path("result/", include("mainapp.urls")),
    path("report/", include("mainapp.urls"))
]
