# Generated by Django 4.0 on 2021-12-28 11:55

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('santabot', '0010_alter_pairs_donor_alter_pairs_receiver_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='game_uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, verbose_name='Уникальный идентификатор для deeplink'),
        ),
    ]
