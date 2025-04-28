from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    country = models.CharField(max_length=70, default="Russian Federation")
    is_label = models.BooleanField(default=False)

    """def add_track_in_listening_history(self, track_id: int) -> None:
        Добавляет трек в историю прослушивания пользователя.
        listening_history: UserListeningHistory | None = UserListeningHistory.objects(user_id=self.id).first()
        if not listening_history:
            listening_history = UserListeningHistory(user_id=self.id)

        track_stream = TrackListening(track_id=track_id, listened_at=timezone.now())
        listening_history.tracks.append(track_stream)
        listening_history.save()"""

    def __str__(self) -> str:
        return self.username
