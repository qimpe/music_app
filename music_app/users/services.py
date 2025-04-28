from django.db.models import QuerySet
from music.models import Artist

from .models import User


def fetch_artists_by_user(user: User) -> QuerySet[Artist]:
    """Возвращает список артистов принадлежащих пользователю."""
    return Artist.objects.select_related("user").filter(user=user)
