import datetime
from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import QuerySet
from music.models import Artist, Track

from music_app.mongo import MongoClientManager


def fetch_music_chart() -> dict:
    """Возвращает топ 100 треков в чарте."""
    with MongoClientManager() as client:
        db = client[settings.MONGO_DB]
        collection = db["track_stream"]
        chart_tracks_ids = [int(track["track_id"]) for track in collection.find().sort("-listen_count")[:100]]
        print(chart_tracks_ids)
        return Track.objects.filter(id__in=list(chart_tracks_ids))


def fetch_user_listening_history(user_id: int) -> dict | None:
    """Возвращает историю прослушиваний по id пользователя."""
    with MongoClientManager() as client:
        db = client[settings.MONGO_DB]
        collection = db["user_listening_history"]
        return collection.find_one({"user_id": user_id})


def add_track_to_listening_history(user_id: int, track_id: int) -> None:
    """Добавляет трек в историю прослушивания пользователя."""
    user_history = fetch_user_listening_history(user_id)
    if not _is_track_listened_today(user_history, track_id):
        new_entry = {"track_id": track_id, "listened_at": datetime.now()}

        with MongoClientManager() as client:
            db = client[settings.MONGO_DB]
            collection = db["user_listening_history"]

            collection.update_one(
                {"user_id": user_id},
                {"$push": {"listened_tracks": {"$each": [new_entry], "$position": 0}}},
                upsert=True,
            )


def _is_track_listened_today(user_history: dict | None, track_id: int) -> bool:
    """Проверяет, был ли трек прослушан сегодня."""
    if not user_history or "listened_tracks" not in user_history:
        return False

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    return any(
        track["track_id"] == track_id and today_start <= track["listened_at"] < today_end
        for track in user_history["listened_tracks"]
    )


def create_track_map(listened_tracks: list[dict]) -> dict[int, dict]:
    """Создает словарь треков по их ID."""
    track_ids = [track["track_id"] for track in listened_tracks]
    track_objs = Track.objects.filter(id__in=track_ids)
    return {track.id: track for track in track_objs}


def group_tracks_by_date(listened_tracks: list[dict]) -> defaultdict[str, list[dict]]:
    """Группирует треки по дате прослушивания."""
    grouped = defaultdict(list)

    for entry in listened_tracks:
        listen_date = entry["listened_at"].strftime("%Y-%m-%d")
        grouped[listen_date].append({"track_id": entry["track_id"], "listened_at": entry["listened_at"]})

    return grouped


def fetch_users_liked_artists(user_id: int) -> QuerySet[Artist]:
    """Возращает любимых артистов пользователя."""
    with MongoClientManager() as client:
        db = client[settings.MONGO_DB]
        collection = db["user_artists_follows"]
        artists_ids = collection.find_one({"user_id": user_id})["artists"]
        return Artist.objects.filter(id__in=artists_ids)
