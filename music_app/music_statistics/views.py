from django.views.generic import TemplateView


class ListeningHistoryListView(TemplateView):
    """Возвращает треки прослушенные пользователем, сгрупированных по дате."""

    template_name = "music_statistics/listen_history.html"
    paginate_by = 50

    """def _get_listening_history(self, user_id: int) -> UserListeningHistory | None:
        Получает историю прослушиваний для текущего пользователя.
        return UserListeningHistory.objects(user_id=user_id).first()

    def _create_track_map(self, tracks_data: list[TrackListening]) -> dict[int, Track]:
        Создает словарь для достура к треку по ID.
        track_ids = [track.track_id for track in tracks_data]
        track_objs = Track.objects.filter(id__in=track_ids)
        return {track.id: track for track in track_objs}

    def _group_tracks_by_date(self, tracks_data: list[TrackListening], track_dict: dict[int, Track]) -> defaultdict:
        Группирует треки по дате прослушивания.
        grouped_tracks = defaultdict(list)
        for track_data in tracks_data:
            track = track_dict.get(track_data.track_id)
            if not track:
                continue
            listen_date = track_data.listened_at.strftime("%Y-%m-%d")
            grouped_tracks[listen_date].append(
                {
                    "track": track,
                    "listened_at": track_data.listened_at,
                }
            )
        return grouped_tracks

    def get_context_data(self, **kwargs: dict) -> dict[str, typing.Any]:
        context = super().get_context_data(**kwargs)
        listening_history = self._get_listening_history(self.request.user.id)
        if listening_history:
            tracks_data = listening_history.tracks
            tracks_dict = self._create_track_map(tracks_data)
            grouped_tracks = self._group_tracks_by_date(tracks_data, tracks_dict)
            context["grouped_tracks"] = sorted(grouped_tracks.items(), reverse=True)
        return context"""
