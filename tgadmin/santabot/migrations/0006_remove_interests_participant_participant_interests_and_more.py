# Generated by Django 4.0 on 2021-12-25 18:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('santabot', '0005_alter_user_external_id_alter_user_name_participant_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interests',
            name='participant',
        ),
        migrations.AddField(
            model_name='participant',
            name='interests',
            field=models.ManyToManyField(to='santabot.Interests', verbose_name='Интересы'),
        ),
        migrations.AlterField(
            model_name='event',
            name='cost_range',
            field=models.CharField(blank=True, max_length=30, verbose_name='Ценовой диапозон'),
        ),
        migrations.AlterField(
            model_name='event',
            name='name',
            field=models.CharField(max_length=39, verbose_name='Название игры'),
        ),
        migrations.AlterField(
            model_name='interests',
            name='interest',
            field=models.CharField(max_length=30, verbose_name='Интерес'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='santabot.event', verbose_name='Игра'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='phone_number',
            field=models.CharField(max_length=30, verbose_name='Номер телефона'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='santabot.user', verbose_name='Имя участника'),
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.TextField(verbose_name='TG Nickname'),
        ),
    ]
