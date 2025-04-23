from django.db import models
from django.utils import timezone
from users.models import User

# Create your models here.


class Music(models.Model):
    """Абстрактный класс который реализует общие методы для музыкальных объектов"""

    def release(self):
        """Релизит объект, становится доступный для пользователей"""
        if not self.release_date:
            self.release_date = timezone.now()
        self.status = self.Status.PUBLISHED
        self.save()

    class Meta:
        abstract = True


class Artist(models.Model):
    name = models.CharField(max_length=128, null=False, blank=False)
    image = models.ImageField(upload_to="artists_cards/")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    bio = models.TextField(null=True, blank=True)
    month_listeners = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class Genre(models.Model):
    title = models.CharField(max_length=64, null=False, blank=False)

    def __str__(self):
        return self.title


class Album(Music):
    class Status(models.TextChoices):
        DRAFT: str = "DR", "Черновик"
        PUBLISHED: str = "PB", "Опубликован"

    title = models.CharField(max_length=256, null=False, blank=False)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    image = models.FileField(upload_to="albums_images/")
    created_at = models.DateTimeField(auto_now_add=True)
    release_date = models.DateTimeField(null=True, blank=True)
    is_explicit = models.BooleanField(default=False, null=False)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )

    def release(self) -> None:
        return super().release()


class Track(Music):
    title = models.CharField(max_length=256, null=False, blank=False)
    album = models.ForeignKey(Album, null=True, blank=True, on_delete=models.SET_NULL)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="tracks_images/")
    duration = models.PositiveIntegerField(default=0)
    audio_file = models.FileField(upload_to="tracks/")
    create_at = models.DateTimeField(auto_now_add=True)
    release_date = models.DateTimeField(blank=True, null=True)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True)
    is_explicit = models.BooleanField(default=False, null=False)

    def release(self) -> None:
        return super().release()

    def __str__(self):
        return f"{self.artist} - {self.title}"


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

    def __str__(self):
        return self.title

    class Meta:
        unique_together = ("owner", "is_liked_playlist", "title")
