from typing import Optional

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.forms import ModelForm

from .models import Album, Artist, Playlist, Track


class CreateArtistForm(ModelForm):
    class Meta:
        model = Artist
        fields = ("name", "bio", "image")


class CreatePlaylistForm(ModelForm):
    class Meta:
        model = Playlist
        fields = ("title", "image", "is_public")


class CreateAlbumForm(ModelForm):
    tracks = forms.ModelMultipleChoiceField(
        queryset=Track.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="Выбранные треки",
    )

    def __init__(self, *args, **kwargs):
        self.artist = kwargs.pop("artist", None)
        super().__init__(*args, **kwargs)

        if self.artist:
            self.fields["tracks"].queryset = Track.objects.filter(
                artist=self.artist, album__isnull=True
            )

    class Meta:
        model = Album
        fields = ("title", "image", "is_explicit")


class CreateTrackForm(ModelForm):
    class Meta:
        model = Track
        fields = ("title", "image", "is_explicit", "audio_file", "genre")

    def clean_audio_file(
        self,
    ) -> Optional[InMemoryUploadedFile | TemporaryUploadedFile]:
        audio: Optional[InMemoryUploadedFile | TemporaryUploadedFile] = (
            self.cleaned_data.get("audio_file")
        )
        if audio:
            allowed_types: list[str] = ["audio/mpeg", "audio/wav", "audio/ogg"]
            if audio.content_type not in allowed_types:
                raise ValidationError("Файл должен быть в формате MP3, WAV или OGG!")

        return audio
