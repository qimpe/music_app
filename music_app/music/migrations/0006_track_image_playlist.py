# Generated by Django 5.0.4 on 2025-03-22 20:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0005_alter_album_image_alter_artist_image'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='track',
            name='image',
            field=models.FileField(default=1, upload_to='tracks_images/'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='Playlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='Мой плейлист', max_length=128)),
                ('image', models.ImageField(upload_to='playlists_images')),
                ('is_public', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
