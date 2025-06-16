from django.urls import path

from . import views

app_name = "music_statistics"
urlpatterns = [
    path(
        "history/<int:user_id>",
        views.ListeningHistoryListView.as_view(),
        name="listening_history",
    ),
    path("charts/", views.TopChartDetailView.as_view(), name="top_chart"),
    path("liked-artists/", views.UserLikedArtistView.as_view(), name="user_liked_artists"),
]
