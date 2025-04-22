from django.db import models
from users.models import User

# Create your models here.


class Artist(models.Model):
    name = models.CharField(max_length=128, null=False, blank=False)
    image = models.ImageField(upload_to="artists_cards/")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    bio = models.TextField(null=True, blank=True)
    month_listeners = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class Album(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    image = models.FileField(upload_to="albums_images/")
    release_date = models.DateTimeField(auto_now_add=True)
    is_explicit = models.BooleanField(default=False, null=False)
    # не опубликованный


class Genre(models.Model):
    title = models.CharField(max_length=64, null=False, blank=False)


class Track(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False)
    album = models.ForeignKey(Album, null=True, blank=True, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="tracks_images/")
    duration = models.PositiveIntegerField(default=0)
    audio_file = models.FileField(upload_to="tracks/")
    release_date = models.DateTimeField(auto_now_add=True)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True)
    is_explicit = models.BooleanField(default=False, null=False)

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
