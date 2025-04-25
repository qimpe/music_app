from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from .models import Artist


class ArtistAccessMixin:
    artist_pk_url_kwarg = "artist_id"

    def get_artist(self) -> Artist:
        artist = get_object_or_404(Artist, pk=self.kwargs[self.artist_pk_url_kwarg])
        if artist.user != self.request.user:
            msg = "You dont have a permission to the artist"
            raise PermissionDenied(msg)
        return artist

    def dispatch(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> None:
        self.artist = self.get_artist()
        return super().dispatch(request, *args, **kwargs)
