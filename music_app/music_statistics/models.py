from datetime import datetime

from mongoengine import DateTimeField, Document, EmbeddedDocument, EmbeddedDocumentField, IntField, ListField


class UserArtistsFollow(Document):
    user_id = IntField(required=True)
    artists = ListField(IntField(required=True))

    def save(self, *args: tuple, **kwargs: dict) -> None:
        self.artists = list(set(self.artists))
        super().save(*args, **kwargs)


class TrackListening(EmbeddedDocument):
    track_id = IntField(required=True)
    listened_at = DateTimeField()

    def save(self, *args: tuple, **kwargs: dict) -> None:
        listened_day = self.listened_at.date()

        existing_record = TrackListening.objects(
            track_id=self.track_id,
            listened_at__gte=datetime.combine(listened_day, datetime.min.time()),
            listened_at__lt=datetime.combine(listened_day, datetime.max.time()),
        ).first()
        if existing_record:
            return
        super().save(*args, **kwargs)


class UserListeningHistory(Document):
    user_id = IntField(required=True, unique=True)
    tracks = ListField(EmbeddedDocumentField(TrackListening))


class ArtistUniqueListeners(Document):
    artist_id = IntField(required=True)
    listeners = ListField(IntField())

    def save(self, *args: tuple, **kwargs: dict) -> None:
        self.listeners = list(set(self.listeners))
        super().save(*args, **kwargs)
