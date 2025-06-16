from datetime import timezone

import pymongo
from django.conf import settings
from django.core.exceptions import PermissionDenied, RequestAborted
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from users.models import User

from music import forms, models
from music_app.mongo import MongoClientManager


def fetch_or_create_artist_unique_listeners(artist_id: int) -> dict:
    """Возвращает документ уникальных слушателей артиста, создает его при отсутствии."""
    with MongoClientManager() as client:
        db = client[settings.MONGO_DB]
        collection = db["artist_unique_listeners"]

        return collection.find_one_and_update(
            {"artist_id": artist_id},
            {"$setOnInsert": {"listeners": []}},
            upsert=True,
            return_document=pymongo.ReturnDocument.AFTER,
        )


def add_unique_listener_to_artist(artist_id: int, listener_id: int) -> None:
    """Добавляет уникального слушателя в список артиста."""
    with MongoClientManager() as client:
        db = client[settings.MONGO_DB]
        collection = db["artist_unique_listeners"]
        collection.update_one({"artist_id": artist_id}, {"$addToSet": {"listeners": listener_id}})


def fetch_music_objects_and_artist_by_status(status: str) -> None:
    """Возвращает музыкальное объект и артистов по их статусу."""
    albums = models.Album.objects.filter(status=status, is_published=False)
    tracks = models.Track.objects.filter(status=status, is_published=False)
    artists = models.Artist.objects.filter(status=status)
    return {"artists": artists, "tracks": tracks, "albums": albums}


def fetch_music_objects_by_id_and_type(obj_type: str, obj_id: int) -> None | models.Music:
    """Возвращает музыкальный объект по его id и типу."""
    TYPE_MODEL_MAP = {"artist": models.Artist, "album": models.Album, "track": models.Track}
    try:
        obj_type = obj_type.lower()
        if obj_type not in TYPE_MODEL_MAP:
            raise RequestAborted
        model_class = TYPE_MODEL_MAP[obj_type]
        return model_class.objects.get(id=obj_id)
    except (model_class.DoesNotExist, RequestAborted):
        return None


def release_music_object(obj: models.Music) -> None:
    """Релизит объект, становится доступный для пользователей."""
    if not obj.release_date:
        obj.release_date = timezone.now()
    obj.status = obj.Status.PUBLISHED
    obj.save()


def update_music_object_status(obj: models.Music, status: str) -> None:
    """Изменяет статут музыкального объекта."""
    obj.status = status
    obj.save()


def create_artist(user: User, form: forms.CreateArtistForm) -> models.Artist:
    """Создает артиста и возвращает его."""
    artist: models.Artist = form.save(commit=False)
    artist.user = user
    artist.save()
    return artist


def create_album(form: forms.CreateAlbumForm, artist_id: int) -> models.Album:
    """Создает альбом и возвращает его."""
    album: models.Album = form.save(commit=False)
    artist = models.Artist.objects.get(id=artist_id)
    with transaction.atomic():
        album.artist = artist
        album.save()
        if tracks := form.cleaned_data["tracks"]:
            tracks.update(album=album)
            tracks.save()
    return album


#! need test
def fetch_or_create_users_favorite_artists(user_id: int) -> dict:
    """Создает или возращает готовый объект."""
    with MongoClientManager() as client:
        db = client[settings.MONGO_DB]
        collection = db["user_artists_follow"]
        return collection.find_one_and_update({"user_id": user_id})


#! need test
def follow_for_artist(user_id: int, artist_id: int) -> None:
    """Добавляет артиста в список любимых артистов пользователя."""
    with MongoClientManager() as client:
        db = client[settings.MONGO_DB]
        collection = db["user_artists_follows"]
        return collection.update_one({"user_id": user_id}, {"$addToSet": {"artists": artist_id}}, upsert=True)


def fetch_track_by_id(track_id: int) -> models.Track:
    """Возвращает трек по id."""
    return models.Track.objects.get(id=track_id)


def manage_track(
    user: User, action: str, track_id: int, *, is_liked: bool, playlist_id: int | None = None
) -> int | None:
    with transaction.atomic():
        track: models.Track = get_object_or_404(models.Track, pk=track_id)
        if not track:
            return None
        playlist = (
            fetch_or_create_user_likes_playlist(user) if is_liked else models.Playlist.objects.get(id=playlist_id)
        )
        if action == "like":
            playlist.tracks.add(track)
        elif action == "unlike":
            playlist.tracks.remove(track)
    return track.artist.id


def add_track_in_favorite() -> None:
    pass


