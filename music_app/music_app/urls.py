from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from music.views import index

urlpatterns = [
    path("", index, name="main"),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("music/", include("music.urls")),
    path("statistics/", include("music_statistics.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
