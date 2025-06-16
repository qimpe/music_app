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
        views.ManageTrack.as_view(),
        name="manage_track",
    ),
    path("stream/<int:track_id>/", views.AudioStreamView.as_view(), name="stream_audio"),
    path("album/<int:album_id>/", views.AlbumDetailView.as_view(), name="album_detail"),
    path(
        "artist/<int:artist_id>/release-album/<int:album_id>/",
        views.ReleaseAlbumView.as_view(),
        name="release_album",
    ),
    path("my-playlists/", views.MyPlaylists.as_view(), name="my_playlists"),
    path("playlist/<int:playlist_id>", views.PlaylistDetail.as_view(), name="playlist_detail"),
    path("create-playlist/", views.CreatePlaylistView.as_view(), name="create_playlist"),
    path("update-playlist/<int:playlist_id>", views.UpdatePlaylistView.as_view(), name="update_playlist"),
    path("delete-playlist/<int:playlist_id>", views.DeletePlaylistView.as_view(), name="delete_playlist"),
    path("admin/review-requests", views.review_requests, name="review_requests"),
    path("admin/approve-review-request/<int:obj_id>", views.approve_review_request, name="approve_review_requests"),
    path("admin/reject-review-request/<int:obj_id>", views.reject_review_request, name="reject_review_requests"),
]
