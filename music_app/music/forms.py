import typing

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.forms import ModelForm
from PIL import Image

from .models import Album, Artist, Playlist, Track


class CreateArtistForm(ModelForm):
    class Meta:
        model = Artist
        fields = ("name", "bio", "image")

    def clean_image(self) -> File | None:
        max_size: typing.Final = 2000
        image_path: str = self.cleaned_data.get("image")
        if image_path:
            image: Image = Image.open(image_path)
            width, height = image.size
            if width > max_size or height > max_size:
                message = "Максимальный размер фото 2000 на 2000"
                raise forms.ValidationError(message)
            return image_path
        return None


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
        labels: typing.ClassVar[dict[str, str]] = {"title": "Название", "image": "Обложка", "is_explicit": "Explicit"}

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        artist = kwargs.pop("artist", None)
        super().__init__(*args, **kwargs)
        if artist:
            self.fields["tracks"].queryset = Track.objects.filter(
                artist=artist,
                album__isnull=True,
            )


class CreateTrackForm(ModelForm):
    class Meta:
        model = Track
        fields: tuple = ("title", "image", "is_explicit", "audio_file", "genre")
        labels: typing.ClassVar[dict[str, str]] = {
            "title": "Название",
            "image": "Обложка",
            "is_explicit": "Explicit",
            "audio_file": "Файл",
            "genre": "Жанр",
        }

    def clean_audio_file(
        self,
    ) -> InMemoryUploadedFile | TemporaryUploadedFile | None:
        audio: InMemoryUploadedFile | TemporaryUploadedFile | None = self.cleaned_data.get("audio_file")
        if audio:
            allowed_types: list[str] = ["audio/mpeg", "audio/wav", "audio/ogg"]
            fs = FileSystemStorage()
            filename = f"tracks/{audio.name}"
            saved_name = fs.save(filename, audio)
            fs.path(saved_name)

            if audio.content_type not in allowed_types:
                msg = "Файл должен быть в формате MP3, WAV или OGG!"
                raise ValidationError(msg)

        return audio


class CreatePlaylistForm(ModelForm):
    class Meta:
        model = Playlist
        fields = ("title", "image", "is_public")
