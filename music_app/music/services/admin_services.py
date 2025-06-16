from django.core.exceptions import PermissionDenied
from users.models import User

from music import models
from . import services


def check_staff_permissions(user: User) -> None:
    """Проверяет является ли пользователь администратором."""
    if not user.is_staff:
        msg = "Ты не администратор"
        raise PermissionDenied(msg)


def approve_music_object(user: User, obj: models.Music) -> None:
    """Изменяет статус музыкального объекта на 'Approve'."""
    check_staff_permissions(user)
    services.update_music_object_status(obj, models.Music.Status.ACTIVE)


def reject_music_object(user: User, obj: models.Music) -> None:
    """Изменяет статус музыкального объекта на 'Rejected'."""
    check_staff_permissions(user)
    services.update_music_object_status(obj, models.Music.Status.REJECTED)
