from django.contrib import admin
from django.urls import path

from .views import (
    AddTrackInPlaylist,
    ArtistDetailView,
    CreateAlbum,
    CreateArtist,
    CreatePlaylist,
    CreateTrack,
    ManageFavoriteTrack,
    MyPlaylists,
    PlaylistDetail,
)

app_name = "music"

urlpatterns = [
    path("create-artist/", CreateArtist.as_view(), name="create_artist"),
    path("artist/<int:pk>/", ArtistDetailView.as_view(), name="artist_detail"),
    path("artist/<int:pk>/create-album/", CreateAlbum.as_view(), name="create_album"),
    path("artist/<int:pk>/create-track/", CreateTrack.as_view(), name="create_track"),
    path("playlist/<int:pk>", PlaylistDetail.as_view(), name="playlist_detail"),
    path("my-playlists/", MyPlaylists.as_view(), name="my_playlists"),
    path("create-playlist/", CreatePlaylist.as_view(), name="create_playlist"),
    path(
        "add-track/<int:track_id>/",
        AddTrackInPlaylist.as_view(),
        name="add_track",
    ),
    path(
        "like-track/<int:track_id>/",
        ManageFavoriteTrack.as_view(),
        name="like_track",
    ),
]
