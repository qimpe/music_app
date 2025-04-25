from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from music_statistics.models import TrackListening, UserListeningHistory


# Create your models here.
class User(AbstractUser):
    country = models.CharField(max_length=70, default="Russian Federation")
    is_label = models.BooleanField(default=False)

    def add_track_in_user_history(self, track_id: int) -> None:
        """Добавляет трек в историю прослушивания пользователя."""
        history = UserListeningHistory.objects(user_id=self.id).first()
        if not history:
            history = UserListeningHistory(user_id=self.id)

        stream = TrackListening(track_id=track_id, listened_at=timezone.now())
        history.tracks.append(stream)

        history.save()

    def __str__(self) -> str:
        return self.username
