# Generated by Django 4.0 on 2021-12-23 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('santabot', '0002_alter_user_options_event'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='last_register_date',
            field=models.TextField(verbose_name='Последний день регистрации'),
        ),
        migrations.AlterField(
            model_name='event',
            name='sending_date',
            field=models.TextField(verbose_name='Дата отправки подарка'),
        ),
    ]
