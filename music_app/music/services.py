import typing

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from music_statistics.models import ArtistUniqueListeners, TrackStream, UserArtistsFollows
from users.models import User

from .models import Album, Artist, Playlist, Track


def fetch_artists_album(user: User, artist: Artist) -> QuerySet[Album]:
    """Возвращает Queryset альбомов в по типу пользователя."""
    if user == artist.user:
        return Album.objects.filter(artist=artist).order_by("-release_date")
    return Album.objects.filter(artist=artist, release_date__isnull=False).order_by("-release_date")


def fetch_artists_unique_listeners(artist_id: int) -> ArtistUniqueListeners | None:
    """Возвращает объект уникальных слушателей по id артиста."""
    return ArtistUniqueListeners.objects(artist_id=artist_id).first()


def fetch_or_create_user_likes_playlist(user: User) -> Playlist:
    """Получает или создает плейлист пользователя с любимыми песнями."""
    user_likes_playlist, _ = Playlist.objects.get_or_create(owner=user, is_liked_playlist=True)
    return user_likes_playlist


def fetch_artists_popular_tracks(artist_id: int) -> QuerySet[Track]:
    """Возвращает первые 5 популярных треков по id артиста."""
    track_listenings = TrackStream.objects(artist_id=artist_id).order_by("-listen_count")[:5]
    tracks_ids = [track.track_id for track in track_listenings]
    return Track.objects.filter(artist=artist_id, id__in=tracks_ids)


def fetch_artists_detail_page(context: dict[str, typing.Any], user: User, artist: Artist) -> dict[str, typing.Any]:
    """Вовращает основную информацию для карточки артиста."""
    user_likes_playlist = fetch_or_create_user_likes_playlist(user=user)
    unique_listeners = fetch_artists_unique_listeners(artist_id=artist.id)
    listeners_count = len(unique_listeners.listeners) if unique_listeners else 0
    context["albums"] = fetch_artists_album(user=user, artist=artist)
    context["month_listeners_count"] = listeners_count
    context["popular_tracks"] = fetch_artists_popular_tracks(artist_id=artist.id)
    context["liked_tracks"] = user_likes_playlist.tracks.filter(artist=artist) if user_likes_playlist else []
    return context


def follow_for_artist(user_id: int, artist_id: int) -> None:
    """Получает список отслеживаемых пользователем артистов, если нет списка то создает его."""
    is_already_liked = UserArtistsFollows.objects(user_id=user_id).first()
    if not is_already_liked:
        is_already_liked = UserArtistsFollows(user_id=user_id)
    is_already_liked.artists.append(artist_id)
    is_already_liked.save()


def fetch_top_5_artists_per_month() -> QuerySet[Artist]:
    """Возвращает топ 5 артистов по прослушиваниям за прошлый месяц."""
    top_artists = ArtistUniqueListeners.objects.aggregate([{"$group": {"_id": "$artist_id", "listeners": {"$sum": 1}}}])
    artists_ids = [artist.get("_id") for artist in top_artists]
    return Artist.objects.filter(id__in=artists_ids)


def fetch_tracks_without_album(artist: Artist) -> QuerySet[Track]:
    """возвращает треки которые еще не принадлежат ни одному треку."""
    return Track.objects.filter(artist=artist, album__isnull=True)


def fetch_tracks_in_album(album: Album) -> QuerySet[Album]:
    """Возвращает треки которые находятся в альбоме."""
    return Track.objects.filter(album=album)


def fetch_artist_by_user_id(user_id: int) -> Artist:
    """Возвращает артиста по id пользователя кому он принадлежит."""
    return Artist.objects.filter(user=user_id).get()


def add_track_in_likes_playlist(track_id: int, user: User) -> str:
    """Добавляет трек артиста и избранное."""
    track: Track = get_object_or_404(Track, pk=track_id)
    if track:
        liked_playlist, _ = Playlist.objects.get_or_create(
            owner=user, is_liked_playlist=True, title="favorite", image="/playlists_images/favorite.jpg"
        )
        liked_playlist.tracks.add(track)
        return f"Трек {track.title} был добавлен"
    return None


def delete_track_from_likes_playlist(track_id: int, user: User) -> None:
    """Удаляет трек артиста из избранного."""
    track: Track = get_object_or_404(Track, pk=track_id)
    if track:
        liked_playlist, _ = Playlist.objects.get_or_create(
            owner=user, is_liked_playlist=True, title="favorite", image="/playlists_images/favorite.jpg"
        )
        liked_playlist.tracks.delete(track)
        return f"Трек {track.title} был удален"
    return None


def fetch_my_playlists(user: User) -> QuerySet[Playlist]:
    return Playlist.objects.filter(owner=user)
