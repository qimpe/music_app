import typing
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.http.response import HttpResponseRedirectBase
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView
from music_statistics.models import ArtistUniqueListeners, UserArtistsFollow
from mutagen import File

from .forms import CreateAlbumForm, CreateArtistForm, CreateTrackForm
from .mixins import ArtistAccessMixin
from .models import Album, Artist, Playlist, Track


# Create your views here.
# * Main Page
def index(request: HttpRequest) -> HttpResponse:
    """Главная страница с топом артистов, последними релизами артистов за которыми следит пользователь."""  # noqa: RUF002
    top_month_artists = Artist.objects.order_by("-month_listeners")[:5]
    context: dict = {"top_month_artists": top_month_artists}
    return render(request, "index.html", context=context)


# * Artist Views
class CreateArtistView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Представление создание артиста."""

    form_class = CreateArtistForm
    template_name = "music/create_artist.html"
    permission_denied_message = "The number of artists you can create has been exceeded"

    def test_func(self) -> bool:
        """Проверяет может ли пользователь создать более одного артиста. Лейбл может создать больше 1 артиста."""
        user = self.request.user
        return user.is_label or Artist.objects.filter(user=user).count() < 1

    def form_valid(self, form: CreateArtistForm) -> HttpResponse:
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy("music:artist_detail", kwargs={"artist_id": self.object.pk})


class ArtistDetailView(DetailView):
    """Подробная страница артиста."""

    model = Artist
    pk_url_kwarg = "artist_id"
    template_name = "music/artist_detail.html"
    context_object_name = "artist"

    def get_context_data(self, **kwargs: dict) -> dict[str, typing.Any]:
        context = super().get_context_data(**kwargs)
        artist = self.object
        user = self.request.user
        if user == artist.user:
            context["albums"] = Album.objects.filter(artist=artist).order_by(
                "-release_date",
            )
        else:
            context["albums"] = Album.objects.filter(
                artist=artist,
                release_date__isnull=False,
            ).order_by(
                "-release_date",
            )
        unique_listeners = ArtistUniqueListeners.objects(artist_id=artist.id).first()
        """is_followed = UserArtistsFollow.objects(
            user_id=self.request.user.id,artists
        )"""
        listeners_count = len(unique_listeners.listeners) if unique_listeners else 0
        context["month_listeners"] = listeners_count

        user_likes_playlist, _ = Playlist.objects.get_or_create(
            owner=user,
            is_liked_playlist=True,
        )
        context["tracks"] = Track.objects.filter(artist=artist)
        context["liked_tracks"] = user_likes_playlist.tracks.filter(artist=artist) if user_likes_playlist else []

        return context


class FollowArtist(LoginRequiredMixin, View):
    """Подписка на артиста."""

    def post(self, request: HttpRequest, **kwargs: dict) -> HttpResponse:
        if artist_id := kwargs.get("artist_id"):
            is_liked = UserArtistsFollow.objects(user_id=request.user.id).first()
            if not is_liked:
                is_liked = UserArtistsFollow(user_id=request.user.id)
            is_liked.artists.append(artist_id)
            is_liked.save()
            messages.success(request, "Артист добален в лайки")

        else:
            messages.error(request, "Артист не найден")
        return redirect("music:artist_detail", artist_id=artist_id)


# * Albums views
class CreateAlbum(ArtistAccessMixin, LoginRequiredMixin, CreateView):
    """Представление создания альбома."""

    form_class = CreateAlbumForm
    template_name = "music/create_album.html"

    def get_form_kwargs(self) -> dict[str, typing.Any]:
        kwargs = super().get_form_kwargs()
        kwargs["artist"] = self.artist
        return kwargs

    def get_context_data(self, **kwargs: dict) -> dict[str, typing.Any]:
        context = super().get_context_data(**kwargs)
        context["artist_id"] = self.kwargs["artist_id"]
        context["tracks"] = Track.objects.filter(artist=self.artist, album__isnull=True)
        return context

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.instance.artist = self.artist
        response = super().form_valid(form)
        tracks = form.cleaned_data.get("tracks")

        if tracks:
            tracks.update(album=form.instance)
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("music:artist_detail", kwargs={"artist_id": self.artist.pk})


class AlbumDetailView(DetailView):
    """Подробная информация об альбоме."""  # noqa: RUF002

    model = Album
    pk_url_kwarg = "album_id"
    template_name = "music/album_detail.html"
    context_object_name = "album"

    def get_context_data(self, **kwargs: dict) -> dict[str, typing.Any]:
        context = super().get_context_data(**kwargs)
        album: Album = self.get_object()

        if self.request.user == album.artist.user:
            context["artist"] = album.artist

        context.update({"tracks": Track.objects.filter(album=album)})
        return context


class ReleaseAlbumView(ArtistAccessMixin, View):
    """Релизит альбом и делает его общедоступным."""  # noqa: RUF002

    def post(
        self,
        request: HttpRequest,  # noqa: ARG002
        artist_id: int,
        album_id: int,
    ) -> HttpResponse | HttpResponseRedirectBase:
        if album := get_object_or_404(Album, pk=album_id):
            album.release()
            return redirect("music:artist_detail", artist_id=artist_id)
        return HttpResponse("Album does not exist", status=404)


# * Track views
class CreateTrack(LoginRequiredMixin, CreateView):
    """Представление создания трека."""

    form_class = CreateTrackForm
    template_name = "music/create_track.html"

    def get_success_url(self) -> str:
        return reverse_lazy(
            "music:artist_detail",
            kwargs={"artist_id": self.kwargs["artist_id"]},
        )

    def form_valid(self, form: CreateTrackForm) -> HttpResponse:
        self.object: Track = form.save(commit=False)
        audio_file = self.object.audio_file
        audio = File(audio_file)
        self.object.artist = Artist.objects.filter(user=self.request.user.id).first()
        self.object.duration = int(audio.info.length)
        self.object.save()
        self.kwargs["artist_id"] = self.object.artist.pk
        return super().form_valid(form)


class AudioStreamView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, track_id: int) -> StreamingHttpResponse:
        user = request.user
        user.add_track_in_user_history(track_id)
        track = get_object_or_404(Track, id=track_id)
        track.artist.update_unique_listeners(user.id)
        file_path = track.audio_file.path
        file_size = Path.stat(file_path).st_size
        range_header: str = request.headers.get("Range", "").strip()
        start, end = range_header.replace("bytes=", "").split("-")

        content_type = "audio/mpeg"
        response = None

        if range_header:
            start = int(start)
            end = int(end) if end else file_size - 1
            length = end - start + 1

            def stream_file():
                with Path(file_path).open("rb") as f:
                    f.seek(start)
                    remaining = length
                    chunk_size = 8192  # 8KB

                    while remaining > 0:
                        data = f.read(min(chunk_size, remaining))
                        if not data:
                            break
                        yield data
                        remaining -= len(data)

            response = StreamingHttpResponse(
                stream_file(),
                status=206,
                content_type=content_type,
            )
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Content-Length"] = str(length)

        else:

            def stream_file():
                with Path(file_path).open("rb") as f:
                    yield from f

            response = StreamingHttpResponse(stream_file(), content_type=content_type)
            response["Content-Length"] = str(file_size)

        response["Accept-Ranges"] = "bytes"
        return response


class ManageFavoriteTrack(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, track_id: int) -> HttpResponseRedirectBase:
        track: Track = get_object_or_404(Track, pk=track_id)
        liked_playlist, created = Playlist.objects.get_or_create(
            owner=request.user,
            is_liked_playlist=True,
            title="favorite",
            image="/playlists_images/favorite.jpg",
        )
        action = request.POST.get("action")
        if action == "like":
            liked_playlist.tracks.add(track)

            messages.success(request, f"Трек {track.title} был добавлен в мне нравится")
        elif action == "unlike":
            liked_playlist.tracks.remove(track)
            messages.info(request, f"Трек {track.title} был удален")
        else:
            messages.error(request, "Неизвестное действие")
        return redirect("music:artist_detail", artist_id=track.artist.id)


"""class UnlikeTrack(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, track_id: int) -> HttpResponseRedirectBase:
        track: Track = get_object_or_404(Track, pk=track_id)
        liked_playlist = Playlist.objects.get(
            owner=request.user,
            is_liked_playlist=True,
        )
        if liked_playlist:
            liked_playlist.tracks.delete(track)
        return redirect("music:artist_detail", pk=track.artist.id)