def delete_track_from_favorite() -> None:
    pass


def create_playlist() -> None:
    """Создает плейлист."""


def delete_playlist(user: User, playlist_id: int) -> None:
    """Удаляет плейлиста с проверкой что он принадледжит этого пользователю."""
    playlist = get_object_or_404(models.Playlist, id=playlist_id)
    if user != playlist.owner or playlist.is_liked_playlist:
        msg = "Нет прав на удаление этого плейлиста"
        raise PermissionDenied(msg)
    playlist.delete()


def update_playlist(user: User, title: str, image: UploadedFile | None, playlist_id: int, *, is_public: bool) -> None:
    """Обновляет данные плейлиста."""
    playlist = fetch_playlist(playlist_id)
    if playlist.owner != user:
        msg = "Нет прав на удаление этого плейлиста"
        raise PermissionDenied(msg)
    playlist.title = title
    playlist.image = image
    playlist.is_public = is_public
    playlist.save()


#! refactor
def check_is_user_artist_owner(user_id: int, artist_id: int) -> models.Artist:
    """Проверяет является ли пользователь."""
    artist = fetch_artist_by_user_id(user_id)
    if artist.id != artist_id:
        msg = "You dont have a permission to the artist"
        raise PermissionDenied(msg)
    return artist


def fetch_album_by_id(album_id: int) -> models.Album:
    """Возвращает альбом по его id."""
    return models.Album.objects.get(id=album_id)


def fetch_artists_album(user: User, artist: models.Artist) -> QuerySet[models.Album]:
    """Возвращает Queryset альбомов в по типу пользователя."""
    if user == artist.user:
        return models.Album.objects.filter(artist=artist).order_by("-release_date")
    return models.Album.objects.filter(
        artist=artist, status=models.Music.Status.ACTIVE, release_date__isnull=False
    ).order_by("-release_date")


#! need to test
def fetch_artists_unique_listeners(artist_id: int) -> dict[str, int] | None:
    """Возвращает объект уникальных слушателей по id артиста."""
    with MongoClientManager() as client:
        db = client[settings.MONGO_DB]
        collection = db["artist_unique_listeners"]
        return collection.find_one({"artist_id": artist_id})


#! some error
def fetch_or_create_user_likes_playlist(user: User) -> models.Playlist:
    """Получает или создает плейлист пользователя с любимыми песнями."""
    user_likes_playlist, _ = models.Playlist.objects.get_or_create(owner=user, is_liked_playlist=True)
    return user_likes_playlist


def fetch_artists_popular_tracks(artist_id: int) -> QuerySet[models.Track]:
    """Возвращает первые 5 популярных треков по id артиста."""
    with MongoClientManager():
        """db = client[settings.MONGO_DB]
        collection = db["track_stream"]
        track_listenings = collection.find({"artist_id": artist_id}).sort("-listen_count")[:5]
        tracks_ids = [track["track_id"] for track in track_listenings]"""
        return models.Track.objects.filter(artist=artist_id)  # id__in=tracks_ids


def fetch_top_5_artists_per_month() -> QuerySet[models.Artist]:
    """Возвращает топ 5 артистов по прослушиваниям за прошлый месяц."""
    with MongoClientManager() as client:
        db = client[settings.MONGO_DB]
        collection = db["track_stream"]
        top_artists = collection.aggregate([{"$group": {"_id": "$artist_id", "listeners": {"$sum": 1}}}])
        artists_ids = [artist["_id"] for artist in top_artists]
        return models.Artist.objects.filter(id__in=artists_ids)


def fetch_tracks_without_album(artist: models.Artist) -> QuerySet[models.Track]:
    """Возвращает треки которые еще не принадлежат ни одному альбому."""
    return models.Track.objects.filter(artist=artist, album__isnull=True)


def fetch_tracks_in_album(album: models.Album) -> QuerySet[models.Album]:
    """Возвращает все треки которые находятся в альбоме."""
    return models.Track.objects.filter(album=album)


def fetch_artist_by_user_id(user_id: int) -> models.Artist:
    """Возвращает артиста по id пользователя кому он принадлежит."""
    return models.Artist.objects.filter(user=user_id).get()


def fetch_my_playlists(user: User) -> QuerySet[models.Playlist]:
    """Возвращает плейлисты пользователя."""
    return models.Playlist.objects.filter(owner=user)


def fetch_playlist(playlist_id: int) -> models.Playlist:
    """Возвращает плейлист по id."""
    return get_object_or_404(models.Playlist, id=playlist_id)
