from django.forms import BaseModelForm
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from .forms import (
    CreateAlbumForm,
    CreateArtistForm,
    CreatePlaylistForm,
    CreateTrackForm,
)
from .models import Album, Artist, Playlist, Track


# Create your views here.
def index(request) -> HttpResponse:
    return render(request, "index.html")


class CreateArtist(CreateView):
    form_class = CreateArtistForm
    template_name = "music/create_artist.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("music:artist_detail", kwargs={"pk": self.object.pk})


class ArtistDetailView(DetailView):
    model = Artist
    pk_url_kwarg = "pk"
    template_name = "music/artist_detail.html"
    context_object_name = "artist"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        artist = self.object
        tracks = Track.objects.filter(artist=artist)
        albums = Album.objects.filter(artist=artist)
        liked_playlist = Playlist.objects.filter(
            owner=self.request.user, is_liked_playlist=True
        ).first()
        context["liked_tracks"] = (
            liked_playlist.tracks.filter(artist=artist) if liked_playlist else []
        )
        context["playlists"] = Playlist.objects.filter(owner=self.request.user)
        context["tracks"] = tracks
        context["albums"] = albums
        return context


class CreateAlbum(CreateView):
    form_class = CreateAlbumForm
    template_name = "music/create_album.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        artist_id = self.kwargs["pk"]
        if artist := get_object_or_404(Artist, pk=artist_id):
            self.request.user = artist.user
            kwargs["artist"] = artist
        return kwargs

    """def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        artist = kwargs["artist"]
        print(artist)
        form = self.get_form()
        tracks = Track.objects.filter(artist=artist, album__isnull=True)
        form.fields["tracks"] = tracks
        context["tracks"] = tracks
        return context
"""


class CreateTrack(CreateView):
    form_class = CreateTrackForm
    template_name = "music/create_track.html"

    def form_valid(self, form: BaseModelForm):
        file_path = self.object.audio_file.path
        form.instance.artist = self.request.user.id
        # self.object.duration = int(audio.info.length)
        self.object.save(update_fields=["duration"])

        return super().form_valid(form)


class ManageFavoriteTrack(View):
    def post(self, request, track_id: int):
        track: Track = get_object_or_404(Track, pk=track_id)
        liked_playlist, created = Playlist.objects.get_or_create(
            owner=request.user,
            is_liked_playlist=True,
            title="favorite",
            image="/playlists_images/favorite.jpg",
        )
        if liked_playlist:
            action = request.POST.get("action")
            if action == "like":
                liked_playlist.tracks.add(track)
            elif action == "unlike":
                liked_playlist.tracks.remove(track)

        return redirect("music:artist_detail", pk=track.artist.id)


class UnlikeTrack(View):
    def post(self, request, track_id: int):
        track: Track = get_object_or_404(Track, pk=track_id)
        liked_playlist = Playlist.objects.get(
            owner=request.user, is_liked_playlist=True
        )
        if liked_playlist:
            liked_playlist.tracks.delete(track)
        return redirect("music:artist_detail", pk=track.artist.id)


class AddTrackInPlaylist(View):
    def post(self, request, track_id: int):
        track: Track = get_object_or_404(Track, pk=track_id)
        playlist_id: int = request.POST.get("playlist_id")
        if playlist_id:
            playlist = get_object_or_404(
                Playlist,
                pk=playlist_id,
                owner=request.user,
            )
            print(playlist)
            playlist.tracks.add(track)
        return redirect("music:artist_detail", pk=track.artist.id)


class RemoveTrackFromFavorite(DeleteView):
    pass


# Playlist views


class CreatePlaylist(CreateView):
    form_class = CreatePlaylistForm
    template_name = "music/create_playlist.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class PlaylistDetail(DetailView):
    model = Playlist
    template_name = "music/playlist_detail.html"
    context_object_name = "playlist"

    """def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tracks_in_playlist"]=self.get_object()
"""


class UpdatePlaylist(UpdateView):
    model = Playlist


class DeletePlaylist(DetailView):
    model = Playlist


class MyPlaylists(ListView):
    model = Playlist
    paginate_by = 10
    template_name = "music/my_playlists.html"
    context_object_name = "playlists"

    def get_queryset(self):
        user = self.request.user
        return Playlist.objects.filter(owner=user)
