import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import BaseModelForm
from django.http import FileResponse, HttpResponse
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
from mutagen import File

from .forms import (
    CreateAlbumForm,
    CreateArtistForm,
    CreatePlaylistForm,
    CreateTrackForm,
)
from .mixins import ArtistAccessMixin
from .models import Album, Artist, Playlist, Track


# Create your views here.
def index(request) -> HttpResponse:
    """Главная страница с топом артистов, последними релизами артистов за которыми следит пользователь"""
    top_month_artists = Artist.objects.order_by("-month_listeners")[:5]
    context: dict = {"top_month_artists": top_month_artists}
    return render(request, "index.html", context=context)


class CreateArtist(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = CreateArtistForm
    template_name = "music/create_artist.html"
    permission_denied_message = "The number of artists you can create has been exceeded"

    def test_func(self) -> bool:
        user = self.request.user
        return user.is_label or Artist.objects.filter(user=user).count() < 1

    def form_valid(self, form: CreateArtistForm) -> HttpResponse:
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("music:artist_detail", kwargs={"pk": self.object.pk})


class ArtistDetailView(DetailView):
    """Подробная страница артиста"""

    model = Artist
    pk_url_kwarg = "pk"
    template_name = "music/artist_detail.html"
    context_object_name = "artist"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        artist = self.object
        user = self.request.user
        context.update(
            {
                "tracks": Track.objects.filter(artist=artist),
                "albums": Album.objects.filter(artist=artist),
            }
        )

        user_likes_playlist, _ = Playlist.objects.get_or_create(
            owner=user, is_liked_playlist=True
        )
        context["liked_tracks"] = (
            user_likes_playlist.tracks.filter(artist=artist)
            if user_likes_playlist
            else []
        )

        return context


class CreateAlbum(ArtistAccessMixin, LoginRequiredMixin, CreateView):
    """Представление создания альбома"""

    form_class = CreateAlbumForm
    template_name = "music/create_album.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["artist"] = self.artist
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["artist_id"] = self.kwargs["artist_id"]
        context["tracks"] = Track.objects.filter(artist=self.artist, album__isnull=True)
        return context

    def form_valid(self, form):
        form.instance.artist = self.artist
        response = super().form_valid(form)
        tracks = form.cleaned_data.get("tracks")
        if tracks:
            tracks.update(album=form.instance)
        return response

    def get_success_url(self):
        return reverse_lazy("music:artist_detail", kwargs={"pk": self.artist.pk})


class CreateTrack(LoginRequiredMixin, CreateView):
    form_class = CreateTrackForm
    template_name = "music/create_track.html"

    def get_success_url(self):
        return reverse_lazy(
            "music:artist_detail", kwargs={"pk": self.kwargs["artist_id"]}
        )

    def form_valid(self, form: BaseModelForm):
        self.object = form.save(commit=False)
        audio_file = self.object.audio_file
        audio = File(audio_file)
        self.object.artist = Artist.objects.filter(user=self.request.user.id).first()
        self.object.duration = int(audio.info.length)
        self.object.save()
        self.kwargs["artist_id"] = self.object.artist.pk
        return super().form_valid(form)


class AlbumDetailView(DetailView):
    model = Album
    pk_url_kwarg = "album_id"
    template_name = "music/album_detail.html"
    context_object_name = "album"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        album = self.get_object()
        context.update({"tracks": Track.objects.filter(album=album)})
        return context


class AudioStreamView(View):
    CHUNK_SIZE = 8192
    MIME_TYPE = "audio/mpeg"

    def get(self, request, track_id):
        try:
            track = get_object_or_404(Track, pk=track_id)
            file_path = track.audio_file.path

            if not os.path.exists(file_path):
                raise FileNotFoundError("Audio file not found")

            file_size: int = os.path.getsize(file_path)
            range_header: str = request.headers.get("Range", "").strip()
            print(range_header)
            if not range_header:
                response = FileResponse(
                    open(file_path, "rb"),
                    content_type=self.MIME_TYPE,
                    as_attachment=False,
                )
                response["Accept-Ranges"] = "bytes"
                return response

            byte_range = self.parse_range_header(range_header, file_size)

            if not byte_range:
                return HttpResponse(status=416)
            start, end = byte_range
            content_length = end - start + 1
            response = FileResponse(
                self.file_iterator(file_path, start, end),
                status=206,
                content_type=self.MIME_TYPE,
            )
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Accept-Ranges"] = "bytes"
            response["Content-Length"] = content_length
            return response
        except Track.DoesNotExist:
            return HttpResponse("Track not found", status=404)
        except FileNotFoundError:
            return HttpResponse("Audio file not found", status=404)
        except Exception as e:
            # В продакшене следует добавить логирование ошибки
            return HttpResponse(str(e), status=500)

    def parse_range_header(self, range_header: str, file_size: int) -> tuple:
        try:
            # Разделяем "bytes=0-100" на "bytes" и "0-100"
            unit, ranges = range_header.split("=")
            if unit.strip().lower() != "bytes":
                return None

            # Разделяем "0-100" на start_str и end_str
            start_str, end_str = ranges.split("-", 1)

            # Парсим start
            start = int(start_str) if start_str else 0

            # Парсим end
            if end_str:
                end = int(end_str)
            else:
                # Если end не указан (например, "bytes=0-"), берем конец файла
                end = file_size - 1

            # Корректируем end, если он больше размера файла
            end = min(end, file_size - 1)

            # Проверяем валидность диапазона
            if start < 0 or start > end:
                return None

            return (start, end)
        except (ValueError, AttributeError, TypeError):
            return None

    def file_iterator(self, file_path: str, start: int, end: int):
        with open(file_path, "rb") as file:
            file.seek(start)
            remaining = end - start + 1

            while remaining > 0:
                chunk_size = min(self.CHUNK_SIZE, remaining)
                data = file.read(chunk_size)
                if not data:
                    break
                remaining -= len(data)
                yield (data)


class ManageFavoriteTrack(LoginRequiredMixin, View):
    def post(self, request, track_id: int):
        track: Track = get_object_or_404(Track, pk=track_id)
        liked_playlist, created = Playlist.objects.get_or_create(
            owner=request.user,
            is_liked_playlist=True,
            title="favorite",
            image="/playlists_images/favorite.jpg",
        )
        print(liked_playlist.tracks)
        action = request.POST.get("action")
        if action == "like":
            print("До:", liked_playlist.tracks.all())
            liked_playlist.tracks.add(track)

            print("После:", liked_playlist.tracks.all())
            messages.success(request, f"Трек {track.title} был добавлен в мне нравится")
        elif action == "unlike":
            print("До:", liked_playlist.tracks.all())
            liked_playlist.tracks.remove(track)
            print(liked_playlist.tracks.all())
            print("После:", liked_playlist.tracks.all())
            messages.info(request, f"Трек {track.title} был удален")
        else:
            messages.error(request, "Неизвестное действие")
        return redirect("music:artist_detail", pk=track.artist.id)


class UnlikeTrack(LoginRequiredMixin, View):
    def post(self, request, track_id: int):
        track: Track = get_object_or_404(Track, pk=track_id)
        liked_playlist = Playlist.objects.get(
            owner=request.user, is_liked_playlist=True
        )
        if liked_playlist:
            liked_playlist.tracks.delete(track)
        return redirect("music:artist_detail", pk=track.artist.id)


class AddTrackInPlaylist(LoginRequiredMixin, View):
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


class CreatePlaylist(LoginRequiredMixin, CreateView):
    form_class = CreatePlaylistForm
    template_name = "music/create_playlist.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class PlaylistDetail(LoginRequiredMixin, DetailView):
    model = Playlist
    template_name = "music/playlist_detail.html"
    context_object_name = "playlist"

    """def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tracks_in_playlist"]=self.get_object()
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

    def get_queryset(self):
        user = self.request.user
        return Playlist.objects.filter(owner=user)
