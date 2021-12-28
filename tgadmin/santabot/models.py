import uuid

from django.db import models


class User(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name='ID',
    )
    name = models.TextField(
        verbose_name='TG Nickname',
    )

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователя'


class Event(models.Model):
    name = models.CharField(
        max_length=39,
        verbose_name='Название игры',
    )
    creator = models.ForeignKey(
        to='santabot.User',
        verbose_name='Создатель',
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(
        verbose_name='Время создания',
        auto_now_add=True,
    )
    cost_range = models.CharField(
        max_length=30,
        verbose_name='Ценовой диапозон',
        blank=True,
    )
    last_register_date = models.DateTimeField(
        verbose_name='Последний день регистрации',
    )
    sending_date = models.DateTimeField(
        verbose_name='Дата отправки подарка',
    )
    game_uuid = models.UUIDField(
        verbose_name='Уникальный идентификатор для deeplink',
        primary_key=False,
        default=uuid.uuid4,
        editable=False
    )
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'


class Interests(models.Model):
    interest = models.CharField(
        max_length=30,
        verbose_name='Интерес',
        unique=True,
    )

    def __str__(self):
        return f'{self.interest}'

    class Meta:
        verbose_name = 'Интерес'
        verbose_name_plural = 'Интересы'


class Participant(models.Model):
    event = models.ForeignKey(
        to='santabot.Event',
        verbose_name='Игра',
        related_name='participant',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        to='santabot.User',
        verbose_name='TG Nickname',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Имя участника',
    )
    phone_number = models.CharField(
        max_length=30,
        verbose_name='Номер телефона'
    )
    letter_for_santa = models.TextField(
        verbose_name='Письмо Санте',
        blank=True,
    )
    interests = models.ManyToManyField(
        Interests,
        verbose_name='Интересы',
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'


class Pairs(models.Model):
    event = models.ForeignKey(
        to='santabot.Event',
        verbose_name='Игра',
        on_delete=models.CASCADE,
    )
    donor = models.ForeignKey(
        to='santabot.Participant',
        related_name='donor',
        verbose_name='Ник дарящего',
        on_delete=models.CASCADE,
    )
    receiver = models.ForeignKey(
        to='santabot.Participant',
        related_name='receiver',
        verbose_name='Ник получающего',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'Пара {self.donor} - {self.receiver} в игре {self.event}'

    class Meta:
        verbose_name = 'Пара'
        verbose_name_plural = 'Выбранные пары'
