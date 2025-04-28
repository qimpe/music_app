from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from .models import Artist


class ArtistAccessMixin(View):
    artist_pk_url_kwarg = "artist_id"

    def dispatch(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> HttpResponse:
        self.artist = self.get_artist()
        return super().dispatch(request, *args, **kwargs)

    def get_artist(self) -> Artist:
        artist = get_object_or_404(Artist, pk=self.kwargs[self.artist_pk_url_kwarg])
        if artist.user != self.request.user:
            msg = "You dont have a permission to the artist"
            raise PermissionDenied(msg)
        return artist
