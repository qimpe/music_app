from mongoengine import DateTimeField, Document, IntField, ListField


class UserArtistsFollows(Document):
    user_id = IntField(required=True)
    artists = ListField(IntField(required=True))

    def save(self, *args: tuple, **kwargs: dict) -> None:
        self.artists = list(set(self.artists))
        super().save(*args, **kwargs)


class TrackStream(Document):
    artist_id = IntField(required=True)
    track_id = IntField(required=True)
    listen_count = IntField(required=True, default=0)
    listened_at = DateTimeField()

    """def save(self, *args: tuple, **kwargs: dict) -> None:
        listened_day = self.listened_at.date()
        existing_record = TrackStream.objects(
            track_id=self.track_id,
            listened_at__gte=datetime.combine(listened_day, datetime.min.time()),
            listened_at__lt=datetime.combine(listened_day, datetime.max.time()),
        ).first()
        if existing_record:
            return
        super().save(*args, **kwargs)"""


class UserListeningHistory(Document):
    user_id = IntField(required=True, unique=True)
    listened_tracks = ListField(IntField())


class ArtistUniqueListeners(Document):
    artist_id = IntField(required=True)
    listeners = ListField(IntField())

    def save(self, *args: tuple, **kwargs: dict) -> None:
        self.listeners = list(set(self.listeners))
        super().save(*args, **kwargs)
