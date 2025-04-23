from django.urls import path

from .views import (
    AddTrackInPlaylist,
    AlbumDetailView,
    ArtistDetailView,
    AudioStreamView,
    CreateAlbum,
    CreateArtistView,
    CreatePlaylist,
    CreateTrack,
    ManageFavoriteTrack,
    MyPlaylists,
    PlaylistDetail,
    ReleaseAlbumView,
)

app_name = "music"

urlpatterns = [
    path("create-artist/", CreateArtistView.as_view(), name="create_artist"),
    path("artist/<int:artist_id>/", ArtistDetailView.as_view(), name="artist_detail"),
    path(
        "artist/<int:artist_id>/create-album/",
        CreateAlbum.as_view(),
        name="create_album",
    ),
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
        "manage-track/<int:track_id>/",
        ManageFavoriteTrack.as_view(),
        name="manage_track",
    ),
    path("stream/<int:track_id>/", AudioStreamView.as_view(), name="stream_audio"),
    path("album/<int:album_id>/", AlbumDetailView.as_view(), name="album_detail"),
    path(
        "artist/<int:artist_id>/release-album/<int:album_id>/",
        ReleaseAlbumView.as_view(),
        name="release_album",
    ),
]
