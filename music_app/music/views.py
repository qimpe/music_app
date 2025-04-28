import typing
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.http.response import HttpResponseRedirectBase
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from mutagen import File

from . import services
from .forms import CreateAlbumForm, CreateArtistForm, CreatePlaylistForm, CreateTrackForm
from .mixins import ArtistAccessMixin
from .models import Album, Artist, Playlist, Track

if typing.TYPE_CHECKING:
    from users.models import User


# Create your views here.
# * Main Page
def index(request: HttpRequest) -> HttpResponse:
    """Главная страница с топом артистов, последними релизами артистов за которыми следит пользователь."""
    context: dict = {"top_month_artists": services.fetch_top_5_artists_per_month()}
    return render(request, "index.html", context=context)


# * Artist Views
# ! refactoring
class CreateArtistView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Представление создание артиста."""

    form_class = CreateArtistForm
    template_name = "music/create_artist.html"
    permission_denied_message = "The number of artists you can create has been exceeded"

    def test_func(self) -> bool:
        """Проверяет может ли пользователь создать более одного артиста. Лейбл может создать больше 1 артиста."""
        user = typing.cast("User", self.request.user)
        return user.is_label or Artist.objects.filter(user=user).count() < 1

    def form_valid(self, form: CreateArtistForm) -> HttpResponse:
        user = typing.cast("User", self.request.user)
        form.instance.user = user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        artist = typing.cast("Artist", self.object)
        return reverse_lazy("music:artist_detail", kwargs={"artist_id": artist.pk})


class ArtistDetailView(LoginRequiredMixin, DetailView):
    """Карточка артиста."""

    model = Artist
    pk_url_kwarg = "artist_id"
    template_name = "music/artist_detail.html"
    context_object_name = "artist"

    def get_context_data(self, **kwargs: dict) -> dict[str, typing.Any]:
        context = super().get_context_data(**kwargs)
        artist = self.object
        user = self.request.user
        services.fetch_artists_detail_page(context, user, artist)
        return context


class FollowArtist(LoginRequiredMixin, View):
    """Подписка на артиста."""

    def post(self, request: HttpRequest, **kwargs: dict) -> HttpResponse:
        if artist_id := kwargs.get("artist_id"):
            services.follow_for_artist(request.user.id, artist_id)
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
        context["tracks"] = services.fetch_tracks_without_album(self.artist)
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
    """Подробная информация об альбоме."""

    model = Album
    pk_url_kwarg = "album_id"
    template_name = "music/album_detail.html"
    context_object_name = "album"

    def get_context_data(self, **kwargs: dict) -> dict[str, typing.Any]:
        context = super().get_context_data(**kwargs)
        album: Album = self.get_object()
        if self.request.user == album.artist.user:
            context["artist"] = album.artist
        context.update({"tracks": services.fetch_tracks_in_album()})
        return context


class ReleaseAlbumView(ArtistAccessMixin, View):
    """Релизит альбом и делает его общедоступным."""

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
        try:
            audio = File(audio_file)
        except Exception as ex:
            msg = "file not found"
            raise TypeError(msg) from ex

        artist: Artist = services.fetch_artist_by_user_id(self.request.user.id)
        track_duration_in_seconds: int = int(audio.info.length)
        if artist:
            self.object.artist = artist
            self.object.duration = track_duration_in_seconds
            self.object.save()
            self.kwargs["artist_id"] = artist.id
        return super().form_valid(form)


class AudioStreamView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, track_id: int) -> StreamingHttpResponse:
        track = get_object_or_404(Track, id=track_id)
        file_path: str = track.audio_file.path
        file_size: int = Path.stat(file_path).st_size
        range_header: str = request.headers.get("Range", "").strip()
        start, end = range_header.replace("bytes=", "").split("-")

        content_type = "audio/mpeg"
        response = None

        if range_header:
            start = int(start)
            end = int(end) if end else file_size - 1
            length = end - start + 1

            def stream_file():
                with open(file_path, "rb") as f:
                    f.seek(start)
                    remaining = length
                    chunk_size = 8192  # 8KB

                    while remaining > 0:
                        data = f.read(min(chunk_size, remaining))
                        if not data:
                            break
                        yield data
                        remaining -= len(data)

            response = StreamingHttpResponse(stream_file(), status=206, content_type=content_type)
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Content-Length"] = str(length)

        else:

            def stream_file():
                with open(file_path, "rb") as f:
                    yield from f

            response = StreamingHttpResponse(stream_file(), content_type=content_type)
            response["Content-Length"] = str(file_size)

        response["Accept-Ranges"] = "bytes"
        return response


"""typing.cast("User", request.user)
        user.add_track_in_listening_history(track_id)


        track.artist.update_unique_listeners(user.id)
        track = get_object_or_404(Track, id=track_id)
        track_stream: TrackStream = TrackStream.objects(artist_id=track.artist.id, track_id=track_id).first()
        if not track_stream:
            track_stream = TrackStream(artist_id=track.artist.id, track_id=track_id)
        track_stream.listen_count += 1
        track_stream.save()

        file_path: str = track.audio_file.path
        file_size: int = Path.stat(file_path).st_size
        range_header: str = request.headers.get("Range", "").strip()
        start, end = range_header.replace("bytes=", "").split("-")

        content_type = "audio/mpeg"
        response = None

        if range_header:
            start = int(start)
            end = int(end) if end else file_size - 1
            file_length: int = end - start + 1
            response = StreamingHttpResponse(
                self.stream_file(start, file_path, file_length),
                status=206,
                content_type=content_type,
            )
            response["Content-Length"] = str(file_length)
            response["Accept-Ranges"] = "bytes"
        else:
            pass

        return response

    def stream_file(self, start: int, file_path: str, file_length: int) -> typing.Generator[bytes, None, None]:
        with Path(file_path).open("rb") as file:
            file.seek(start)
            remaining = file_length
            chunk_size: typing.Final = 8192  # 8KB

            while remaining > 0:
                data = file.read(min(chunk_size, remaining))
                if not data:
                    break
                yield data
                remaining -= len(data)"""


class ManageFavoriteTrack(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, track_id: int) -> HttpResponseRedirectBase:
        action = request.POST.get("action")
        if action == "like":
            track = services.add_track_in_likes_playlist(track_id, request.user)
            messages.success(request, f"Трек {track.title} был добавлен")
        elif action == "unlike":
            track = services.delete_track_from_likes_playlist(track_id, request.user)
            messages.info(request, f"Трек {track.title} был удален")
        else:
            messages.error(request, "Неизвестное действие")
        return redirect("music:artist_detail", artist_id=track.artist.id)


# * Playlists view
class PlaylistDetail(LoginRequiredMixin, DetailView):
    model = Playlist
    template_name = "music/playlist_detail.html"
    context_object_name = "playlist"

    def get_context_data(self, **kwargs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        context = super().get_context_data(**kwargs)
        context["tracks_in_playlist"] = self.get_object()
        return context


class MyPlaylists(LoginRequiredMixin, ListView):
    model = Playlist
    paginate_by = 10
    template_name = "music/my_playlists.html"
    context_object_name = "playlists"

    def get_queryset(self) -> QuerySet[Playlist]:
        request: HttpRequest = self.request
        return Playlist.objects.filter(owner=request.user)


class CreatePlaylist(LoginRequiredMixin, CreateView):
    form_class = CreatePlaylistForm
    template_name = "music/create_playlist.html"

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.instance.owner = self.request.user
        return super().form_valid(form)
