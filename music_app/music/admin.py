from django.contrib import admin

from .models import Album, Artist, Genre, Playlist, Track

# Register your models here.
admin.site.register(Artist)
admin.site.register(Track)
admin.site.register(Playlist)
admin.site.register(Album)
admin.site.register(Genre)