class AddTrackInPlaylist(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, track_id: int) -> HttpResponseRedirectBase:
        track: Track = get_object_or_404(Track, pk=track_id)
        playlist_id: int = request.POST.get("playlist_id")
        if playlist_id:
            playlist = get_object_or_404(
                Playlist,
                pk=playlist_id,
                owner=request.user,
            )
            playlist.tracks.add(track)
        return redirect("music:artist_detail", pk=track.artist.id)


class RemoveTrackFromFavorite(DeleteView):
    pass


# Playlist views


class CreatePlaylist(LoginRequiredMixin, CreateView):
    form_class = CreatePlaylistForm
    template_name = "music/create_playlist.html"

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.instance.owner = self.request.user
        return super().form_valid(form)


class PlaylistDetail(LoginRequiredMixin, DetailView):
    model = Playlist
    template_name = "music/playlist_detail.html"
    context_object_name = "playlist"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tracks_in_playlist"]=self.get_object()

    """
"""


class UpdatePlaylist(LoginRequiredMixin, UpdateView):
    model = Playlist


class DeletePlaylist(LoginRequiredMixin, DetailView):
    model = Playlist


class MyPlaylists(LoginRequiredMixin, ListView):
    model = Playlist
    paginate_by = 10
    template_name = "music/my_playlists.html"
    context_object_name = "playlists"

    def get_queryset(self) -> QuerySet[Playlist]:
        user = self.request.user
        return Playlist.objects.filter(owner=user)"""
