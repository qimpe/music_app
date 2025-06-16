import typing
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import exceptions
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import Http404, HttpRequest, HttpResponse, StreamingHttpResponse
from django.http.response import HttpResponseRedirectBase
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from music_statistics import services as stat_services
from music_statistics import services as stats_services
from mutagen import File

from .forms import CreateAlbumForm, CreateArtistForm, CreatePlaylistForm, CreateTrackForm
from .mixins import ArtistAccessMixin
from .models import Album, Artist, Music, Playlist, Track
from .services import services
from .services.admin_services import approve_music_object, check_staff_permissions, reject_music_object


# Create your views here.
# * Main Page
def index(request: HttpRequest) -> HttpResponse:
    """Главная страница с топом артистов, последними релизами артистов за которыми следит пользователь."""
    context: dict = {
        "top_month_artists": services.fetch_top_5_artists_per_month(),
        "chart": stats_services.fetch_music_chart(),
    }
    return render(request, "index.html", context=context)


# * Artist Views
class CreateArtistView(LoginRequiredMixin, View):
    """Представление создание артиста."""

    def get(self, request: HttpRequest) -> HttpResponse:
        form = CreateArtistForm()
        return render(request, "music/create_artist.html", context={"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = CreateArtistForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                artist = services.create_artist(request.user, form)
                messages.success(request, "Артист успешно создан!")
                return redirect("music:artist_detail", artist_id=artist.id)

            messages.error(request, "Исправьте ошибки в форме")
            return render(request, "music/create_artist.html", {"form": form})

        except exceptions.ValidationError as e:
            return render(request, "music/create_artist.html", {"form": form, "error": str(e)})


class ArtistDetailView(LoginRequiredMixin, DetailView):
    """Карточка артиста."""

    model = Artist
    pk_url_kwarg = "artist_id"
    template_name = "music/artist_detail.html"
    context_object_name = "artist"

    def get_context_data(self, **kwargs: dict) -> dict[str, typing.Any]:
        context = super().get_context_data(**kwargs)

        user = self.request.user
        artist = self.object
        services.fetch_or_create_artist_unique_listeners(artist.id)
        user_likes_playlist = services.fetch_or_create_user_likes_playlist(user=user)
        unique_listeners = services.fetch_artists_unique_listeners(artist_id=artist.id)

        context["albums"] = services.fetch_artists_album(user=user, artist=artist)
        context["month_listeners_count"] = len(unique_listeners["listeners"]) if unique_listeners["listeners"] else 0
        # context["popular_tracks"] = services.fetch_artists_popular_tracks(artist_id=artist.id)
        context["popular_tracks"] = services.fetch_artists_popular_tracks(artist_id=artist.id)
        context["liked_tracks"] = user_likes_playlist.tracks.filter(artist=artist) if user_likes_playlist else []

        return context


class FollowArtist(LoginRequiredMixin, View):
    """Подписка на артиста."""

    def post(self, request: HttpRequest, **kwargs: dict) -> HttpResponse:
        if artist_id := kwargs.get("artist_id"):
            services.follow_for_artist(request.user.id, artist_id)
            messages.success(request, "Артист добален в лайки")
        else:
            messages.error(request, "Артист не найден")
            # TODO нужно перенаправить куда-то если артист не найден
        return redirect("music:artist_detail", artist_id=artist_id)


# * Albums views
class CreateAlbum(ArtistAccessMixin, LoginRequiredMixin, View):
    """Представление создания альбома."""

    def get(self, request: HttpRequest, artist_id: int) -> HttpResponse:
        tracks = services.fetch_tracks_without_album(self.artist)
        form = CreateAlbumForm(tracks=tracks)
        return render(
            request, "music/create_album.html", context={"form": form, "artist_id": artist_id, "tracks": tracks}
        )

    def post(self, request: HttpRequest, artist_id: int) -> HttpResponse:
        tracks = services.fetch_tracks_without_album(self.artist)
        form = CreateAlbumForm(request.POST, request.FILES, tracks=tracks)
        try:
            if form.is_valid():
                album = services.create_album(form, artist_id)
                return redirect("music:album_detail", album_id=album.id)
        except exceptions.ValidationError as e:
            return render(request, "music/create_artist.html", {"form": form, "error": str(e)})


class AlbumDetailView(DetailView):
    """Подробная информация об альбоме."""

    model = Album
    pk_url_kwarg = "album_id"
    template_name = "music/album_detail.html"
    context_object_name = "album"

    def get_context_data(self, **kwargs: dict) -> dict[str, typing.Any]:
        context = super().get_context_data(**kwargs)
        album = services.fetch_album_by_id(self.kwargs["album_id"])
        if self.request.user == album.artist.user:
            context["artist"] = album.artist
        context.update({"tracks": services.fetch_tracks_in_album(album)})
        return context


class ReleaseAlbumView(ArtistAccessMixin, View):
    """Релизит альбом и делает его общедоступным."""

    def post(
        self,
        request: HttpRequest,  # noqa: ARG002
        artist_id: int,
        album_id: int,
    ) -> HttpResponse:
        try:
            if album := services.fetch_album_by_id(album_id):
                album.release()
                return redirect("music:artist_detail", artist_id=artist_id)
        except Http404:
            return HttpResponse("Album does not exist", status=404)


############################# * Track views
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


##################################################*


class AudioStreamView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, track_id: int) -> StreamingHttpResponse:
        track = get_object_or_404(Track, id=track_id)
        file_path: str = track.audio_file.path
        file_size: int = Path.stat(file_path).st_size
        range_header: str = request.headers.get("Range", "").strip()
        start, end = range_header.replace("bytes=", "").split("-")
        services.add_unique_listener_to_artist(artist_id=track.artist.id, listener_id=request.user.id)
        stat_services.add_track_to_listening_history(request.user.id, track.id)

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


class ManageTrack(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, track_id: int) -> HttpResponseRedirectBase:
        action = request.POST.get("action")
        artist_id = None
        if action in ("like", "unlike"):
            artist_id = services.manage_track(request.user, action, track_id, is_liked=True)
        else:
            playlist_id = request.POST.get("playlist_id")
            artist_id = services.manage_track(request.user, action, track_id, is_liked=False, playlist_id=playlist_id)
        return redirect("music:artist_detail", artist_id=artist_id)


# * Playlists view
class PlaylistDetail(LoginRequiredMixin, DetailView):
    model = Playlist
    template_name = "music/playlist_detail.html"
    context_object_name = "playlist"
    pk_url_kwarg = "playlist_id"

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
        return services.fetch_my_playlists(request.user)


#! refactoring
class CreatePlaylistView(LoginRequiredMixin, CreateView):
    form_class = CreatePlaylistForm
    template_name = "music/create_playlist.html"

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.instance.owner = self.request.user
        return super().form_valid(form)


class DeletePlaylistView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, playlist_id: Playlist) -> None:
        try:
            services.delete_playlist(request.user, playlist_id)
            messages.success(request, "Плейлист удален")
            return redirect(reverse("music:my_playlists"))
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect("music:playlist_detail", playlist_id=playlist_id)


