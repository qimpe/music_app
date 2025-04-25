from django.urls import path

from . import views

app_name = "music"

urlpatterns = [
    path("create-artist/", views.CreateArtistView.as_view(), name="create_artist"),
    path("artist/<int:artist_id>/", views.ArtistDetailView.as_view(), name="artist_detail"),
    path("artist/<int:pk>/create-track/", views.CreateTrack.as_view(), name="create_track"),
    path(
        "artist/<int:artist_id>/create-album/",
        views.CreateAlbum.as_view(),
        name="create_album",
    ),
    path(
        "like/artist/<int:artist_id>/",
        views.FollowArtist.as_view(),
        name="follow_artist",
    ),
    path(
        "manage-track/<int:track_id>/",
        views.ManageFavoriteTrack.as_view(),
        name="manage_favorite",
    ),
    path("stream/<int:track_id>/", views.AudioStreamView.as_view(), name="stream_audio"),
    path("album/<int:album_id>/", views.AlbumDetailView.as_view(), name="album_detail"),
    path(
        "artist/<int:artist_id>/release-album/<int:album_id>/",
        views.ReleaseAlbumView.as_view(),
        name="release_album",
    ),
]

""" path("playlist/<int:pk>", views.PlaylistDetail.as_view(), name="playlist_detail"),
    path("my-playlists/", views.MyPlaylists.as_view(), name="my_playlists"),
    path("create-playlist/", views.CreatePlaylist.as_view(), name="create_playlist"),
    path(
        "add-track/<int:track_id>/",
        views.AddTrackInPlaylist.as_view(),
        name="add_track",
    ),"""
