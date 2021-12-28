# Generated by Django 4.0 on 2021-12-28 02:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('santabot', '0009_alter_participant_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pairs',
            name='donor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='donor', to='santabot.participant', verbose_name='Ник дарящего'),
        ),
        migrations.AlterField(
            model_name='pairs',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receiver', to='santabot.participant', verbose_name='Ник получающего'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participant', to='santabot.event', verbose_name='Игра'),
        ),
    ]