class UpdatePlaylistView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, playlist_id: Playlist) -> None:
        return render(request, "music/update_playlist.html", context={"playlist_id": playlist_id})

    def post(self, request: HttpRequest, playlist_id: Playlist) -> None:
        try:
            title = request.POST.get("title")
            is_public = request.POST.get("is_public") == "on"
            image = request.FILES.get("image")
            services.update_playlist(self.request.user, title, image, playlist_id, is_public=is_public)
            messages.success(request, "Плейлист обновлен")
            return redirect("music:playlist_detail", playlist_id=playlist_id)

        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect("music:playlist_detail", playlist_id=playlist_id)


def review_requests(request: HttpRequest) -> HttpResponse:
    check_staff_permissions(request.user)
    artists_requests = services.fetch_music_objects_and_artist_by_status(Music.Status.PENDING)
    return render(request, "music/review_requests.html", context={"artists_requests": artists_requests})


def approve_review_request(request: HttpRequest, obj_id: int) -> None:
    obj_type = request.POST.get("obj_type")
    obj = services.fetch_music_objects_by_id_and_type(obj_type, obj_id)
    approve_music_object(request.user, obj)
    return redirect("music:review_requests")


def reject_review_request(request: HttpRequest, obj_id: int) -> None:
    obj_type = request.POST.get("obj_type")
    obj = services.fetch_music_objects_by_id_and_type(obj_type, obj_id)
    reject_music_object(request.user, obj)
    return redirect("music:review_requests")
