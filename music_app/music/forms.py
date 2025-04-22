from typing import Optional

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.forms import ModelForm
from PIL import Image

from .models import Album, Artist, Playlist, Track


class CreateArtistForm(ModelForm):
    class Meta:
        model = Artist
        fields = ("name", "bio", "image")

    def clean_image(self):
        MAX_SIZE = 2000
        image = self.cleaned_data.get("image")
        if image:
            img = Image.open(image)
            width, height = img.size
            if width > MAX_SIZE or height > MAX_SIZE:
                raise forms.ValidationError("Максимальный размер фото 2000 на 2000")
        return image


class CreateAlbumForm(ModelForm):
    tracks = forms.ModelMultipleChoiceField(
        queryset=Track.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label="Какие треки будут в альбоме",
        required=False,
    )

    class Meta:
        model = Album
        fields = ("title", "image", "is_explicit")
        labels = {"title": "Название", "image": "Обложка", "is_explicit": "Explicit"}

    def __init__(self, *args, **kwargs):
        artist = kwargs.pop("artist", None)
        super().__init__(*args, **kwargs)
        if artist:
            self.fields["tracks"].queryset = Track.objects.filter(
                artist=artist, album__isnull=True
            )


class CreateTrackForm(ModelForm):
    class Meta:
        model = Track
        fields = ("title", "image", "is_explicit", "audio_file", "genre")
        labels = {
            "title": "Название",
            "image": "Обложка",
            "is_explicit": "Explicit",
            "audio_file": "Файл",
            "genre": "Жанр",
        }

    def clean_audio_file(
        self,
    ) -> Optional[InMemoryUploadedFile | TemporaryUploadedFile]:
        audio: Optional[InMemoryUploadedFile | TemporaryUploadedFile] = (
            self.cleaned_data.get("audio_file")
        )
        if audio:
            allowed_types: list[str] = ["audio/mpeg", "audio/wav", "audio/ogg"]
            fs = FileSystemStorage()
            filename = f"tracks/{audio.name}"
            saved_name = fs.save(filename, audio)
            fs.path(saved_name)

            if audio.content_type not in allowed_types:
                raise ValidationError("Файл должен быть в формате MP3, WAV или OGG!")

        return audio


class CreatePlaylistForm(ModelForm):
    class Meta:
        model = Playlist
        fields = ("title", "image", "is_public")
