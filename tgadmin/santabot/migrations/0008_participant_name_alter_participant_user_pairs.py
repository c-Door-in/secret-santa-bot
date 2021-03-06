# Generated by Django 4.0 on 2021-12-27 14:46

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('santabot', '0007_alter_interests_interest'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='name',
            field=models.CharField(default=django.utils.timezone.now, max_length=60, verbose_name='Имя участника'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='participant',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='santabot.user', verbose_name='TG Nickname'),
        ),
        migrations.CreateModel(
            name='Pairs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('donor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Даритель', to='santabot.participant', verbose_name='Ник дарящего')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='santabot.event', verbose_name='Игра')),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Принимающий', to='santabot.participant', verbose_name='Ник получающего')),
            ],
            options={
                'verbose_name': 'Пара',
                'verbose_name_plural': 'Выбранные пары',
            },
        ),
    ]
