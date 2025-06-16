from django.http import HttpRequest, HttpResponse
from django.views.generic import View

from .services.services import check_is_user_artist_owner


class ArtistAccessMixin(View):
    artist_pk_url_kwarg = "artist_id"

    def dispatch(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> HttpResponse:
        self.artist = check_is_user_artist_owner(request.user.id, self.kwargs[self.artist_pk_url_kwarg])
        return super().dispatch(request, *args, **kwargs)
