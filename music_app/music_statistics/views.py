import typing

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.views.generic import ListView, TemplateView
from music.models import Artist, Track

from . import services


class ListeningHistoryListView(LoginRequiredMixin, TemplateView):
    """Отображает историю прослушиваний, сгруппированную по датам."""

    template_name = "music_statistics/listen_history.html"

    def get_context_data(self, **kwargs: dict) -> dict[str, typing.Any]:
        context = super().get_context_data(**kwargs)
        user_id = self.request.user.id

        raw_history = services.fetch_user_listening_history(user_id)

        if raw_history and "listened_tracks" in raw_history:
            listened_tracks = raw_history["listened_tracks"]

            track_map = services.create_track_map(listened_tracks)
            print(track_map)
            grouped_tracks = services.group_tracks_by_date(listened_tracks)
            processed_data = []
            for date_str, entries in sorted(grouped_tracks.items(), reverse=True):
                date_entries = []
                for entry in entries:
                    track_data = track_map.get(entry["track_id"], {})
                    date_entries.append({"track": track_data, "listened_at": entry["listened_at"]})
                processed_data.append((date_str, date_entries))

            context["grouped_tracks"] = processed_data

        return context


class TopChartDetailView(ListView):
    """Показывает топ 100 треков в чарте."""

    model = Track
    template_name = "music_statistics/music_chart.html"
    context_object_name = "tracks"
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Track]:
        return services.fetch_music_chart()


class UserLikedArtistView(ListView):
    """Показывает любимых артистов пользователя."""

    model = Artist
    template_name = "music_statistics/liked_artists.html"
    context_object_name = "artists"
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Artist]:
        return services.fetch_users_liked_artists(self.request.user.id)
