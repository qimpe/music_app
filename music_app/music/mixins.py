from typing import Optional

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Artist


class ArtistAccessMixin:
    artist_pk_url_kwarg = "artist_id"

    def get_artist(self):
        artist = get_object_or_404(Artist, pk=self.kwargs[self.artist_pk_url_kwarg])
        if artist.user != self.request.user:
            raise PermissionDenied("You dont have a permission to the artist")
        return artist

    def dispatch(self, request, *args, **kwargs):
        self.artist = self.get_artist()
        return super().dispatch(request, *args, **kwargs)
