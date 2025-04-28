from django.db import models
from django.utils import timezone
from django_stubs_ext.db.models import TypedModelMeta
from music_statistics.models import ArtistUniqueListeners
from users.models import User


# Create your models here.
class Artist(models.Model):
    name = models.CharField(max_length=128, null=False, blank=False)
    image = models.ImageField(upload_to="artists_cards/")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    bio = models.TextField(blank=True)
    month_listeners = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.name

    def update_unique_listeners(self, listener_id: int) -> None:
        unique_listeners = ArtistUniqueListeners.objects(artist_id=self.pk).first()
        if not unique_listeners:
            unique_listeners = ArtistUniqueListeners(artist_id=self.pk)
        unique_listeners.listeners.append(listener_id)
        unique_listeners.save()


class Genre(models.Model):
    title = models.CharField(max_length=64, null=False, blank=False)

    def __str__(self) -> str:
        return self.title


class Music(models.Model):
    """Абстрактный класс для музыкальных объектов."""

    class Status(models.TextChoices):
        DRAFT = ("DR", "Черновик")
        PUBLISHED = ("PB", "Опубликован")

    title = models.CharField(max_length=256, null=False, blank=False)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="albums_images/")
    created_at = models.DateTimeField(auto_now_add=True)
    release_date = models.DateTimeField(null=True, blank=True)
    is_explicit = models.BooleanField(default=False, null=False)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    class Meta(TypedModelMeta):
        abstract = True

    def release(self) -> None:
        """Релизит объект, становится доступный для пользователей."""
        if not self.release_date:
            self.release_date = timezone.now()
        self.status = self.Status.PUBLISHED
        self.save()


class Album(Music):
    def __str__(self) -> str:
        return self.title

    def release(self) -> None:
        return super().release()


class Track(Music):
    album = models.ForeignKey(Album, null=True, blank=True, on_delete=models.SET_NULL)
    duration = models.PositiveIntegerField(default=0)
    audio_file = models.FileField(upload_to="tracks/")

    def __str__(self) -> str:
        return f"{self.artist} - {self.title}"

    def release(self) -> None:
        return super().release()


class Playlist(models.Model):
    title = models.CharField(
        max_length=128,
        null=False,
        default="favorite",
        unique=True,
        verbose_name="Мне нравится",
    )
    image = models.ImageField(upload_to="playlists_images/")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    tracks = models.ManyToManyField(Track)
    is_liked_playlist = models.BooleanField(default=False)

    class Meta(TypedModelMeta):
        unique_together = ("owner", "is_liked_playlist", "title")

    def __str__(self) -> str:
        return self.title
