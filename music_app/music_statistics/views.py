import typing
from collections import defaultdict

from django.views.generic import TemplateView
from music.models import Track

from music_statistics.models import UserListeningHistory


class ListeningHistoryListView(TemplateView):
    """Возвращает треки, прослушенные пользователем, сгрупированных по дате."""

    template_name = "music_statistics/listen_history.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: dict) -> dict[str, typing.Any]:
        context = super().get_context_data(**kwargs)

        history = UserListeningHistory.objects(user_id=self.request.user.id).first()
        tracks_data = history.tracks if history else []

        tracks_ids = [track.track_id for track in tracks_data]
        tracks_objs = Track.objects.filter(id__in=tracks_ids)
        track_map = {track.id: track for track in tracks_objs}

        grouped_tracks = defaultdict(list)

        for t in tracks_data:
            track = track_map.get(t.track_id)
            if not track:
                continue

            date_str = t.listened_at.strftime("%Y-%m-%d")
            grouped_tracks[date_str].append(
                {
                    "track": track,
                    "listened_at": t.listened_at,
                },
            )
        context["grouped_tracks"] = sorted(grouped_tracks.items(), reverse=True)
        return context
